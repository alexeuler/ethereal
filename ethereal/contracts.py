from typing import Dict, Any, Union
import json
from datetime import datetime
from hexbytes import HexBytes
from eth_typing.encoding import HexStr
from requests.exceptions import ReadTimeout
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.contract.contract import (
    Contract,
    ContractEvent,
    ContractFunction,
)
from web3.exceptions import ContractLogicError
from web3._utils.abi import get_abi_input_types, get_abi_output_types

from eth_utils import function_abi_to_4byte_selector
from .etherscan import Etherscan
from .base import Base
from .cache import Cache


class Web3JsonEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Web3 objects.
    """

    def default(self, o: Any) -> Union[Dict[Any, Any], HexStr]:
        if isinstance(o, AttributeDict):
            return dict(o.items())
        if isinstance(o, HexBytes):
            return HexStr(o.hex())
        if isinstance(o, (bytes, bytearray)):
            return HexStr(HexBytes(o).hex())
        return json.JSONEncoder.default(self, o)


def json_response(response: AttributeDict) -> str:
    """
    Convert a Web3 response to JSON.
    """
    return json.dumps(response, cls=Web3JsonEncoder)


class Contracts(Base):
    """
    Web3 Contract related functionality.
    """

    _etherscan: Etherscan
    _web3: Web3
    _cache: Cache

    def __init__(self, etherscan: Etherscan, web3: Web3, cache: Cache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._etherscan = etherscan
        self._web3 = web3
        self._cache = cache

    def calldata(self, call: ContractFunction) -> str:
        """
        Get the calldata for a given function call.

        :param call: The contract call.
        """
        selector = HexBytes(function_abi_to_4byte_selector(call.abi)).hex()
        abi_types = get_abi_input_types(call.abi)
        bytes_calldata = self._rpc.codec.encode(abi_types, call.args)
        return selector + HexBytes(bytes_calldata).hex()[2:]

    def decode_response(self, call: ContractFunction, response: Any) -> Any:
        """
        Decode a response from a contract call.

        :param call: The contract call.
        :param response: The response to decode.
        """
        abi = get_abi_output_types(call.abi)
        return self._rpc.codec.decode(abi, response)

    def get_contract(self, address: str, resolve_proxy: bool) -> Contract:
        """
        Get a contract for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve a proxy contract abi.
        """
        abi = self.get_abi(address, resolve_proxy)
        return self._web3.eth.contract(
            address=self._web3.to_checksum_address(address), abi=abi
        )

    def get_abi(self, address: str, resolve_proxy: bool) -> list[dict[str, Any]]:
        """
        Get the ABI for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve a proxy contract abi.
        """
        abi = self._etherscan.get_abi(address)
        if not resolve_proxy:
            return abi
        for f in abi:
            if not "name" in f:
                continue
            if f["name"] == "implementation":
                try:
                    contract = self._get_contract(address)
                    implementation = contract.functions.implementation().call()
                    return self._etherscan.get_abi(implementation)
                except ContractLogicError:
                    implementation_slot = "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
                    implementation_address = self._web3.eth.get_storage_at(
                        address, implementation_slot
                    )
                    implementation_address = (
                        implementation_address[-20:].rjust(20, b"\x00").hex()
                    )
                    implementation_address = f"0x{implementation_address}"
                    return self._etherscan.get_abi(implementation_address)
        return abi

    def list_events(self, address: str, resolve_proxy: bool) -> list[str]:
        """
        List all events for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve a proxy contract abi.
        """
        abi = self.get_abi(address, resolve_proxy)
        return [self._event_signature(e) for e in abi if e["type"] == "event"]

    def get_events(
        self,
        address: str,
        event: str,
        from_time: int | str | datetime,
        to_time: int | str | datetime,
        argument_filters: Dict[str, Any] | None = None,
        resolve_proxy: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get events for a given address.

        :param address: The address to look up.
        :param event: The event to look up.
        :param from_time: The start time to look up.
        :param to_time: The end time to look up.
        :param argument_filters: The argument filters to apply.
        :param resolve_proxy: Whether to resolve a proxy contract abi.
        """
        contract = self.get_contract(address, resolve_proxy)
        contract_event = contract.events[event]
        from_block = self._etherscan.to_block(from_time)
        to_block = self._etherscan.to_block(to_time)
        from_block_timestamp = self._web3.eth.get_block(from_block)["timestamp"]
        to_block_timestamp = self._web3.eth.get_block(to_block)["timestamp"]
        return self._cache.read_or_fetch(
            [
                "contracts",
                "get_events",
                address.lower(),
                event,
                from_block,
                to_block,
                argument_filters,
            ],
            lambda: self._get_events_for_blocks(
                contract_event,
                from_block,
                to_block,
                from_block_timestamp,
                to_block_timestamp,
                argument_filters,
            ),
        )

    def _get_events_for_blocks(
        self,
        event: ContractEvent,
        from_block: int,
        to_block: int,
        from_block_timestamp: int,
        to_block_timestamp: int,
        argument_filters: Dict[str, Any] | None = None,
    ):
        current_chunk_size = to_block - from_block
        current_from_block = from_block
        res = []
        while current_from_block <= to_block:
            if current_chunk_size == 0:
                raise RuntimeError(
                    "Couldn't fetch data because minimum chunk size is reached"
                )
            try:
                current_to_block = min(
                    [current_from_block + current_chunk_size, to_block]
                )
                current_res = self._get_events_for_blocks_raw(
                    event,
                    current_from_block,
                    current_to_block,
                    argument_filters,
                )
                res += current_res
                current_from_block = current_to_block + 1
            except (ValueError, ReadTimeout):
                current_chunk_size //= 2
        for e in res:
            block = e["blockNumber"]
            timestamp = (block - from_block) / (to_block - from_block) * (
                to_block_timestamp - from_block_timestamp
            ) + from_block_timestamp
            timestamp = int(timestamp)
            e["estimatedTimestamp"] = timestamp
            e["estimatedDate"] = datetime.fromtimestamp(timestamp).isoformat()
        return res

    def _get_events_for_blocks_raw(
        self,
        event: ContractEvent,
        from_block: int,
        to_block: int,
        argument_filters: Dict[str, Any] | None = None,
    ):
        event_filter = event.create_filter(
            fromBlock=from_block,
            toBlock=to_block,
            argument_filters=argument_filters,
        )
        entries = event_filter.get_all_entries()
        return [json.loads(json_response(e)) for e in entries]

    def _get_contract(self, address: str) -> Contract:
        abi = self._etherscan.get_abi(address)
        return self._web3.eth.contract(
            address=self._web3.to_checksum_address(address), abi=abi
        )

    def _event_signature(self, event_abi: Dict[str, Any]) -> str:
        return f"{event_abi['name']}({','.join([self._event_type(p) for p in event_abi['inputs']])})"

    def _event_type(self, event_type_abi: Dict[str, Any]) -> str:
        res = f"{event_type_abi['type']} {event_type_abi['name']}"
        if event_type_abi["indexed"]:
            res = f"indexed {res}"
        return res

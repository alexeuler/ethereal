from typing import Dict, Any, Union
import json
from functools import cache
from hexbytes import HexBytes
from eth_typing.encoding import HexStr
from requests.exceptions import ReadTimeout
from datetime import datetime
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.contract.contract import (
    Contract,
    ContractEvent,
    ContractFunction,
)
from web3._utils.abi import get_abi_input_types, get_abi_output_types

from eth_utils import function_abi_to_4byte_selector
from .etherscan import Etherscan
from .base import Base
from .cache import Cache


class Web3JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Union[Dict[Any, Any], HexStr]:
        if isinstance(o, AttributeDict):
            return dict(o.items())
        if isinstance(o, HexBytes):
            return HexStr(o.hex())
        if isinstance(o, (bytes, bytearray)):
            return HexStr(HexBytes(o).hex())
        return json.JSONEncoder.default(self, o)


def json_response(response: AttributeDict) -> str:
    return json.dumps(response, cls=Web3JsonEncoder)


class Contracts(Base):
    _etherscan: Etherscan
    _web3: Web3
    _cache: Cache

    def __init__(self, etherscan: Etherscan, web3: Web3, cache: Cache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._etherscan = etherscan
        self._web3 = web3
        self._cache = cache

    def calldata(self, call: ContractFunction) -> str:
        selector = HexBytes(function_abi_to_4byte_selector(call.abi)).hex()
        abi_types = get_abi_input_types(call.abi)
        bytes_calldata = self._rpc.codec.encode(abi_types, call.args)
        return selector + HexBytes(bytes_calldata).hex()[2:]

    def decode_response(self, call: ContractFunction, response: Any) -> Any:
        abi = get_abi_output_types(call.abi)
        return self._rpc.codec.decode(abi, response)

    def get_contract(self, address: str, resolve_proxy: bool) -> Contract:
        abi = self.get_abi(address, resolve_proxy)
        return self._web3.eth.contract(address=address, abi=abi)

    def get_abi(self, address: str, resolve_proxy: bool) -> list[dict[str, Any]]:
        abi = self._etherscan.get_abi(address)
        if not resolve_proxy:
            return abi
        for f in abi:
            if not "name" in f:
                continue
            if f["name"] == "implementation":
                contract = self._get_contract(address)
                implementation = contract.functions.implementation().call()
                return self._etherscan.get_abi(implementation)
        return abi

    def list_events(self, address: str) -> list[str]:
        abi = self.get_abi(address)
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
        return self._web3.eth.contract(address=address, abi=abi)

    def __getattr__(self, name):
        if name in self._registry():
            return self._contract(self._registry()[name], name)

        def _contract(*args, **kwargs):
            return self._contract(args[0], name)

        return _contract

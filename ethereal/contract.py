from typing import Dict, Any, Union
import json
from functools import cache
from hexbytes import HexBytes
from eth_typing.encoding import HexStr
from web3.datastructures import AttributeDict
from web3.contract import (
    Contract,
    ContractEvent,
    ContractFunction,
    get_abi_input_types,
    get_abi_output_types,
)
from eth_utils import function_abi_to_4byte_selector
from .cache import AssetsCache
from .rpc import RPC
from .base import Base


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
    _assets_cache: AssetsCache
    _rpc: RPC

    def __init__(self, assets_cache: AssetsCache, rpc: RPC, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._assets_cache = assets_cache
        self._rpc = rpc

    def calldata(self, call: ContractFunction) -> str:
        selector = HexBytes(function_abi_to_4byte_selector(call.abi)).hex()
        abi_types = get_abi_input_types(call.abi)
        bytes_calldata = self._rpc.codec.encode(abi_types, call.args)
        return selector + HexBytes(bytes_calldata).hex()[2:]

    def decode_response(self, call: ContractFunction, response: Any) -> Any:
        abi = get_abi_output_types(call.abi)
        return self._rpc.codec.decode(abi, response)

    def get_events(
        self,
        event: ContractEvent,
        from_block: int,
        to_block: int,
        argument_filters: Dict[str, Any] | None = None,
    ):
        self.logger.debug(
            f"Fetching events `{event.event_name}` for contract `{event.address}` with args `{argument_filters}` for blocks `{from_block}` - `{to_block}`"
        )
        event_filter = event.create_filter(
            fromBlock=from_block,
            toBlock=to_block,
            argument_filters=argument_filters,
        )
        entries = event_filter.get_all_entries()
        return [json.loads(json_response(e)) for e in entries]

    @cache
    def _contract(self, address: str, abi_name: str) -> Contract:
        contract = self._rpc.eth.contract(
            address=self._rpc.to_checksum_address(address),
            abi=self._assets_cache.data(f"abi/{abi_name}"),
        )
        contract.abi.append(
            {
                "name": "monkey_patch_for_contract_name_not_real_event",
                "contract_name": abi_name,
                "type": "event",
            }
        )  # monkey patching for logging purposes
        return contract

    def __getattr__(self, name):
        if name in self._registry():
            return self._contract(self._registry()[name], name)

        def _contract(*args, **kwargs):
            return self._contract(args[0], name)

        return _contract

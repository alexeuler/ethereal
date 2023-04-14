from typing import Any, Dict, List
from datetime import datetime
from web3 import Web3
from .etherscan import Etherscan
from .contracts import Contracts
from .cache import Cache


class EtherealFacade:
    _etherscan: Etherscan
    _web3: Web3
    _cache: Cache

    def __init__(self, etherscan: Etherscan, web3: Web3, cache: Cache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._etherscan = etherscan
        self._web3 = web3
        self._cache = cache

    def get_block_by_timestamp(self, timestamp: int) -> int:
        return self._etherscan.get_block_by_timestamp(timestamp)

    def get_abi(self, address: str, resolve_proxy: bool) -> Dict[str, Any]:
        return self._contracts().get_abi(address, resolve_proxy)

    def list_events(self, address: str, resolve_proxy: bool) -> List[str]:
        return self._etherscan.list_events(address)

    def get_events(
        self,
        address: str,
        event: str,
        from_time: int | str | datetime,
        to_time: int | str | datetime,
        argument_filters: Dict[str, Any] | None = None,
    ):
        return self._contracts().get_events(
            address, event, from_time, to_time, argument_filters
        )

    def _contracts(self) -> Contracts:
        return Contracts(self._etherscan, self._web3, self._cache)

from typing import Any, Dict, List
from .etherscan import Etherscan
from .cache import Cache


class EtherealFacade:
    _etherscan: Etherscan
    _cache: Cache

    def __init__(self, etherscan: Etherscan, cache: Cache):
        self._etherscan = etherscan
        self._cache = cache

    def get_block_by_timestamp(self, timestamp: int) -> int:
        return self._cache.read_or_fetch(
            ["get_block_by_timestamp", timestamp],
            lambda: self._etherscan.get_block_by_timestamp(timestamp),
        )

    def get_abi(self, address: str) -> Dict[str, Any]:
        return self._cache.read_or_fetch(
            ["get_abi", address],
            lambda: self._etherscan.get_abi(address),
        )

    def list_events(self, address: str) -> List[str]:
        abi = self.get_abi(address)
        return [self._event_signature(e) for e in abi if e["type"] == "event"]

    def _event_signature(self, event_abi: Dict[str, Any]) -> str:
        return f"{event_abi['name']}({','.join([self._event_type(p) for p in event_abi['inputs']])})"

    def _event_type(self, event_type_abi: Dict[str, Any]) -> str:
        res = f"{event_type_abi['type']} {event_type_abi['name']}"
        if event_type_abi["indexed"]:
            res = f"indexed {res}"
        return res

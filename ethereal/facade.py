from .etherscan import Etherscan
from .cache import Cache


class EtherealFacade:
    _etherscan: Etherscan
    _cache: Cache

    def __init__(self, etherscan: Etherscan, cache: Cache):
        self._etherscan = etherscan
        self._cache = cache

    def get_block_by_timestamp(self, timestamp: int):
        return self._cache.read_or_fetch(
            ["get_block_by_timestamp", timestamp],
            lambda: self._etherscan.get_block_by_timestamp(timestamp),
        )

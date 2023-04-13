from typing import Any, Dict, List
from .etherscan import Etherscan
from .cache import Cache


class EtherealFacade:
    _etherscan: Etherscan

    def __init__(self, etherscan: Etherscan):
        self._etherscan = etherscan

    def get_block_by_timestamp(self, timestamp: int) -> int:
        return self._etherscan.get_block_by_timestamp(timestamp)

    def get_abi(self, address: str) -> Dict[str, Any]:
        return self._etherscan.get_abi(address)

    def list_events(self, address: str) -> List[str]:
        return self._etherscan.list_events(address)

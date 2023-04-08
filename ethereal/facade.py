from etherscan import Etherscan


class EtherealFacade:
    _etherscan: Etherscan

    def __init__(self, etherscan: Etherscan):
        self._etherscan = etherscan

    def get_block_by_timestamp(self, timestamp: int):
        return self._etherscan.get_block_by_timestamp(timestamp)

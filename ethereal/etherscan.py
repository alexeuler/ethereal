from typing import Dict, Any, TypedDict, Literal
import json
from datetime import datetime
import time
import requests
from dateutil.parser import parse
from .cache import Cache
from .base import Base
from .networks import get_network

ETH_START_TIMESTAMP = int(time.mktime(datetime(2015, 7, 30).timetuple()))

ENDPOINTS = {
    1: "https://api.etherscan.io",
    3: "https://api-ropsten.etherscan.io",
    4: "https://api-rinkeby.etherscan.io",
    5: "https://api-goerli.etherscan.io",
    42: "https://api-kovan.etherscan.io",
    137: "https://api.polygonscan.com",
    43114: "https://api.avax.network",
    250: "https://api.ftmscan.com",
    42161: "https://api.arbiscan.io",
    10: "https://api-optimistic.etherscan.io",
}


class EtherscanError(Exception):
    """
    Etherscan error
    """


class EtherscanNetworkConfig(TypedDict):
    """
    Etherscan network configuration
    """

    key: str


class EtherscanConfig(TypedDict):
    """
    Etherscan configuration
    """

    chain_id: str | int
    timeout: str
    mainnet: EtherscanNetworkConfig
    polygon: EtherscanNetworkConfig
    avalanche: EtherscanNetworkConfig
    ftm: EtherscanNetworkConfig
    arbitrum: EtherscanNetworkConfig
    optimism: EtherscanNetworkConfig


class Etherscan(Base):
    """
    Etherscan API client
    """

    _config: EtherscanConfig
    _cache: Cache
    _chain_id: int

    def __init__(self, config: EtherscanConfig, cache: Cache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        self._cache = cache
        self._chain_id = int(config["chain_id"])

    def get_block_by_timestamp(
        self,
        timestamp: int,
        closest: Literal["before", "after"] = "after",
    ) -> int:
        """
        Get the block number for a given timestamp.

        :param timestamp: The timestamp to look up.
        :param closest: Whether to return the block closest to the timestamp before or after.
        """
        return self._cache.read_or_fetch(
            ["etherscan", "get_block_by_timestamp", timestamp, closest],
            lambda: self._get_block_by_timestamp(timestamp, closest),
        )

    def to_block(self, ts: int | str | datetime) -> int:
        """
        Convert a timestamp to a block number.

        :param ts: The timestamp to convert.
        """
        if isinstance(ts, int):
            # block or timestamp
            if ts < ETH_START_TIMESTAMP:
                # block
                return ts
            # timestamp
            return self.get_block_by_timestamp(ts)
        if isinstance(ts, datetime):
            ts = int(time.mktime(ts.timetuple()))
            return self.get_block_by_timestamp(ts)
        # parseable date
        date = parse(ts)
        ts = int(time.mktime(date.timetuple()))
        return self.get_block_by_timestamp(ts)

    def get_abi(self, address: str) -> str:
        """
        Get the ABI for a given address.

        :param address: The address to look up.
        """
        return self._cache.read_or_fetch(
            ["etherscan", "get_abi", address],
            lambda: self._get_abi(address),
        )

    def _get_block_by_timestamp(
        self, timestamp: int, closest: Literal["before", "after"] = "after"
    ) -> int:
        params = {
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": timestamp,
            "closest": closest,
        }
        return int(self._fetch(params))

    def _get_abi(self, address: str) -> str:
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
        }
        return self._fetch(params)

    def _fetch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = self._endpoint()
        params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{endpoint}/api?{params_str}"
        url_with_api_key = f"{url}&apiKey={self._get_key()}"
        self.logger.debug(f"Fetching {url} from etherscan")
        resp = requests.get(url_with_api_key, timeout=int(self._config["timeout"]))
        self.logger.debug(f"Got response {resp.status_code}")
        resp = resp.json()
        if resp["status"] != "1":
            raise EtherscanError(
                f"Error fetching data from etherscan: {resp['result']}"
            )
        return json.loads(resp["result"])

    def _get_key(self) -> str:
        return self._config[self._get_network()]["key"]

    def _endpoint(self) -> str:
        return ENDPOINTS[self._chain_id]

    def _get_network(self) -> str:
        return get_network(self._chain_id)

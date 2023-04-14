from typing import Dict, Any, TypedDict, Literal, List
import requests
import json
from datetime import datetime
from dateutil.parser import parse
import time
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


class EtherscanNetworkConfig(TypedDict):
    key: str


class EtherscanConfig(TypedDict):
    chain_id: str | int
    mainnet: EtherscanNetworkConfig
    polygon: EtherscanNetworkConfig
    avalanche: EtherscanNetworkConfig
    ftm: EtherscanNetworkConfig
    arbitrum: EtherscanNetworkConfig
    optimism: EtherscanNetworkConfig


class Etherscan(Base):
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
        return self._cache.read_or_fetch(
            ["etherscan", "get_block_by_timestamp", timestamp, closest],
            lambda: self._get_block_by_timestamp(timestamp, closest),
        )

    def to_block(self, ts: int | str | datetime) -> int:
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

    def _event_signature(self, event_abi: Dict[str, Any]) -> str:
        return f"{event_abi['name']}({','.join([self._event_type(p) for p in event_abi['inputs']])})"

    def _event_type(self, event_type_abi: Dict[str, Any]) -> str:
        res = f"{event_type_abi['type']} {event_type_abi['name']}"
        if event_type_abi["indexed"]:
            res = f"indexed {res}"
        return res

    def _fetch(
        self, params: Dict[str, Any], chain_id: int | None = None
    ) -> Dict[str, Any]:
        endpoint = self._endpoint()
        params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{endpoint}/api?{params_str}"
        url_with_api_key = f"{url}&apiKey={self._get_key()}"
        self.logger.debug(f"Fetching {url} from etherscan")
        resp = requests.get(url_with_api_key)
        self.logger.debug(f"Got response {resp.status_code}")
        resp = resp.json()
        if resp["status"] != "1":
            raise Exception(f"Error fetching data from etherscan: {resp['result']}")
        return json.loads(resp["result"])

    def _get_key(self) -> str:
        return self._config[self._get_network()]["key"]

    def _endpoint(self) -> str:
        return ENDPOINTS[self._chain_id]

    def _get_network(self) -> str:
        return get_network(self._chain_id)

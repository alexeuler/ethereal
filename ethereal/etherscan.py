from typing import Dict, Any, TypedDict, Literal
import requests
from .base import Base
from .networks import get_network, get_chain_id

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
    default_chain_id: str | int
    mainnet: EtherscanNetworkConfig
    polygon: EtherscanNetworkConfig
    avalanche: EtherscanNetworkConfig
    ftm: EtherscanNetworkConfig
    arbitrum: EtherscanNetworkConfig
    optimism: EtherscanNetworkConfig


class Etherscan(Base):
    _config: EtherscanConfig
    _default_chain_id: int

    def __init__(self, config: EtherscanConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        self._default_chain_id = int(config["default_chain_id"])

    def get_block_by_timestamp(
        self,
        timestamp: int,
        closest: Literal["before", "after"] = "after",
        chain_id: int | None = None,
    ) -> int:
        params = {
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": timestamp,
            "closest": closest,
        }
        return int(self._fetch(params, chain_id=chain_id))

    def _fetch(
        self, params: Dict[str, Any], chain_id: int | None = None
    ) -> Dict[str, Any]:
        endpoint = self._endpoint(chain_id)
        params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{endpoint}/api?{params_str}"
        url_with_api_key = f"{url}&apiKey={self._get_key(chain_id)}"
        self.logger.debug(f"Fetching {url} from etherscan")
        resp = requests.get(url_with_api_key)
        self.logger.debug(f"Got response {resp.status_code}")
        resp = resp.json()
        if resp["status"] != "1":
            raise Exception(f"Error fetching data from etherscan: {resp['result']}")
        return resp["result"]

    def _get_key(self, chain_id: int | None = None) -> str:
        network = self._get_network(chain_id)
        return self._config[network]["key"]

    def _endpoint(self, chain_id: int | None = None) -> str:
        network = self._get_network(chain_id)
        chain_id = get_chain_id(network)
        return ENDPOINTS[chain_id]

    def _get_network(self, chain_id: int | None = None) -> str:
        chain_id = self._chain_id(chain_id)
        return get_network(chain_id)

    def _chain_id(self, chain_id: int | None) -> int:
        return chain_id if chain_id is not None else self._default_chain_id

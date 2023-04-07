CHAIN_IDS_INDEX = {
    1: "mainnet",
    3: "ropsten",
    4: "rinkeby",
    5: "goerli",
    42: "kovan",
    137: "polygon",
    43114: "avalanche",
    250: "fantom",
    42161: "arbitrum",
    10: "optimism",
}

NETWORKS_INDEX = {v: k for k, v in CHAIN_IDS_INDEX.items()}


def get_chain_id(network: str) -> int:
    """
    Returns the chain ID for a given network name

    @param network: The network name to get the chain ID for

    """
    return NETWORKS_INDEX[network.lower()]


def get_network(chain_id: int) -> str:
    """
    Returns the network name for a given chain_id

    @param chain_id: The chain ID to get the network name for
    """
    return CHAIN_IDS_INDEX[chain_id]

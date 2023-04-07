import logging.config
from dependency_injector import containers, providers
from etherscan import Etherscan


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["../config.yml"])
    logging = providers.Resource(logging.config.dictConfig, config=config.logging)
    etherscan = providers.Singleton(Etherscan, config=config.etherscan)

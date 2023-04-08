import logging.config
from dependency_injector import containers, providers
from etherscan import Etherscan
from facade import EtherealFacade


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["../config.yml"])
    logging = providers.Resource(logging.config.dictConfig, config=config.logging)
    etherscan = providers.Factory(Etherscan, config=config.etherscan)
    ethereal_facade = providers.Factory(EtherealFacade, etherscan=etherscan)

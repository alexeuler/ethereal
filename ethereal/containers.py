import os
import logging.config
from dependency_injector import containers, providers
from .accounts import Accounts
from .etherscan import Etherscan
from .facade import EtherealFacade
from .cache import MemoryCache, DbCache, Cache

current_folder = os.path.realpath(os.path.dirname(__file__))


class AppContainer(containers.DeclarativeContainer):
    """
    The dependency injection container for Ethereal
    """

    config = providers.Configuration(
        yaml_files=[os.path.abspath(f"{current_folder}/config.yml")]
    )
    memory_cache = providers.Factory(MemoryCache)
    db_cache = providers.Singleton(DbCache, config=config.cache)
    cache = providers.Factory(Cache, memory_cache=memory_cache, db_cache=db_cache)
    etherscan = providers.Factory(Etherscan, config=config.etherscan, cache=cache)
    accounts = providers.Factory(Accounts)
    ethereal_facade = providers.Factory(
        EtherealFacade, etherscan=etherscan, accounts=accounts, cache=cache
    )

import os
import logging.config
from dependency_injector import containers, providers
from .etherscan import Etherscan
from .facade import EtherealFacade
from .cache import MemoryCache, DbCache, Cache

current_folder = os.path.realpath(os.path.dirname(__file__))


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration(
        yaml_files=[os.path.abspath(f"{current_folder}/../config.yml")]
    )
    logging = providers.Resource(logging.config.dictConfig, config=config.logging)
    memory_cache = providers.Factory(MemoryCache)
    db_cache = providers.Singleton(DbCache, config=config.cache)
    cache = providers.Factory(Cache, memory_cache=memory_cache, db_cache=db_cache)
    etherscan = providers.Factory(Etherscan, config=config.etherscan, cache=cache)
    ethereal_facade = providers.Factory(EtherealFacade, etherscan=etherscan)

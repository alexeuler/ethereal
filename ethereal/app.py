from web3 import Web3
from .containers import AppContainer
from .networks import get_chain_id
from .facade import EtherealFacade


class Ethereal(Web3):
    _log_level: str | None
    _facade: EtherealFacade | None
    _w3: Web3
    e: EtherealFacade

    def __init__(self, w3: Web3, log_level: str | None = None):
        self._w3 = w3
        self._log_level = log_level
        self._facade = None

    def __getattr__(self, name):
        if name != "e":
            return getattr(self._w3, name)

        if self._facade is None:
            app = self._init_app()
            self._facade = app.ethereal_facade()

        return self._facade

    def _init_app(self):
        log_level = self._log_level.upper() if not self._log_level is None else None
        chain_id = self._w3.eth.chain_id

        app = AppContainer()
        if not log_level is None:
            app.config.logging.loggers["root"].level.from_value(log_level)

        app.config.etherscan.default_chain_id.from_value(chain_id)

        try:
            app.init_resources()
            app.wire(modules=[__name__])
            return app
        except Exception as e:
            print(f"Error initializing Ethereal: {e}")
            raise e

from typing import List, TypedDict
from datetime import datetime
from web3 import Web3
from web3.providers import BaseProvider, HTTPProvider, IPCProvider, WebsocketProvider
from .base import Base
from urllib.parse import urlparse
from eth_typing import URI


def load_provider_from_uri(uri_string: URI, timeout=10) -> BaseProvider:
    uri = urlparse(uri_string)
    if uri.scheme == "file":
        return IPCProvider(uri.path)
    elif uri.scheme in ["http", "https"]:
        return HTTPProvider(uri_string, request_kwargs={"timeout": timeout})
    elif uri.scheme in ["ws", "wss"]:
        return WebsocketProvider(uri_string, websocket_timeout=timeout)
    else:
        raise NotImplementedError(
            "Web3 does not know how to connect to scheme "
            f"{uri.scheme!r} in {uri_string!r}"
        )


class RPCException(Exception):
    pass


class RPCConfig(TypedDict):
    endpoints: List[str]
    max_fails: int
    max_fails_period_secs: int
    timeout: int


class RPC(Base):
    _config: RPCConfig
    _w3s: List[Web3]
    _current_instance_num: int
    _fails: List[datetime]

    def __init__(self, config: RPCConfig):
        super().__init__()
        if len(config["endpoints"]) == 0:
            raise RPCException("Cannot create RPC with 0 endpoints")
        self._config = config
        self.logger.debug(f"Initializing {len(config['endpoints'])} web3 backends...")
        self._w3s = [
            Web3(load_provider_from_uri(endpoint, config["timeout"]))
            for endpoint in config["endpoints"]
        ]
        self.logger.debug(f"Done")
        self._current_instance_num = 0
        self._fails = []
        self._log_current_endpoint()

    def report_fail(self):
        now = datetime.now()

        self._fails.append(datetime.now())
        self._fails = [
            f
            for f in self._fails
            if (now - f).total_seconds() <= self._config["max_fails_period_secs"]
        ]
        if len(self._fails) >= self._config["max_fails"]:
            self.rotate()

    def rotate(self):
        self.logger.info("Rotating RPC endpoint")
        self._current_instance_num += 1
        self._current_instance_num = self._current_instance_num % len(self._w3s)
        self._fails = []
        self._log_current_endpoint()

    def _fails_count(self):
        self._fails = [
            fail
            for fail in self._fails
            if (fail - self._fails[0]).total_seconds()
            <= self._config["max_fails_period_secs"]
        ]
        return len(self._fails)

    def _log_current_endpoint(self):
        self.logger.info(
            f"Current endpoint is {self._config['endpoints'][self._current_instance_num]}"
        )

    def _current_instance(self) -> Web3:
        return self._w3s[self._current_instance_num]

    def __getattr__(self, name):
        return getattr(self._current_instance(), name)

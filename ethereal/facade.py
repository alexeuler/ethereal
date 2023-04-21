from typing import Any, Dict, List
from datetime import datetime
from web3 import Web3
from web3.contract import Contract
from .accounts import Accounts, Account
from .etherscan import Etherscan
from .contracts import Contracts
from .cache import Cache


class EtherealFacade:
    """
    The main class containing Ethereal's functionality.
    """

    _etherscan: Etherscan
    _web3: Web3
    _accounts: Accounts
    _cache: Cache

    def __init__(
        self,
        etherscan: Etherscan,
        web3: Web3,
        accounts: Accounts,
        cache: Cache,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._etherscan = etherscan
        self._web3 = web3
        self._accounts = accounts
        self._cache = cache

    def get_block_by_timestamp(self, timestamp: int = True) -> int:
        """
        Get the block number for a given timestamp.

        :param timestamp: The timestamp to look up.
        """
        return self._etherscan.get_block_by_timestamp(timestamp)

    def get_abi(self, address: str, resolve_proxy: bool = True) -> Dict[str, Any]:
        """
        Get the ABI for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve proxies. If true, the ABI for the
                              implementation contract will be returned.
        """
        return self._contracts().get_abi(address, resolve_proxy)

    def list_events(self, address: str, resolve_proxy: bool = True) -> List[str]:
        """
        Get a list of events for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve proxies. If true, the ABI for the
        """
        return self._contracts().list_events(address, resolve_proxy)

    def get_contract(self, address: str, resolve_proxy: bool = True) -> Contract:
        """
        Get a contract for a given address.

        :param address: The address to look up.
        :param resolve_proxy: Whether to resolve proxies. If true, the ABI for the
                              implementation contract will be used.
        """
        return self._contracts().get_contract(address, resolve_proxy)

    def derive_account(self, seed_phrase: str, index: int) -> Account:
        """
        Derive public and a private key from a seed phrase (Metamask or other bip 44)

        :param seed_phrase: The seed phrase to use
        :param index: The index to use

        :return: The pubic and private key
        """
        return self._accounts.derive_account(seed_phrase, index)

    def generate_mnemonic(self, strength: int = 128) -> str:
        """
        Generate a mnemonic

        :param strength: The strength of the mnemonic. Default = 128 (12 words)

        :return: The mnemonic
        """
        return self._accounts.generate_mnemonic(strength=strength)

    def get_events(
        self,
        address: str,
        event: str,
        from_time: int | str | datetime,
        to_time: int | str | datetime,
        argument_filters: Dict[str, Any] | None = None,
        resolve_proxy: bool = True,
    ):
        """
        Get events for a given address.

        :param address: The address to look up.
        :param event: The event name to look up.
        :param from_time: The start time to look up. Can be a block number, a timestamp, a datetime, or a string with datetime.
        :param to_time: The end time to look up. Can be a block number, a timestamp, a datetime , or a string with datetime.
        :param argument_filters: A dictionary of argument names and values to filter by.
        :param resolve_proxy: Whether to resolve proxies. If true, the ABI for the implementation contract will be used.
        """
        return self._contracts().get_events(
            address, event, from_time, to_time, argument_filters, resolve_proxy
        )

    def _contracts(self) -> Contracts:
        return Contracts(self._etherscan, self._web3, self._cache)

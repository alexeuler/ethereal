from typing import TypedDict
from hdwallet import BIP44HDWallet
from hdwallet.utils import generate_mnemonic
from hdwallet.symbols import ETH as SYMBOL


class Account(TypedDict):
    """
    Account
    """

    address: str
    private_key: str


class Accounts:
    """
    Working with accounts
    """

    def derive_account(self, seed_phrase: str, index: int) -> Account:
        """
        Derive public and a private key from a seed phrase (Metamask or other bip 44)

        :param seed_phrase: The seed phrase to use
        :param index: The index to use

        :return: The pubic and private key
        """
        path = f"m/44'/60'/0'/0/{index}"
        wallet = BIP44HDWallet(symbol=SYMBOL).from_mnemonic(seed_phrase)
        wallet.clean_derivation()
        wallet.from_path(path)
        return {"address": wallet.address(), "private_key": wallet.private_key()}

    def generate_mnemonic(self, strength: int = 128) -> str:
        """
        Generate a mnemonic

        :param strength: The strength of the mnemonic. Default = 128 (12 words)

        :return: The mnemonic
        """
        return generate_mnemonic(strength=strength)

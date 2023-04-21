import os
import pprint
import json
import click
from web3 import Web3
from dependency_injector.wiring import inject
from ethereal.networks import load_provider_from_uri
from ethereal.app import Ethereal


current_folder = os.path.realpath(os.path.dirname(__file__))
web3: Ethereal = None


@click.group()
@click.option(
    "-ll",
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    help="Log level for the app",
)
@click.option(
    "-r",
    "--rpc",
    type=str,
    default=lambda: os.environ.get("WEB3_PROVIDER_URI", "http://localhost:8545"),
    help="RPC endpoint to use",
)
def cli(log_level: str | None, rpc: str | None):
    """
    Ethereal CLI
    """
    global web3
    web3 = Ethereal(Web3(load_provider_from_uri(rpc)), log_level)


@cli.command()
@click.argument("timestamp", type=int)
@inject
def get_block_by_timestamp(
    timestamp: int,
):
    """
    Get block by timestamp

    @param timestamp: Timestamp to search for
    """

    print(web3.e.get_block_by_timestamp(timestamp))


@cli.command()
@click.argument("seed_phrase", type=str)
@click.argument("index", type=int)
@click.option("-p", "--passphrase", type=str, help="Passphrase to use")
@inject
def derive_account(
    seed_phrase: str,
    index: int,
    passphrase: str | None = None,
):
    """
    Derive metamask account from seed_phrase

    @param seed_phrase: Seed phrase to use
    @param index: Index to use
    @param passphrase: Passphrase to use
    """

    print(web3.e.derive_account(seed_phrase, index, passphrase))


@cli.command()
@click.argument("strength", type=int, default=128)
@inject
def generate_seed_phrase(
    strength: int,
):
    """
    Generate a mnemonic

    @param strength: Strength of the mnemonic. Default = 128 (12 words)
    """

    print(web3.e.generate_seed_phrase(strength))


@cli.command()
@click.argument("address", type=str)
@click.argument("proxy", type=bool, default=True)
@inject
def get_abi(
    address: str,
    proxy: bool,
):
    """
    Get ABI by contract address

    @param address: Address of the contracts
    @param proxy: Resolve proxy contracts. Default = True.
    """

    print(json.dumps(web3.e.get_abi(address, proxy), indent=4))


@cli.command()
@click.argument("address", type=str)
@click.argument("proxy", type=bool, default=True)
@inject
def list_events(
    address: str,
    proxy: bool,
):
    """
    List events for contract address

    @param address: Address of the contracts
    @param proxy: Resolve proxy contracts. Default = True.
    """

    pprint.pprint(web3.e.list_events(address, proxy))


@cli.command()
@click.argument("address", type=str)
@click.argument("event", type=str)
@click.argument("from_time", type=str)
@click.argument("to_time", type=str)
@inject
def get_events(
    address: str,
    event: str,
    from_time: int | str,
    to_time: int | str,
):
    """
    Get events of a contract

    @param address: Address of the contract
    @param event: Event name
    @param from_time: Date or unix timestamp or block number
    @param to_time: Date or unix timestamp or block number
    """

    print(json.dumps(web3.e.get_events(address, event, from_time, to_time), indent=4))


def start_cli():
    """
    Start the CLI
    """
    # pylint: disable=no-value-for-parameter
    cli(auto_envvar_prefix="ETHEREAL")


if __name__ == "__main__":
    start_cli()

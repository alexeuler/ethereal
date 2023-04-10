import os
import click
from web3 import Web3
from dependency_injector.wiring import inject
import pprint
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
@click.argument("address", type=str)
@inject
def get_abi(
    address: str,
):
    """
    Get ABI by contract address

    @param address: Address of the contracts
    """

    print(web3.e.get_abi(address))


@cli.command()
@click.argument("address", type=str)
@inject
def list_events(
    address: str,
):
    """
    List events for contract address

    @param address: Address of the contracts
    """

    pprint.pprint(web3.e.list_events(address))


def start_cli():
    cli(auto_envvar_prefix="ETHEREAL")


if __name__ == "__main__":
    start_cli()

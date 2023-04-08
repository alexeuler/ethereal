import os
import click
from typing import List
from containers import AppContainer
from dependency_injector.wiring import Provide, inject
from etherscan import Etherscan
from networks import load_provider_from_uri
from app import Ethereal

current_folder = os.path.realpath(os.path.dirname(__file__))
web3: Ethereal = None


@click.group()
@click.option(
    "-c",
    "--chain",
    type=click.Choice(
        ["mainnet", "polygon", "avalanche", "ftm", "arbitrum", "optimism"],
        case_sensitive=False,
    ),
    default="mainnet",
    help="Chain to use",
)
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
def cli(chain: str | None, log_level: str | None, rpc: str | None):
    global web3
    web3 = Ethereal(load_provider_from_uri(rpc), chain, log_level)


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


def start_cli():
    cli(auto_envvar_prefix="ETHEREAL")


if __name__ == "__main__":
    start_cli()

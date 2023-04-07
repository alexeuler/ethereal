import os
import click
from typing import List
from containers import AppContainer
from dependency_injector.wiring import Provide, inject
from etherscan import Etherscan
from networks import get_chain_id

current_folder = os.path.realpath(os.path.dirname(__file__))


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
    help="RPC endpoint to use",
)
def cli(chain: str | None, log_level: str | None, rpc: str | None):
    log_level = log_level.upper()

    app = AppContainer()
    if not log_level is None:
        app.config.logging.loggers["root"].level.from_value(log_level)
    if not chain is None:
        app.config.etherscan.default_chain_id.from_value(get_chain_id(chain))

    try:
        app.init_resources()
        app.wire(modules=[__name__])
    except Exception as e:
        print(f"Error initializing the app: {e}")
        raise e


@cli.command()
@click.argument("timestamp", type=int)
@inject
def get_block_by_timestamp(
    timestamp: int,
    etherscan: Etherscan = Provide[AppContainer.etherscan],
):
    """
    Get block by timestamp

    @param timestamp: Timestamp to search for
    """
    print(etherscan.get_block_by_timestamp(timestamp))


def start_cli():
    cli(auto_envvar_prefix="ETHEREAL")


if __name__ == "__main__":
    start_cli()

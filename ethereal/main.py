import os
import click
from typing import List
from containers import AppContainer
from dependency_injector.wiring import Provide, inject
from core import Telegram, Contracts, Promise
from data import GearboxProtocol, GearboxCreditAccounts, ConvexProtocol
from liquidator import (
    HealthFactorSeeker,
    LiquidatorExecutor,
    LiquidatorServer,
    Unwinder,
)

current_folder = os.path.realpath(os.path.dirname(__file__))


@click.group()
@click.option(
    "-lf",
    "--log-filename",
    type=str,
    default="default.log",
    help="Filename for the logger (will stored in ./logs folder)",
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
    "rpcs",
    multiple=True,
    help="One or more Ethereum RPC endpoints. For env variable use space-separated values",
)
def cli(log_filename: str, log_level: str, rpcs: List[str]):
    log_level = log_level.upper()
    rpcs = [rpc.replace('"', "").replace("'", "") for rpc in rpcs]

    app = AppContainer()

    app.config.core.logging.handlers.file.filename.from_value(
        os.path.realpath(f"{current_folder}/../logs/{log_filename}")
    )
    app.config.core.logging.loggers["root"].level.from_value(log_level)
    app.config.core.logging.loggers.arkenstone_gearbox_bot.level.from_value(log_level)
    app.config.core.rpc.endpoints.from_value(rpcs)

    try:
        app.core.init_resources()
        app.wire(modules=[__name__, "core.promise"])
    except Exception as e:
        print(f"Error initializing the app: {e}")
        raise e


@cli.command()
@inject
def bot_contract_info(
    contracts: Contracts = Provide[AppContainer.core.contracts],
):
    """
    Get bot contract info
    """
    owner, managers = Promise.traverse(
        [
            Promise.contract(contracts.arkenstone_gearbox.functions.owner()),
            Promise.contract(contracts.arkenstone_gearbox.functions.managers()),
        ]
    ).call()
    print({"owner": owner, "managers": managers})


@cli.command()
@inject
def fetch_gearbox_protocol(
    gearbox_protocol: GearboxProtocol = Provide[AppContainer.data.gearbox_protocol],
):
    """
    Fetch and save the data for the gearbox protocol
    """
    gearbox_protocol.save()


@cli.command()
@inject
def fetch_convex_protocol(
    convex_protocol: ConvexProtocol = Provide[AppContainer.data.convex_protocol],
):
    """
    Fetch and save the data for the convex protocol
    """
    convex_protocol.save()


@cli.command()
@inject
def fetch_gearbox_credit_accounts(
    gearbox_credit_accounts: GearboxCreditAccounts = Provide[
        AppContainer.data.gearbox_credit_accounts
    ],
):
    """
    Fetch and save the data for the gearbox credit accounts
    """

    gearbox_credit_accounts.save()


@cli.command()
@inject
def prefetch(
    gearbox_protocol: GearboxProtocol = Provide[AppContainer.data.gearbox_protocol],
    gearbox_credit_accounts: GearboxCreditAccounts = Provide[
        AppContainer.data.gearbox_credit_accounts
    ],
    gearbox_liquidations: GearboxCreditAccounts = Provide[
        AppContainer.data.gearbox_liquidations
    ],
    convex_protocol: ConvexProtocol = Provide[AppContainer.data.convex_protocol],
):
    """
    Prefetch cache data for bot
    """

    gearbox_protocol.save()
    gearbox_credit_accounts.save()
    convex_protocol.save()
    gearbox_liquidations.save()


@cli.command()
@inject
def fetch_low_health_factors(
    health_factor_seeker: HealthFactorSeeker = Provide[
        AppContainer.liquidator.health_factor_seeker
    ],
):
    """
    Get low health factor accounts
    """
    print(
        f"Found {len(health_factor_seeker.low_credit_accounts_healths)} credit accounts with low health: {health_factor_seeker.low_credit_accounts_healths}"
    )
    print(
        f"Health factor distrubution: {health_factor_seeker.credit_accounts_healths_distribution}"
    )


@cli.command()
@click.argument("message")
@inject
def telegram(
    message: str,
    telegram: Telegram = Provide[AppContainer.core.telegram],
):
    """
    Send message to telegram chat
    """
    telegram.notify(message)


@cli.command()
@inject
def liquidate(
    liquidator_executor: LiquidatorExecutor = Provide[
        AppContainer.liquidator.liquidator_executor
    ],
):
    """
    Run a liquidator job (seek low health and liquidate)
    """
    liquidator_executor.run()


@cli.command()
@click.argument("credit_account")
@inject
def unwind(
    credit_account: str,
    unwinder: Unwinder = Provide[AppContainer.liquidator.unwinder.unwinder],
):
    """
    Run a liquidator job (seek low health and liquidate)
    """
    print(unwinder.liquidation_multicall_calldata_for_credit_account(credit_account))


@cli.command()
@inject
def start(
    liquidator_server: LiquidatorServer = Provide[
        AppContainer.liquidator.liquidator_server
    ],
):
    """
    Starts a liquidation bot
    """
    liquidator_server.run()


def start_cli():
    cli(auto_envvar_prefix="ARKENSTONE_GEARBOX_BOT")


if __name__ == "__main__":
    start_cli()

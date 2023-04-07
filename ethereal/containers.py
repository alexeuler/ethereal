from dependency_injector import containers, providers


class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration(yaml_files=["../config.yml"])

    core = providers.Container(
        CoreContainer,
        config=config.core,
    )

    data = providers.Container(
        DataContainer,
        root_folder=core.root_folder,
        contracts=core.contracts,
        tokens=core.tokens,
        rpc=core.rpc,
    )

    liquidator = providers.Container(
        LiquidatorContainer,
        config=config.liquidator,
        contracts=core.contracts,
        telegram=core.telegram,
        telemetry=core.telemetry,
        rpc=core.rpc,
        gearbox_protocol=data.gearbox_protocol,
        gearbox_credit_accounts=data.gearbox_credit_accounts,
        gearbox_liquidations=data.gearbox_liquidations,
        convex_protocol=data.convex_protocol,
        tokens=core.tokens,
        assets_cache=core.assets_cache,
        signer=core.signer,
    )

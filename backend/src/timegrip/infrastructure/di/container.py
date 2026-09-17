from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from timegrip.infrastructure.di.providers.app_provider import AppProvider
from timegrip.infrastructure.di.providers.config_provider import ConfigProvider
from timegrip.infrastructure.di.providers.gateway_provider import (
    GatewayProvider,
    WebGatewayProvider,
)
from timegrip.infrastructure.email.config import load_email_config
from timegrip.infrastructure.frontend.config import load_frontend_config
from timegrip.infrastructure.jwt.config import load_jwt_token_config
from timegrip.infrastructure.postgres.config import load_postgres_config


def create_app_container() -> AsyncContainer:
    load_postgres_config()
    load_jwt_token_config()
    load_email_config()
    load_frontend_config()

    return make_async_container(
        AppProvider(),
        ConfigProvider(),
        GatewayProvider(),
        WebGatewayProvider(),
        FastapiProvider(),
    )


def create_worker_container() -> AsyncContainer:
    load_postgres_config()
    load_email_config()

    return make_async_container(
        AppProvider(),
        ConfigProvider(),
        GatewayProvider(),
    )

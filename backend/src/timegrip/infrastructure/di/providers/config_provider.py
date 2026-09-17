from dishka import Provider, Scope, provide

from timegrip.application.common.email_config import EmailConfig
from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.common.jwt_token_config import JWTTokenConfig
from timegrip.infrastructure.email.config import load_email_config
from timegrip.infrastructure.frontend.config import load_frontend_config
from timegrip.infrastructure.jwt.config import load_jwt_token_config
from timegrip.infrastructure.postgres.config import (
    PostgresConfig,
    load_postgres_config,
)


class ConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def get_postgres_config(self) -> PostgresConfig:
        return load_postgres_config()

    @provide(scope=Scope.APP)
    def get_jwt_token_config(self) -> JWTTokenConfig:
        return load_jwt_token_config()

    @provide(scope=Scope.APP)
    def get_email_config(self) -> EmailConfig:
        return load_email_config()

    @provide(scope=Scope.APP)
    def get_frontend_config(self) -> FrontendConfig:
        return load_frontend_config()

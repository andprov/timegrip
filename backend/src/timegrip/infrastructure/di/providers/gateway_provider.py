from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from timegrip.adapters.common.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from timegrip.adapters.common.permission_manager import PermissionManager
from timegrip.adapters.common.token_id_provider import (
    JWTTokenManager,
    TokenIdProvider,
)
from timegrip.adapters.db.activation_code_gateway import (
    DatabaseActivationCodeGateway,
)
from timegrip.adapters.db.email_outbox_gateway import (
    DatabaseEmailOutboxGateway,
)
from timegrip.adapters.db.email_queue_gateway import (
    DatabaseEmailQueueGateway,
)
from timegrip.adapters.db.password_reset_code_gateway import (
    DatabasePasswordResetCodeGateway,
)
from timegrip.adapters.db.project_gateway import DatabaseProjectGateway
from timegrip.adapters.db.refresh_token_gateway import (
    DatabaseRefreshTokenGateway,
)
from timegrip.adapters.db.timer_gateway import DatabaseTimerGateway
from timegrip.adapters.db.user_gateway import DatabaseUserGateway
from timegrip.adapters.email.console_sender import ConsoleEmailSender
from timegrip.adapters.email.smtp_sender import SMTPEmailSender
from timegrip.application.auth.gateway import RefreshTokenGateway
from timegrip.application.common.email_config import EmailConfig
from timegrip.application.common.id_provider_gateway import (
    IdProviderGateway,
)
from timegrip.application.common.jwt_token_config import JWTTokenConfig
from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.outbox.email_outbox_gateway import (
    EmailOutboxGateway,
)
from timegrip.application.outbox.email_queue_gateway import (
    EmailQueueGateway,
)
from timegrip.application.outbox.email_sender_gateway import (
    EmailSenderGateway,
)
from timegrip.application.password_reset.gateway import (
    PasswordResetCodeGateway,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.gateway import TimerGateway
from timegrip.application.user.gateway import UserGateway
from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)
from timegrip.infrastructure.postgres.config import PostgresConfig
from timegrip.infrastructure.postgres.session import get_async_sessionmaker


class GatewayProvider(Provider):
    @provide(scope=Scope.APP)
    def get_session_maker(
        self,
        config: PostgresConfig,
    ) -> async_sessionmaker[AsyncSession]:
        return get_async_sessionmaker(config=config)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_jwt_token_manager(self, config: JWTTokenConfig) -> JWTTokenManager:
        return JWTTokenManager(config=config)

    bcrypt_password_hasher = provide(
        source=BcryptPasswordHasher,
        scope=Scope.REQUEST,
        provides=PasswordHasherGateway,
    )
    permission_manager = provide(
        source=PermissionManager,
        scope=Scope.REQUEST,
        provides=PermissionGateway,
    )
    user_gateway = provide(
        source=DatabaseUserGateway,
        scope=Scope.REQUEST,
        provides=UserGateway,
    )
    project_gateway = provide(
        source=DatabaseProjectGateway,
        scope=Scope.REQUEST,
        provides=ProjectGateway,
    )
    timer_gateway = provide(
        source=DatabaseTimerGateway,
        scope=Scope.REQUEST,
        provides=TimerGateway,
    )
    refresh_token_gateway = provide(
        source=DatabaseRefreshTokenGateway,
        scope=Scope.REQUEST,
        provides=RefreshTokenGateway,
    )
    activation_code_gateway = provide(
        source=DatabaseActivationCodeGateway,
        scope=Scope.REQUEST,
        provides=ActivationCodeGateway,
    )
    email_queue_gateway = provide(
        source=DatabaseEmailQueueGateway,
        scope=Scope.REQUEST,
        provides=EmailQueueGateway,
    )
    password_reset_code_gateway = provide(
        source=DatabasePasswordResetCodeGateway,
        scope=Scope.REQUEST,
        provides=PasswordResetCodeGateway,
    )
    email_outbox_gateway = provide(
        source=DatabaseEmailOutboxGateway,
        scope=Scope.REQUEST,
        provides=EmailOutboxGateway,
    )

    @provide(scope=Scope.REQUEST)
    def get_email_sender_gateway(
        self,
        config: EmailConfig,
    ) -> EmailSenderGateway:
        if config.sender_backend == "console":
            return ConsoleEmailSender()
        return SMTPEmailSender(config=config)


class WebGatewayProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_token_id_provider(
        self,
        manager: JWTTokenManager,
        request: Request,
    ) -> IdProviderGateway:
        return TokenIdProvider(
            token_manager=manager,
            request=request,
        )

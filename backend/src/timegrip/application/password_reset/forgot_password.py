import logging
from datetime import UTC, datetime, timedelta

from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.outbox.email_queue_gateway import (
    EmailQueueGateway,
)
from timegrip.application.password_reset.gateway import (
    PasswordResetCodeGateway,
)
from timegrip.application.password_reset.password_reset_code_manager import (
    PASSWORD_RESET_CODE_RESEND_COOLDOWN_SECONDS,
    PasswordResetCodeManager,
)
from timegrip.application.password_reset.password_reset_email import (
    build_password_reset_email,
    build_password_reset_url,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Email

logger = logging.getLogger(__name__)


class ForgotPasswordInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_reset_code_gateway: PasswordResetCodeGateway,
        password_reset_code_manager: PasswordResetCodeManager,
        email_queue_gateway: EmailQueueGateway,
        frontend_config: FrontendConfig,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_reset_code_gateway = password_reset_code_gateway
        self.password_reset_code_manager = password_reset_code_manager
        self.email_queue_gateway = email_queue_gateway
        self.frontend_config = frontend_config

    async def __call__(self, email: str) -> None:
        user = await self.user_gateway.get_user_by_email(email=Email(email))
        if user is None:
            logger.info(
                "Forgot password requested for unknown email, ignoring",
            )
            return

        latest_code = (
            await self.password_reset_code_gateway.get_latest_code_for_user(
                user_id=user.id,
            )
        )
        cooldown = timedelta(
            seconds=PASSWORD_RESET_CODE_RESEND_COOLDOWN_SECONDS,
        )
        if (
            latest_code is not None
            and latest_code.created_at is not None
            and latest_code.created_at > datetime.now(UTC) - cooldown
        ):
            logger.info(
                f"Forgot password | [user_id: {user.id} Sent recently, "
                "ignoring]",
            )
            return

        code = await self.password_reset_code_manager(user_id=user.id)
        reset_url = build_password_reset_url(
            frontend_url=self.frontend_config.url,
            email=user.email.value,
            code=code,
        )
        reset_email = build_password_reset_email(
            code,
            reset_url=reset_url,
            locale=user.locale,
        )
        await self.email_queue_gateway.enqueue(
            to_email=user.email.value,
            subject=reset_email.subject,
            body=reset_email.body,
        )
        logger.info(f"Forgot password | [user_id: {user.id}]")

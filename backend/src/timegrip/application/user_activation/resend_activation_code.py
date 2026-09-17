import logging
from uuid import UUID

from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.exceptions import (
    ActivationCodeRecentlySentError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.outbox.email_queue_gateway import (
    EmailQueueGateway,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.application.user_activation.activation_code_manager import (
    ActivationCodeManager,
    seconds_until_code_resend,
)
from timegrip.application.user_activation.activation_email import (
    build_activation_email,
    build_activation_url,
)
from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)

logger = logging.getLogger(__name__)


class ResendActivationCodeInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        activation_code_gateway: ActivationCodeGateway,
        activation_code_manager: ActivationCodeManager,
        email_queue_gateway: EmailQueueGateway,
        frontend_config: FrontendConfig,
    ) -> None:
        self.user_gateway = user_gateway
        self.activation_code_gateway = activation_code_gateway
        self.activation_code_manager = activation_code_manager
        self.email_queue_gateway = email_queue_gateway
        self.frontend_config = frontend_config

    async def __call__(self, current_user_id: UUID) -> None:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        if user.is_active:
            logger.warning(
                f"Resend activation code | [user_id: {current_user_id} "
                "Already active]",
            )
            raise UserAlreadyActiveError("User is already active")

        latest_code = (
            await self.activation_code_gateway.get_latest_code_for_user(
                user_id=user.id,
            )
        )
        retry_after_seconds = seconds_until_code_resend(latest_code)
        if retry_after_seconds > 0:
            logger.warning(
                f"Resend activation code | [user_id: {user.id} Sent recently]",
            )
            raise ActivationCodeRecentlySentError(
                "Activation code was sent recently, try again later",
                retry_after_seconds=retry_after_seconds,
            )

        code = await self.activation_code_manager(user_id=user.id)
        activation_url = build_activation_url(
            frontend_url=self.frontend_config.url,
            code=code,
        )
        email = build_activation_email(
            code,
            activation_url=activation_url,
            locale=user.locale,
        )
        await self.email_queue_gateway.enqueue(
            to_email=user.email.value,
            subject=email.subject,
            body=email.body,
        )
        logger.info(f"Resend activation code | [user_id: {user.id}]")

import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.exceptions import (
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.application.user_activation.activation_code_manager import (
    seconds_until_code_resend,
)
from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)

logger = logging.getLogger(__name__)


@dataclass
class GetResendCooldownResponseDTO:
    retry_after_seconds: int


class GetResendCooldownInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        activation_code_gateway: ActivationCodeGateway,
    ) -> None:
        self.user_gateway = user_gateway
        self.activation_code_gateway = activation_code_gateway

    async def __call__(
        self,
        current_user_id: UUID,
    ) -> GetResendCooldownResponseDTO:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        if user.is_active:
            logger.warning(
                f"Get resend cooldown | [user_id: {current_user_id} "
                "Already active]",
            )
            raise UserAlreadyActiveError("User is already active")

        latest_code = (
            await self.activation_code_gateway.get_latest_code_for_user(
                user_id=user.id,
            )
        )
        return GetResendCooldownResponseDTO(
            retry_after_seconds=seconds_until_code_resend(latest_code),
        )

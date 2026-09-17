import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from timegrip.application.exceptions import (
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.application.user_activation.activation_code_manager import (
    MAX_ACTIVATION_ATTEMPTS,
)
from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)

logger = logging.getLogger(__name__)


@dataclass
class ActivateUserRequestDTO:
    code: str


class ActivateUserInteractor:
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
        activate_dto: ActivateUserRequestDTO,
    ) -> None:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        if user.is_active:
            logger.warning(
                f"Activate user | [user_id: {current_user_id} Already active]",
            )
            raise UserAlreadyActiveError("User is already active")

        activation_code = (
            await self.activation_code_gateway.get_latest_code_for_user(
                user_id=current_user_id,
            )
        )

        if (
            activation_code is None
            or activation_code.used_at is not None
            or activation_code.expires_at < datetime.now(UTC)
            or activation_code.attempts >= MAX_ACTIVATION_ATTEMPTS
        ):
            logger.warning(
                f"Activate user | [user_id: {current_user_id} Invalid code]",
            )
            raise InvalidActivationCodeError("Invalid or expired code")

        if activation_code.code != activate_dto.code:
            await self.activation_code_gateway.increment_attempts(
                id=activation_code.id,
            )
            logger.warning(
                f"Activate user | [user_id: {current_user_id} Wrong code]",
            )
            raise InvalidActivationCodeError("Invalid or expired code")

        await self.activation_code_gateway.mark_code_used(
            id=activation_code.id,
        )
        await self.user_gateway.activate_user(id=current_user_id)
        await self.activation_code_gateway.delete_codes_for_user(
            user_id=current_user_id,
        )
        logger.info(f"Activate user | [user_id: {current_user_id}]")

import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.exceptions import (
    InvalidTimeFormatError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Locale, TimeFormat, User

logger = logging.getLogger(__name__)


@dataclass
class UpdateTimeFormatRequestDTO:
    time_format: str


@dataclass
class UpdateTimeFormatResponseDTO:
    id: UUID
    email: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale


class UpdateTimeFormatInteractor:
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        update_time_format_dto: UpdateTimeFormatRequestDTO,
    ) -> UpdateTimeFormatResponseDTO:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        try:
            time_format = TimeFormat(update_time_format_dto.time_format)
        except ValueError:
            logger.warning(
                f"User with id {current_user_id} tried to set an invalid "
                f"time format [time_format: "
                f"{update_time_format_dto.time_format}]",
            )
            raise InvalidTimeFormatError(
                f"Time format must be one of "
                f"{', '.join(tf.value for tf in TimeFormat)}",
            ) from None

        updated_user = User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            time_format=time_format,
            locale=user.locale,
        )
        user = await self.user_gateway.update_user(user=updated_user)
        return UpdateTimeFormatResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )

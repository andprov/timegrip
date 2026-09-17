import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.exceptions import (
    InvalidLocaleError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Locale, TimeFormat, User

logger = logging.getLogger(__name__)


@dataclass
class UpdateLocaleRequestDTO:
    locale: str


@dataclass
class UpdateLocaleResponseDTO:
    id: UUID
    email: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale


class UpdateLocaleInteractor:
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        update_locale_dto: UpdateLocaleRequestDTO,
    ) -> UpdateLocaleResponseDTO:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        try:
            locale = Locale(update_locale_dto.locale)
        except ValueError:
            logger.warning(
                f"User with id {current_user_id} tried to set an invalid "
                f"locale [locale: {update_locale_dto.locale}]",
            )
            raise InvalidLocaleError(
                f"Locale must be one of "
                f"{', '.join(loc.value for loc in Locale)}",
            ) from None

        updated_user = User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=locale,
        )
        user = await self.user_gateway.update_user(user=updated_user)
        return UpdateLocaleResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )

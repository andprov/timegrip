import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.exceptions import (
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Locale, TimeFormat

logger = logging.getLogger(__name__)


@dataclass
class GetUserResponseDTO:
    id: UUID
    email: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale


class GetUserByIdInteractor:
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def __call__(
        self,
        current_user_id: UUID,
    ) -> GetUserResponseDTO:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        return GetUserResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )

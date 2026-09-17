import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.auth.gateway import RefreshTokenGateway
from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.common.password_policy import (
    validate_password_strength,
)
from timegrip.application.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import User

logger = logging.getLogger(__name__)


@dataclass
class UpdatePasswordRequestDTO:
    current_password: str
    new_password: str


class UpdatePasswordInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_hasher: PasswordHasherGateway,
        refresh_token_gateway: RefreshTokenGateway,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_hasher = password_hasher
        self.refresh_token_gateway = refresh_token_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        update_password_dto: UpdatePasswordRequestDTO,
    ) -> None:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        if not await self.password_hasher.verify_password(
            password=update_password_dto.current_password,
            hashed_password=user.hashed_password,
        ):
            logger.warning(
                f"Update password failed: wrong current password for "
                f"user_id: {current_user_id}",
            )
            raise InvalidCredentialsError(
                "Invalid current password",
                code="invalid_current_password",
            )

        validate_password_strength(password=update_password_dto.new_password)
        hashed_password = await self.password_hasher.hash_password(
            password=update_password_dto.new_password,
        )
        updated_user = User(
            id=user.id,
            email=user.email,
            hashed_password=hashed_password,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )
        await self.refresh_token_gateway.revoke_all_for_user(
            user_id=current_user_id,
        )
        await self.user_gateway.update_user(user=updated_user)
        logger.info(f"Update password | [user_id: {current_user_id}]")

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from timegrip.application.auth.gateway import RefreshTokenGateway
from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.common.password_policy import (
    validate_password_strength,
)
from timegrip.application.exceptions import InvalidPasswordResetCodeError
from timegrip.application.password_reset.gateway import (
    PasswordResetCodeGateway,
)
from timegrip.application.password_reset.password_reset_code_manager import (
    MAX_PASSWORD_RESET_ATTEMPTS,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Email, User

logger = logging.getLogger(__name__)


@dataclass
class ResetPasswordRequestDTO:
    email: str
    code: str
    new_password: str


class ResetPasswordInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_reset_code_gateway: PasswordResetCodeGateway,
        password_hasher: PasswordHasherGateway,
        refresh_token_gateway: RefreshTokenGateway,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_reset_code_gateway = password_reset_code_gateway
        self.password_hasher = password_hasher
        self.refresh_token_gateway = refresh_token_gateway

    async def __call__(self, reset_dto: ResetPasswordRequestDTO) -> None:
        user = await self.user_gateway.get_user_by_email(
            email=Email(reset_dto.email),
        )
        if user is None:
            logger.warning(
                "Reset password | [Unknown email]",
            )
            raise InvalidPasswordResetCodeError("Invalid or expired code")

        reset_code = (
            await self.password_reset_code_gateway.get_latest_code_for_user(
                user_id=user.id,
            )
        )

        if (
            reset_code is None
            or reset_code.used_at is not None
            or reset_code.expires_at < datetime.now(UTC)
            or reset_code.attempts >= MAX_PASSWORD_RESET_ATTEMPTS
        ):
            logger.warning(
                f"Reset password | [user_id: {user.id} Invalid code]",
            )
            raise InvalidPasswordResetCodeError("Invalid or expired code")

        if reset_code.code != reset_dto.code:
            await self.password_reset_code_gateway.increment_attempts(
                id=reset_code.id,
            )
            logger.warning(
                f"Reset password | [user_id: {user.id} Wrong code]",
            )
            raise InvalidPasswordResetCodeError("Invalid or expired code")

        validate_password_strength(password=reset_dto.new_password)
        hashed_password = await self.password_hasher.hash_password(
            password=reset_dto.new_password,
        )
        updated_user = User(
            id=user.id,
            email=user.email,
            hashed_password=hashed_password,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )
        await self.refresh_token_gateway.revoke_all_for_user(user_id=user.id)
        await self.user_gateway.update_user(user=updated_user)
        await self.password_reset_code_gateway.mark_code_used(
            id=reset_code.id,
        )
        await self.password_reset_code_gateway.delete_codes_for_user(
            user_id=user.id,
        )
        logger.info(f"Reset password | [user_id: {user.id}]")

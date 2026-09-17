import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.exceptions import InvalidCredentialsError
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Email

logger = logging.getLogger(__name__)


@dataclass
class AuthRequestDTO:
    email: str
    password: str


class AuthUserInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_hasher: PasswordHasherGateway,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_hasher = password_hasher

    async def __call__(self, auth_dto: AuthRequestDTO) -> UUID:
        email = Email(auth_dto.email)
        user = await self.user_gateway.get_user_by_email(email=email)
        if user is None:
            logger.warning(
                f"Auth failed: user with email: {email} not found",
            )
            raise InvalidCredentialsError("Invalid email or password")

        if not await self.password_hasher.verify_password(
            password=auth_dto.password,
            hashed_password=user.hashed_password,
        ):
            logger.warning(
                f"Auth failed: wrong password for user_id: {user.id}",
            )
            raise InvalidCredentialsError("Invalid email or password")

        return user.id

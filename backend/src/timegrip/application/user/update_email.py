import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Email, Locale, TimeFormat, User

logger = logging.getLogger(__name__)


@dataclass
class UpdateEmailRequestDTO:
    password: str
    new_email: str


@dataclass
class UpdateEmailResponseDTO:
    id: UUID
    email: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale


class UpdateEmailInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_hasher: PasswordHasherGateway,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_hasher = password_hasher

    async def __call__(
        self,
        current_user_id: UUID,
        update_email_dto: UpdateEmailRequestDTO,
    ) -> UpdateEmailResponseDTO:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        if not await self.password_hasher.verify_password(
            password=update_email_dto.password,
            hashed_password=user.hashed_password,
        ):
            logger.warning(
                f"Update email failed: wrong password for "
                f"user_id: {current_user_id}",
            )
            raise InvalidCredentialsError(
                "Invalid password",
                code="invalid_password",
            )

        new_email = Email(update_email_dto.new_email)
        existing_user = await self.user_gateway.get_user_by_email(
            email=new_email,
        )
        if existing_user is not None and existing_user.id != user.id:
            logger.warning(
                f"Attempt to update email to an existing one: {new_email}",
            )
            raise UserAlreadyExistsError(
                f"User with email {new_email} already exists",
            )

        updated_user = User(
            id=user.id,
            email=new_email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )
        user = await self.user_gateway.update_user(user=updated_user)
        return UpdateEmailResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )

import logging
from dataclasses import dataclass
from uuid import UUID

from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.common.password_policy import (
    validate_password_strength,
)
from timegrip.application.exceptions import UserAlreadyExistsError
from timegrip.application.outbox.email_queue_gateway import (
    EmailQueueGateway,
)
from timegrip.application.user.gateway import UserGateway
from timegrip.application.user_activation.activation_code_manager import (
    ActivationCodeManager,
)
from timegrip.application.user_activation.activation_email import (
    build_activation_email,
    build_activation_url,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

logger = logging.getLogger(__name__)


@dataclass
class AddUserRequestDTO:
    email: str
    password: str
    locale: str | None = None


@dataclass
class AddUserResponseDTO:
    id: UUID
    email: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale


class AddUserInteractor:
    def __init__(
        self,
        user_gateway: UserGateway,
        password_hasher: PasswordHasherGateway,
        activation_code_manager: ActivationCodeManager,
        email_queue_gateway: EmailQueueGateway,
        frontend_config: FrontendConfig,
    ) -> None:
        self.user_gateway = user_gateway
        self.password_hasher = password_hasher
        self.activation_code_manager = activation_code_manager
        self.email_queue_gateway = email_queue_gateway
        self.frontend_config = frontend_config

    async def __call__(
        self,
        add_user_dto: AddUserRequestDTO,
    ) -> AddUserResponseDTO:
        user_email = Email(add_user_dto.email)
        existing_user = await self.user_gateway.get_user_by_email(
            email=user_email,
        )
        if existing_user is not None:
            logger.warning(
                f"Attempt to create user with existing email: {user_email}",
            )
            raise UserAlreadyExistsError(
                f"User with email {user_email} already exists",
            )

        validate_password_strength(password=add_user_dto.password)
        hashed_password = await self.password_hasher.hash_password(
            password=add_user_dto.password,
        )
        try:
            locale = Locale(add_user_dto.locale)
        except ValueError:
            locale = Locale.EN
        new_user = User(
            id=None,
            email=user_email,
            hashed_password=hashed_password,
            is_active=False,
            time_format=TimeFormat.TWENTY_FOUR_HOUR,
            locale=locale,
        )
        user = await self.user_gateway.add_user(user=new_user)
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
        return AddUserResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            time_format=user.time_format,
            locale=user.locale,
        )

import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from timegrip.application.password_reset.gateway import (
    PasswordResetCodeGateway,
)
from timegrip.entities.password_reset_code import PasswordResetCode

logger = logging.getLogger(__name__)

PASSWORD_RESET_CODE_TTL_MINUTES = 15
PASSWORD_RESET_CODE_RESEND_COOLDOWN_SECONDS = 60
MAX_PASSWORD_RESET_ATTEMPTS = 5


class PasswordResetCodeManager:
    def __init__(
        self,
        password_reset_code_gateway: PasswordResetCodeGateway,
    ) -> None:
        self.password_reset_code_gateway = password_reset_code_gateway

    async def __call__(self, user_id: UUID) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        reset_code = PasswordResetCode(
            id=None,
            user_id=user_id,
            code=code,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=PASSWORD_RESET_CODE_TTL_MINUTES),
            used_at=None,
            attempts=0,
            created_at=None,
        )
        await self.password_reset_code_gateway.add_code(
            reset_code=reset_code,
        )
        logger.info(f"Issue password reset code | [user_id: {user_id}]")
        return code

import logging
import math
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)
from timegrip.entities.activation_code import ActivationCode

logger = logging.getLogger(__name__)

ACTIVATION_CODE_TTL_HOURS = 24
ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS = 60
MAX_ACTIVATION_ATTEMPTS = 5


def seconds_until_code_resend(activation_code: ActivationCode | None) -> int:
    if activation_code is None or activation_code.created_at is None:
        return 0
    resend_available_at = activation_code.created_at + timedelta(
        seconds=ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS,
    )
    seconds_left = (resend_available_at - datetime.now(UTC)).total_seconds()
    return max(0, math.ceil(seconds_left))


class ActivationCodeManager:
    def __init__(
        self,
        activation_code_gateway: ActivationCodeGateway,
    ) -> None:
        self.activation_code_gateway = activation_code_gateway

    async def __call__(self, user_id: UUID) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        activation_code = ActivationCode(
            id=None,
            user_id=user_id,
            code=code,
            expires_at=datetime.now(UTC)
            + timedelta(hours=ACTIVATION_CODE_TTL_HOURS),
            used_at=None,
            attempts=0,
            created_at=None,
        )
        await self.activation_code_gateway.add_code(
            activation_code=activation_code,
        )
        logger.info(f"Issue activation code | [user_id: {user_id}]")
        return code

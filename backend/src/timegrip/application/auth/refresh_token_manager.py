import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from timegrip.application.auth.gateway import RefreshTokenGateway
from timegrip.application.exceptions import (
    InvalidRefreshTokenError,
    RefreshTokenNotFoundError,
)
from timegrip.entities.refresh_token import (
    RefreshToken,
    RefreshTokenRevokeReason,
)

logger = logging.getLogger(__name__)

REFRESH_TOKEN_TTL_DAYS = 30
REFRESH_TOKEN_GRACE_SECONDS = 30


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


@dataclass
class RotatedTokens:
    user_id: UUID
    refresh_token: str


@dataclass
class ActiveSessionDTO:
    id: int
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None


class RefreshTokenManager:
    def __init__(self, refresh_token_gateway: RefreshTokenGateway) -> None:
        self.refresh_token_gateway = refresh_token_gateway

    async def issue(
        self,
        user_id: UUID,
        user_agent: str | None = None,
        ip_address: str | None = None,
        family_id: UUID | None = None,
    ) -> str:
        raw_token = secrets.token_urlsafe(32)
        await self.refresh_token_gateway.add_token(
            refresh_token=RefreshToken(
                id=None,
                user_id=user_id,
                family_id=family_id,
                token_hash=_hash_token(raw_token),
                expires_at=datetime.now(UTC)
                + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
                revoked_at=None,
                revoke_reason=None,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=None,
            ),
        )
        logger.info(f"Issue refresh token | [user_id: {user_id}]")
        return raw_token

    async def rotate(
        self,
        raw_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RotatedTokens:
        record = await self.refresh_token_gateway.get_token_by_hash(
            token_hash=_hash_token(raw_token),
        )
        if record is None:
            logger.warning("Rotate refresh token | [unknown token]")
            raise InvalidRefreshTokenError("Invalid refresh token")

        now = datetime.now(UTC)

        if record.revoke_reason == RefreshTokenRevokeReason.REVOKED:
            logger.warning(
                "Rotate refresh token | [revoked token, "
                f"user_id: {record.user_id}]",
            )
            raise InvalidRefreshTokenError("Invalid refresh token")

        if record.revoked_at is not None:
            grace_deadline = record.revoked_at + timedelta(
                seconds=REFRESH_TOKEN_GRACE_SECONDS,
            )
            if now <= grace_deadline:
                logger.info(
                    "Rotate refresh token | [benign reuse within grace "
                    f"period, user_id: {record.user_id}]",
                )
                new_token = await self.issue(
                    user_id=record.user_id,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    family_id=record.family_id,
                )
                return RotatedTokens(
                    user_id=record.user_id,
                    refresh_token=new_token,
                )

            logger.warning(
                "Rotate refresh token | [reuse detected, revoking all "
                f"sessions for user_id: {record.user_id}]",
            )
            await self.refresh_token_gateway.revoke_all_for_user(
                user_id=record.user_id,
            )
            raise InvalidRefreshTokenError("Invalid refresh token")

        if record.expires_at < now:
            logger.warning(
                f"Rotate refresh token | [expired, user_id: {record.user_id}]",
            )
            raise InvalidRefreshTokenError("Invalid refresh token")

        await self.refresh_token_gateway.rotate_token(id=record.id)
        new_token = await self.issue(
            user_id=record.user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            family_id=record.family_id,
        )
        return RotatedTokens(user_id=record.user_id, refresh_token=new_token)

    async def revoke(self, raw_token: str) -> None:
        record = await self.refresh_token_gateway.get_token_by_hash(
            token_hash=_hash_token(raw_token),
        )
        if (
            record is None
            or record.revoke_reason == RefreshTokenRevokeReason.REVOKED
        ):
            return

        await self.refresh_token_gateway.revoke_family(
            family_id=record.family_id,
        )
        logger.info(f"Revoke refresh token | [user_id: {record.user_id}]")

    async def list_active_sessions(
        self,
        user_id: UUID,
    ) -> list[ActiveSessionDTO]:
        sessions = await self.refresh_token_gateway.get_active_for_user(
            user_id=user_id,
        )
        return [
            ActiveSessionDTO(
                id=session.id,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
                created_at=session.created_at,
            )
            for session in sessions
        ]

    async def revoke_session(self, user_id: UUID, session_id: int) -> None:
        record = await self.refresh_token_gateway.get_active_token_for_user(
            id=session_id,
            user_id=user_id,
        )
        if record is None:
            raise RefreshTokenNotFoundError("Session not found")

        await self.refresh_token_gateway.revoke_family(
            family_id=record.family_id,
        )

    async def revoke_all(self, user_id: UUID) -> None:
        await self.refresh_token_gateway.revoke_all_for_user(
            user_id=user_id,
        )

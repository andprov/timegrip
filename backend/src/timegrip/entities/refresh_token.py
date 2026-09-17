from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class RefreshTokenRevokeReason(StrEnum):
    ROTATED = "rotated"
    REVOKED = "revoked"


@dataclass(frozen=True)
class RefreshToken:
    id: int | None
    user_id: UUID
    family_id: UUID | None
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    revoke_reason: RefreshTokenRevokeReason | None
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None

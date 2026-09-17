from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ActivationCode:
    id: int | None
    user_id: UUID
    code: str
    expires_at: datetime
    used_at: datetime | None
    attempts: int
    created_at: datetime | None

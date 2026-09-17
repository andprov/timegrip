from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from timegrip.entities.exceptions import InvalidHourlyRateError


class ProjectColor(StrEnum):
    RED = "#F44336"
    ORANGE = "#FF9800"
    YELLOW = "#FFEB3B"
    GREEN = "#4CAF50"
    CYAN = "#00CCCC"
    BLUE = "#2196F3"
    INDIGO = "#3F51B5"
    PURPLE = "#9C27B0"
    PINK = "#E91E63"
    GRAY = "#9E9E9E"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Project:
    id: UUID | None
    name: str
    color: ProjectColor
    hourly_rate: Decimal | None
    round_to_hour: bool
    status: ProjectStatus
    user_id: UUID
    created_at: datetime | None

    def __post_init__(self) -> None:
        if self.hourly_rate is not None and self.hourly_rate < 0:
            raise InvalidHourlyRateError("Hourly rate must not be negative")
        if self.hourly_rate == 0:
            object.__setattr__(self, "hourly_rate", None)
        if self.hourly_rate is None and self.round_to_hour:
            object.__setattr__(self, "round_to_hour", False)

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class TimeFormat(StrEnum):
    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class Locale(StrEnum):
    EN = "en"
    RU = "ru"


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self.value.lower())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class User:
    id: UUID | None
    email: Email
    hashed_password: str
    is_active: bool
    time_format: TimeFormat
    locale: Locale

    def __post_init__(self) -> None:
        if not isinstance(self.email, Email):
            raise TypeError("User email must be an Email")

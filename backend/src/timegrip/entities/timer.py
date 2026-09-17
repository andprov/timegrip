from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from timegrip.entities.exceptions import InvalidTimerRangeError

MIN_TIMER_START = datetime(1900, 1, 1, tzinfo=UTC)


def validate_timer_range(
    start_time: datetime | None,
    end_time: datetime | None,
) -> None:
    for value in (start_time, end_time):
        if value is not None and value.utcoffset() is None:
            raise ValueError("Timer times must be timezone-aware")

    if start_time is not None and start_time < MIN_TIMER_START:
        raise InvalidTimerRangeError(
            message=(
                f"Start time must not be before {MIN_TIMER_START:%Y-%m-%d}"
            ),
            code="start_time_too_early",
        )

    if (
        start_time is not None
        and end_time is not None
        and end_time <= start_time
    ):
        raise InvalidTimerRangeError(
            message="End time must be after start time",
            code="end_time_before_start",
        )


@dataclass(frozen=True)
class Timer:
    id: UUID | None
    start_time: datetime | None
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID

    def __post_init__(self) -> None:
        validate_timer_range(
            start_time=self.start_time,
            end_time=self.end_time,
        )

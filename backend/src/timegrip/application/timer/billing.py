from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

SECONDS_PER_DAY = 86400
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = Decimal(3600)
CENTS = Decimal("0.01")


def _round_to_minute(duration: timedelta) -> timedelta:
    total_seconds = duration.days * SECONDS_PER_DAY + duration.seconds
    whole_minutes, remainder = divmod(total_seconds, SECONDS_PER_MINUTE)
    if remainder >= 30:
        whole_minutes += 1
    return timedelta(seconds=whole_minutes * SECONDS_PER_MINUTE)


def _duration_to_hours(duration: timedelta) -> Decimal:
    total_seconds = duration.days * SECONDS_PER_DAY + duration.seconds
    return Decimal(total_seconds) / SECONDS_PER_HOUR


def calculate_billable_amount(
    duration: timedelta | None,
    hourly_rate: Decimal | None,
    round_to_hour: bool,
) -> Decimal | None:
    if duration is None or hourly_rate is None:
        return None

    hours = _duration_to_hours(_round_to_minute(duration))
    if round_to_hour:
        hours = hours.to_integral_value(rounding=ROUND_HALF_UP)
    return (hours * hourly_rate).quantize(CENTS, rounding=ROUND_HALF_UP)

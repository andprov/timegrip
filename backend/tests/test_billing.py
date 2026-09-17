from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from timegrip.application.timer.billing import calculate_billable_amount


def test_calculate_billable_amount_no_duration():
    result = calculate_billable_amount(
        duration=None,
        hourly_rate=Decimal("50.00"),
        round_to_hour=False,
    )
    assert result is None


def test_calculate_billable_amount_no_hourly_rate():
    result = calculate_billable_amount(
        duration=timedelta(hours=1),
        hourly_rate=None,
        round_to_hour=False,
    )
    assert result is None


def test_calculate_billable_amount_exact_fractional_hours():
    result = calculate_billable_amount(
        duration=timedelta(hours=1, minutes=29),
        hourly_rate=Decimal("50.00"),
        round_to_hour=False,
    )
    assert result == Decimal("74.17")


@pytest.mark.parametrize(
    ("duration", "expected"),
    [
        (timedelta(seconds=29), Decimal("0.00")),
        (timedelta(seconds=29, microseconds=999_999), Decimal("0.00")),
        (timedelta(seconds=30), Decimal("1.00")),
        (timedelta(seconds=89), Decimal("1.00")),
        (timedelta(seconds=90), Decimal("2.00")),
    ],
)
def test_calculate_billable_amount_rounds_seconds_to_nearest_minute(
    duration,
    expected,
):
    result = calculate_billable_amount(
        duration=duration,
        hourly_rate=Decimal("60.00"),
        round_to_hour=False,
    )
    assert result == expected


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (29, Decimal("0.00")),
        (30, Decimal("50.00")),
        (89, Decimal("50.00")),
        (90, Decimal("100.00")),
    ],
)
def test_calculate_billable_amount_round_to_hour(minutes, expected):
    result = calculate_billable_amount(
        duration=timedelta(minutes=minutes),
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
    )
    assert result == expected


def test_calculate_billable_amount_rounds_to_minute_before_hour():
    result = calculate_billable_amount(
        duration=timedelta(hours=1, minutes=29, seconds=30),
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
    )
    assert result == Decimal("100.00")


def test_calculate_billable_amount_counts_whole_days():
    result = calculate_billable_amount(
        duration=timedelta(days=2, hours=3),
        hourly_rate=Decimal("10.00"),
        round_to_hour=False,
    )
    assert result == Decimal("510.00")


def test_calculate_billable_amount_rounds_cents_half_up():
    assert calculate_billable_amount(
        duration=timedelta(minutes=1),
        hourly_rate=Decimal("0.25"),
        round_to_hour=False,
    ) == Decimal("0.00")
    assert calculate_billable_amount(
        duration=timedelta(minutes=3),
        hourly_rate=Decimal("0.10"),
        round_to_hour=False,
    ) == Decimal("0.01")


def test_calculate_billable_amount_max_rate_over_datetime_range_fits_column():
    result = calculate_billable_amount(
        duration=datetime.max - datetime.min,
        hourly_rate=Decimal("99999999.99"),
        round_to_hour=True,
    )
    assert result <= Decimal("9999999999999999.99")

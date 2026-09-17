from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.timer import MIN_TIMER_START, Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


def _make_timer(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "id": None,
        "start_time": now - timedelta(hours=2),
        "end_time": now - timedelta(hours=1),
        "duration": None,
        "hourly_rate": None,
        "round_to_hour": False,
        "billable_amount": None,
        "user_id": TEST_USER_ID,
        "project_id": TEST_PROJECT_ID,
    }
    defaults.update(overrides)
    return Timer(**defaults)


def test_timer_accepts_missing_times_for_timer_being_started():
    timer = _make_timer(start_time=None, end_time=None)
    assert timer.start_time is None
    assert timer.end_time is None


def test_timer_accepts_running_timer_without_end_time():
    start_time = datetime.now(UTC) - timedelta(minutes=5)
    timer = _make_timer(start_time=start_time, end_time=None)
    assert timer.start_time == start_time
    assert timer.end_time is None


def test_timer_accepts_start_time_at_minimum():
    timer = _make_timer(
        start_time=MIN_TIMER_START,
        end_time=MIN_TIMER_START + timedelta(hours=1),
    )
    assert timer.start_time == MIN_TIMER_START


def test_timer_rejects_start_time_before_minimum():
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        _make_timer(
            start_time=MIN_TIMER_START - timedelta(microseconds=1),
            end_time=MIN_TIMER_START + timedelta(hours=1),
        )
    assert exc_info.value.code == "start_time_too_early"


def test_timer_rejects_start_time_before_minimum_in_other_timezone():
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        _make_timer(
            start_time=datetime(
                1900,
                1,
                1,
                0,
                10,
                tzinfo=timezone(timedelta(hours=1)),
            ),
            end_time=None,
        )
    assert exc_info.value.code == "start_time_too_early"


def test_timer_accepts_start_time_after_minimum_in_other_timezone():
    start_time = datetime(
        1900,
        1,
        1,
        0,
        10,
        tzinfo=timezone(-timedelta(hours=1)),
    )
    timer = _make_timer(start_time=start_time, end_time=None)
    assert timer.start_time == start_time


@pytest.mark.parametrize(
    "overrides",
    [
        {"start_time": datetime(2024, 1, 1), "end_time": None},
        {"end_time": datetime(2024, 1, 1)},
    ],
    ids=["naive_start_time", "naive_end_time"],
)
def test_timer_rejects_naive_datetimes(overrides):
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_timer(**overrides)


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(hours=-1)])
def test_timer_rejects_end_time_not_after_start_time(offset):
    start_time = datetime.now(UTC) - timedelta(hours=1)
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        _make_timer(start_time=start_time, end_time=start_time + offset)
    assert exc_info.value.code == "end_time_before_start"

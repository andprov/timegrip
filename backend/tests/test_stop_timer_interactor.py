from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import TimerNotRunningError
from timegrip.application.timer.stop_timer import StopTimerInteractor
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


def _make_running_timer(**overrides):
    defaults = {
        "id": TEST_TIMER_ID,
        "start_time": datetime.now(UTC) - timedelta(hours=1, minutes=29),
        "end_time": None,
        "duration": None,
        "hourly_rate": None,
        "round_to_hour": False,
        "billable_amount": None,
        "user_id": TEST_USER_ID,
        "project_id": TEST_PROJECT_ID,
    }
    defaults.update(overrides)
    return Timer(**defaults)


def _stopped(timer, end_time, billable_amount):
    return replace(
        timer,
        end_time=end_time,
        duration=end_time - timer.start_time,
        billable_amount=billable_amount,
    )


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_running_timer_by_user.return_value = _make_running_timer()
    gateway.stop_timer.side_effect = lambda id, end_time, billable_amount: (
        _stopped(
            timer=gateway.get_running_timer_by_user.return_value,
            end_time=end_time,
            billable_amount=billable_amount,
        )
    )
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def stop_timer_interactor(mock_timer_gateway, mock_permission_gateway):
    return StopTimerInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=mock_permission_gateway,
    )


@pytest.mark.asyncio
async def test_stop_timer_no_running_timer(
    stop_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = None
    with pytest.raises(TimerNotRunningError):
        await stop_timer_interactor(current_user_id=TEST_USER_ID)
    mock_timer_gateway.stop_timer.assert_not_called()


@pytest.mark.asyncio
async def test_stop_timer_computes_exact_billable_amount(
    stop_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = (
        _make_running_timer(
            start_time=datetime.now(UTC) - timedelta(hours=1, minutes=29),
            hourly_rate=Decimal("50.00"),
            round_to_hour=False,
        )
    )
    result = await stop_timer_interactor(current_user_id=TEST_USER_ID)
    assert result.billable_amount == Decimal("74.17")
    assert result.duration >= timedelta(hours=1, minutes=29)


@pytest.mark.asyncio
async def test_stop_timer_rounds_billable_amount_to_hour(
    stop_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = (
        _make_running_timer(
            start_time=datetime.now(UTC) - timedelta(hours=1, minutes=31),
            hourly_rate=Decimal("50.00"),
            round_to_hour=True,
        )
    )
    result = await stop_timer_interactor(current_user_id=TEST_USER_ID)
    assert result.billable_amount == Decimal("100.00")
    assert result.duration >= timedelta(hours=1, minutes=31)


@pytest.mark.asyncio
async def test_stop_timer_stops_running_timer_now(
    stop_timer_interactor,
    mock_timer_gateway,
):
    before = datetime.now(UTC)
    await stop_timer_interactor(current_user_id=TEST_USER_ID)
    after = datetime.now(UTC)
    mock_timer_gateway.get_running_timer_by_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    kwargs = mock_timer_gateway.stop_timer.call_args.kwargs
    assert kwargs["id"] == TEST_TIMER_ID
    assert before <= kwargs["end_time"] <= after
    assert kwargs["end_time"].utcoffset() is not None


@pytest.mark.asyncio
async def test_stop_timer_without_hourly_rate_is_not_billable(
    stop_timer_interactor,
    mock_timer_gateway,
):
    result = await stop_timer_interactor(current_user_id=TEST_USER_ID)
    kwargs = mock_timer_gateway.stop_timer.call_args.kwargs
    assert kwargs["billable_amount"] is None
    assert result.billable_amount is None
    assert result.end_time is not None

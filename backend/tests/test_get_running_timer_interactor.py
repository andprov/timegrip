from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.timer.get_running_timer import (
    GetRunningTimerInteractor,
)
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_running_timer_by_user.return_value = None
    return gateway


@pytest.fixture
def get_running_timer_interactor(mock_timer_gateway):
    return GetRunningTimerInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_running_timer_returns_none_when_nothing_runs(
    get_running_timer_interactor,
    mock_timer_gateway,
):
    result = await get_running_timer_interactor(current_user_id=TEST_USER_ID)
    assert result is None
    mock_timer_gateway.get_running_timer_by_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_get_running_timer_returns_timer(
    get_running_timer_interactor,
    mock_timer_gateway,
):
    start_time = datetime.now(UTC) - timedelta(minutes=5)
    mock_timer_gateway.get_running_timer_by_user.return_value = Timer(
        id=TEST_TIMER_ID,
        start_time=start_time,
        end_time=None,
        duration=None,
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
        billable_amount=None,
        user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    result = await get_running_timer_interactor(current_user_id=TEST_USER_ID)
    assert result.id == TEST_TIMER_ID
    assert result.start_time == start_time
    assert result.hourly_rate == Decimal("50.00")
    assert result.round_to_hour is True
    assert result.user_id == TEST_USER_ID
    assert result.project_id == TEST_PROJECT_ID

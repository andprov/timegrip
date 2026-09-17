from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    TimerNotFoundError,
    TimerRunningError,
)
from timegrip.application.timer.bulk_delete_timer import (
    BulkDeleteTimerInteractor,
)
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID_1 = UUID("00000000-0000-0000-0000-000000000099")
TEST_TIMER_ID_2 = UUID("00000000-0000-0000-0000-000000000098")


def _make_timer(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "id": TEST_TIMER_ID_1,
        "start_time": now - timedelta(hours=2),
        "end_time": now - timedelta(hours=1),
        "duration": timedelta(hours=1),
        "hourly_rate": None,
        "round_to_hour": False,
        "billable_amount": None,
        "user_id": TEST_USER_ID,
        "project_id": TEST_PROJECT_ID,
    }
    defaults.update(overrides)
    return Timer(**defaults)


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_timers_by_ids.return_value = [
        _make_timer(id=TEST_TIMER_ID_1),
        _make_timer(id=TEST_TIMER_ID_2),
    ]
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def bulk_delete_timer_interactor(mock_timer_gateway, mock_permission_gateway):
    return BulkDeleteTimerInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=mock_permission_gateway,
    )


@pytest.mark.asyncio
async def test_bulk_delete_timer_success(
    bulk_delete_timer_interactor,
    mock_timer_gateway,
):
    await bulk_delete_timer_interactor(
        current_user_id=TEST_USER_ID,
        timer_ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
    )
    mock_timer_gateway.get_timers_by_ids.assert_called_once_with(
        ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
    )
    mock_timer_gateway.delete_timers.assert_called_once_with(
        ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
    )


@pytest.mark.asyncio
async def test_bulk_delete_timer_not_found(
    bulk_delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timers_by_ids.return_value = [
        _make_timer(id=TEST_TIMER_ID_1),
    ]
    with pytest.raises(TimerNotFoundError):
        await bulk_delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
        )
    mock_timer_gateway.delete_timers.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_delete_timer_not_owned(
    bulk_delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timers_by_ids.return_value = [
        _make_timer(id=TEST_TIMER_ID_1),
        _make_timer(id=TEST_TIMER_ID_2, user_id=TEST_OTHER_USER_ID),
    ]
    with pytest.raises(TimerNotFoundError):
        await bulk_delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
        )
    mock_timer_gateway.delete_timers.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_delete_timer_running(
    bulk_delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timers_by_ids.return_value = [
        _make_timer(id=TEST_TIMER_ID_1),
        _make_timer(id=TEST_TIMER_ID_2, end_time=None, duration=None),
    ]
    with pytest.raises(TimerRunningError):
        await bulk_delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_ids=[TEST_TIMER_ID_1, TEST_TIMER_ID_2],
        )
    mock_timer_gateway.delete_timers.assert_not_called()

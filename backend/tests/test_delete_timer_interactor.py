from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    TimerNotFoundError,
    TimerRunningError,
)
from timegrip.application.timer.delete_timer import DeleteTimerInteractor
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


def _make_timer(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "id": TEST_TIMER_ID,
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
    gateway.get_timer_by_id.return_value = _make_timer()
    return gateway


@pytest.fixture
def delete_timer_interactor(mock_timer_gateway):
    return DeleteTimerInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_delete_timer_success(
    delete_timer_interactor,
    mock_timer_gateway,
):
    await delete_timer_interactor(
        current_user_id=TEST_USER_ID,
        timer_id=TEST_TIMER_ID,
    )
    mock_timer_gateway.get_timer_by_id.assert_called_once_with(
        id=TEST_TIMER_ID,
    )
    mock_timer_gateway.delete_timer.assert_called_once_with(id=TEST_TIMER_ID)


@pytest.mark.asyncio
async def test_delete_timer_not_found(
    delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = None
    with pytest.raises(TimerNotFoundError):
        await delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_id=TEST_TIMER_ID,
        )
    mock_timer_gateway.delete_timer.assert_not_called()


@pytest.mark.asyncio
async def test_delete_timer_not_owned(
    delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        user_id=TEST_OTHER_USER_ID,
    )
    with pytest.raises(TimerNotFoundError):
        await delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_id=TEST_TIMER_ID,
        )
    mock_timer_gateway.delete_timer.assert_not_called()


@pytest.mark.asyncio
async def test_delete_timer_running(
    delete_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        end_time=None,
        duration=None,
    )
    with pytest.raises(TimerRunningError):
        await delete_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_id=TEST_TIMER_ID,
        )
    mock_timer_gateway.delete_timer.assert_not_called()

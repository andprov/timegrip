from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import TimerNotFoundError
from timegrip.application.timer.get_timer import GetTimerByIdInteractor
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
        "hourly_rate": Decimal("50.00"),
        "round_to_hour": True,
        "billable_amount": Decimal("50.00"),
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
def get_timer_interactor(mock_timer_gateway):
    return GetTimerByIdInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_timer_success(get_timer_interactor, mock_timer_gateway):
    timer = mock_timer_gateway.get_timer_by_id.return_value
    result = await get_timer_interactor(
        current_user_id=TEST_USER_ID,
        timer_id=TEST_TIMER_ID,
    )
    mock_timer_gateway.get_timer_by_id.assert_called_once_with(
        id=TEST_TIMER_ID,
    )
    assert result.id == TEST_TIMER_ID
    assert result.start_time == timer.start_time
    assert result.end_time == timer.end_time
    assert result.duration == timedelta(hours=1)
    assert result.hourly_rate == Decimal("50.00")
    assert result.round_to_hour is True
    assert result.billable_amount == Decimal("50.00")
    assert result.user_id == TEST_USER_ID
    assert result.project_id == TEST_PROJECT_ID


@pytest.mark.asyncio
async def test_get_timer_not_found(get_timer_interactor, mock_timer_gateway):
    mock_timer_gateway.get_timer_by_id.return_value = None
    with pytest.raises(TimerNotFoundError):
        await get_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_id=TEST_TIMER_ID,
        )


@pytest.mark.asyncio
async def test_get_timer_not_owned_is_reported_as_not_found(
    get_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        user_id=TEST_OTHER_USER_ID,
    )
    with pytest.raises(TimerNotFoundError) as exc_info:
        await get_timer_interactor(
            current_user_id=TEST_USER_ID,
            timer_id=TEST_TIMER_ID,
        )
    assert str(exc_info.value) == f"Timer with id {TEST_TIMER_ID} not found"

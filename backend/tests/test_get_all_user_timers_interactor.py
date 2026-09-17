from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.timer.get_all_user_timers import (
    GetAllUserTimersInteractor,
)
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    now = datetime.now(UTC)
    gateway.get_all_user_timers.return_value = [
        Timer(
            id=TEST_TIMER_ID,
            start_time=now - timedelta(hours=1),
            end_time=now,
            duration=timedelta(hours=1),
            hourly_rate=None,
            round_to_hour=False,
            billable_amount=None,
            user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        ),
    ]
    gateway.count_user_timers.return_value = 1
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def get_all_user_timers_interactor(
    mock_timer_gateway,
    mock_permission_gateway,
):
    return GetAllUserTimersInteractor(
        timer_gateway=mock_timer_gateway,
        permission_gateway=mock_permission_gateway,
    )


@pytest.mark.asyncio
async def test_get_all_user_timers_returns_total(
    get_all_user_timers_interactor,
    mock_timer_gateway,
):
    result = await get_all_user_timers_interactor(
        current_user_id=TEST_USER_ID,
        page=1,
        page_size=10,
    )
    timer = mock_timer_gateway.get_all_user_timers.return_value[0]
    assert result.total == 1
    assert len(result.items) == 1
    item = result.items[0]
    assert item.id == TEST_TIMER_ID
    assert item.start_time == timer.start_time
    assert item.end_time == timer.end_time
    assert item.duration == timer.duration
    assert item.hourly_rate == timer.hourly_rate
    assert item.round_to_hour == timer.round_to_hour
    assert item.billable_amount == timer.billable_amount
    assert item.user_id == TEST_USER_ID
    assert item.project_id == TEST_PROJECT_ID
    mock_timer_gateway.count_user_timers.assert_called_once_with(
        user_id=TEST_USER_ID,
        project_ids=None,
        date_from=None,
        date_to=None,
        billable=None,
        include_archived_projects=False,
    )


@pytest.mark.asyncio
async def test_get_all_user_timers_total_independent_of_page_slice(
    get_all_user_timers_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.count_user_timers.return_value = 42
    result = await get_all_user_timers_interactor(
        current_user_id=TEST_USER_ID,
        page=2,
        page_size=10,
    )
    assert result.total == 42
    assert len(result.items) == 1
    _, kwargs = mock_timer_gateway.get_all_user_timers.call_args
    assert kwargs["offset"] == 10
    assert kwargs["limit"] == 10


@pytest.mark.asyncio
async def test_get_all_user_timers_passes_filters_through(
    get_all_user_timers_interactor,
    mock_timer_gateway,
):
    date_from = datetime.now(UTC) - timedelta(days=7)
    date_to = datetime.now(UTC)
    await get_all_user_timers_interactor(
        current_user_id=TEST_USER_ID,
        page=1,
        page_size=10,
        project_ids=[TEST_PROJECT_ID],
        date_from=date_from,
        date_to=date_to,
        billable=True,
        include_archived_projects=True,
    )
    mock_timer_gateway.get_all_user_timers.assert_called_once_with(
        user_id=TEST_USER_ID,
        offset=0,
        limit=10,
        project_ids=[TEST_PROJECT_ID],
        date_from=date_from,
        date_to=date_to,
        billable=True,
        include_archived_projects=True,
    )
    mock_timer_gateway.count_user_timers.assert_called_once_with(
        user_id=TEST_USER_ID,
        project_ids=[TEST_PROJECT_ID],
        date_from=date_from,
        date_to=date_to,
        billable=True,
        include_archived_projects=True,
    )

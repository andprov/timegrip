from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerAlreadyRunningError,
    TimerOverlapError,
)
from timegrip.application.timer.start_timer import (
    StartTimerInteractor,
    StartTimerRequestDTO,
)
from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.project import Project, ProjectColor, ProjectStatus
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_OTHER_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000011")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_running_timer_by_user.return_value = None
    gateway.has_overlapping_timer.return_value = False
    gateway.add_timer.return_value = Timer(
        id=TEST_TIMER_ID,
        start_time=datetime.now(UTC),
        end_time=None,
        duration=None,
        hourly_rate=None,
        round_to_hour=False,
        billable_amount=None,
        user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    return gateway


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=None,
        round_to_hour=False,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def start_timer_interactor(
    mock_timer_gateway,
    mock_project_gateway,
    mock_permission_gateway,
):
    return StartTimerInteractor(
        timer_gateway=mock_timer_gateway,
        project_gateway=mock_project_gateway,
        permission_gateway=mock_permission_gateway,
    )


def _make_dto(**overrides):
    defaults = {"project_id": TEST_PROJECT_ID, "user_id": TEST_USER_ID}
    defaults.update(overrides)
    return StartTimerRequestDTO(**defaults)


@pytest.mark.asyncio
async def test_start_timer_success(
    start_timer_interactor,
    mock_timer_gateway,
):
    start_timer_dto = _make_dto()
    result = await start_timer_interactor(start_timer_dto=start_timer_dto)
    assert result.id == TEST_TIMER_ID
    assert result.project_id == TEST_PROJECT_ID
    mock_timer_gateway.add_timer.assert_called_once()


@pytest.mark.asyncio
async def test_start_timer_project_not_found(
    start_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    start_timer_dto = _make_dto()
    with pytest.raises(ProjectNotFoundError):
        await start_timer_interactor(start_timer_dto=start_timer_dto)
    mock_timer_gateway.add_timer.assert_not_called()


@pytest.mark.asyncio
async def test_start_timer_project_not_owned(
    start_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=None,
        round_to_hour=False,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_OTHER_USER_ID,
        created_at=datetime.now(UTC),
    )
    start_timer_dto = _make_dto()
    with pytest.raises(ProjectNotFoundError):
        await start_timer_interactor(start_timer_dto=start_timer_dto)
    mock_timer_gateway.add_timer.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_project_id",
    [TEST_PROJECT_ID, TEST_OTHER_PROJECT_ID],
    ids=["same_project", "other_project"],
)
async def test_start_timer_already_running(
    start_timer_interactor,
    mock_timer_gateway,
    running_project_id,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = Timer(
        id=UUID("00000000-0000-0000-0000-000000000098"),
        start_time=datetime.now(UTC),
        end_time=None,
        duration=None,
        hourly_rate=None,
        round_to_hour=False,
        billable_amount=None,
        user_id=TEST_USER_ID,
        project_id=running_project_id,
    )
    start_timer_dto = _make_dto()
    with pytest.raises(TimerAlreadyRunningError):
        await start_timer_interactor(start_timer_dto=start_timer_dto)
    mock_timer_gateway.get_running_timer_by_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_timer_gateway.add_timer.assert_not_called()


@pytest.mark.asyncio
async def test_start_timer_archived_project(
    start_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=None,
        round_to_hour=False,
        status=ProjectStatus.ARCHIVED,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    start_timer_dto = _make_dto()
    with pytest.raises(ProjectArchivedError):
        await start_timer_interactor(start_timer_dto=start_timer_dto)
    mock_timer_gateway.get_running_timer_by_user.assert_not_called()
    mock_timer_gateway.add_timer.assert_not_called()


@pytest.mark.asyncio
async def test_start_timer_snapshots_project_billing_settings(
    start_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    start_timer_dto = _make_dto()
    await start_timer_interactor(start_timer_dto=start_timer_dto)
    timer = mock_timer_gateway.add_timer.call_args.kwargs["timer"]
    assert timer.id is None
    assert timer.start_time is None
    assert timer.end_time is None
    assert timer.billable_amount is None
    assert timer.hourly_rate == Decimal("50.00")
    assert timer.round_to_hour is True
    assert timer.user_id == TEST_USER_ID
    assert timer.project_id == TEST_PROJECT_ID


@pytest.mark.asyncio
async def test_start_timer_without_start_time_starts_now(
    start_timer_interactor,
    mock_timer_gateway,
):
    await start_timer_interactor(start_timer_dto=_make_dto())
    timer = mock_timer_gateway.add_timer.call_args.kwargs["timer"]
    assert timer.start_time is None
    mock_timer_gateway.has_overlapping_timer.assert_not_called()


@pytest.mark.asyncio
async def test_start_timer_with_past_start_time(
    start_timer_interactor,
    mock_timer_gateway,
):
    started = datetime.now(UTC) - timedelta(minutes=25)
    await start_timer_interactor(
        start_timer_dto=_make_dto(start_time=started),
    )
    timer = mock_timer_gateway.add_timer.call_args.kwargs["timer"]
    assert timer.start_time == started
    assert timer.end_time is None
    mock_timer_gateway.has_overlapping_timer.assert_called_once_with(
        user_id=TEST_USER_ID,
        start_time=started,
        end_time=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start_time", "code"),
    [
        (datetime.now(UTC) + timedelta(hours=1), "start_time_in_future"),
        (datetime(1899, 12, 31, tzinfo=UTC), "start_time_too_early"),
    ],
    ids=["future", "too_early"],
)
async def test_start_timer_rejects_impossible_start_time(
    start_timer_interactor,
    mock_timer_gateway,
    start_time,
    code,
):
    with pytest.raises(InvalidTimerRangeError) as error:
        await start_timer_interactor(
            start_timer_dto=_make_dto(start_time=start_time),
        )
    assert error.value.code == code
    mock_timer_gateway.add_timer.assert_not_called()


@pytest.mark.asyncio
async def test_start_timer_rejects_start_inside_existing_entry(
    start_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.has_overlapping_timer.return_value = True
    with pytest.raises(TimerOverlapError):
        await start_timer_interactor(
            start_timer_dto=_make_dto(
                start_time=datetime.now(UTC) - timedelta(minutes=25),
            ),
        )
    mock_timer_gateway.add_timer.assert_not_called()

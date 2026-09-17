from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerNotFoundError,
    TimerOverlapError,
    TimerRunningError,
)
from timegrip.application.timer.update_timer import (
    UpdateTimerInteractor,
    UpdateTimerRequestDTO,
)
from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.project import Project, ProjectColor, ProjectStatus
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_OTHER_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000011")
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
    gateway.has_overlapping_timer.return_value = False
    return gateway


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_project_by_id.return_value = Project(
        id=TEST_OTHER_PROJECT_ID,
        name="Other Project",
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
def update_timer_interactor(
    mock_timer_gateway,
    mock_project_gateway,
    mock_permission_gateway,
):
    return UpdateTimerInteractor(
        timer_gateway=mock_timer_gateway,
        project_gateway=mock_project_gateway,
        permission_gateway=mock_permission_gateway,
    )


def _make_dto(**overrides):
    defaults = {"id": TEST_TIMER_ID}
    defaults.update(overrides)
    return UpdateTimerRequestDTO(**defaults)


@pytest.mark.asyncio
async def test_update_timer_success(
    update_timer_interactor,
    mock_timer_gateway,
):
    existing = _make_timer()
    new_start_time = existing.start_time + timedelta(minutes=10)
    update_timer_dto = _make_dto(start_time=new_start_time)
    mock_timer_gateway.update_timer.return_value = _make_timer(
        start_time=new_start_time,
    )
    result = await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    assert result.start_time == new_start_time
    mock_timer_gateway.update_timer.assert_called_once()


@pytest.mark.asyncio
async def test_update_timer_not_found(
    update_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = None
    update_timer_dto = _make_dto()
    with pytest.raises(TimerNotFoundError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_not_owned(
    update_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        user_id=TEST_OTHER_USER_ID,
    )
    update_timer_dto = _make_dto()
    with pytest.raises(TimerNotFoundError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_running_rejected(
    update_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        end_time=None,
        duration=None,
    )
    update_timer_dto = _make_dto()
    with pytest.raises(TimerRunningError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_end_before_start(
    update_timer_interactor,
    mock_timer_gateway,
):
    existing = _make_timer()
    update_timer_dto = _make_dto(
        end_time=existing.start_time - timedelta(minutes=1),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    assert exc_info.value.code == "end_time_before_start"
    mock_timer_gateway.has_overlapping_timer.assert_not_called()
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_start_in_future(
    update_timer_interactor,
    mock_timer_gateway,
):
    update_timer_dto = _make_dto(
        start_time=datetime.now(UTC) + timedelta(hours=1),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    assert exc_info.value.code == "start_time_in_future"
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_end_in_future(
    update_timer_interactor,
    mock_timer_gateway,
):
    update_timer_dto = _make_dto(
        end_time=datetime.now(UTC) + timedelta(hours=1),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    assert exc_info.value.code == "end_time_in_future"
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_project_not_found(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    update_timer_dto = _make_dto(project_id=TEST_OTHER_PROJECT_ID)
    with pytest.raises(ProjectNotFoundError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_project_not_owned(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_OTHER_PROJECT_ID,
        name="Other Project",
        color=ProjectColor.GRAY,
        hourly_rate=None,
        round_to_hour=False,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_OTHER_USER_ID,
        created_at=datetime.now(UTC),
    )
    update_timer_dto = _make_dto(project_id=TEST_OTHER_PROJECT_ID)
    with pytest.raises(ProjectNotFoundError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_reassign_to_archived_project(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_OTHER_PROJECT_ID,
        name="Other Project",
        color=ProjectColor.GRAY,
        hourly_rate=None,
        round_to_hour=False,
        status=ProjectStatus.ARCHIVED,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    update_timer_dto = _make_dto(project_id=TEST_OTHER_PROJECT_ID)
    with pytest.raises(ProjectArchivedError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.has_overlapping_timer.assert_not_called()
    mock_timer_gateway.update_timer.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_overlap(
    update_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.has_overlapping_timer.return_value = True
    update_timer_dto = _make_dto()
    with pytest.raises(TimerOverlapError):
        await update_timer_interactor(
            current_user_id=TEST_USER_ID,
            update_timer_dto=update_timer_dto,
        )
    mock_timer_gateway.update_timer.assert_not_called()
    mock_timer_gateway.has_overlapping_timer.assert_called_once()
    _, kwargs = mock_timer_gateway.has_overlapping_timer.call_args
    assert kwargs["exclude_id"] == TEST_TIMER_ID


@pytest.mark.asyncio
async def test_update_timer_computes_billable_amount(
    update_timer_interactor,
    mock_timer_gateway,
):
    existing = _make_timer(hourly_rate=Decimal("50.00"))
    mock_timer_gateway.get_timer_by_id.return_value = existing
    update_timer_dto = _make_dto(
        start_time=existing.end_time - timedelta(hours=1, minutes=30),
    )
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    _, kwargs = mock_timer_gateway.update_timer.call_args
    assert kwargs["timer"].billable_amount == Decimal("75.00")


@pytest.mark.asyncio
async def test_update_timer_rounds_billable_amount_to_hour(
    update_timer_interactor,
    mock_timer_gateway,
):
    existing = _make_timer(hourly_rate=Decimal("50.00"), round_to_hour=True)
    mock_timer_gateway.get_timer_by_id.return_value = existing
    update_timer_dto = _make_dto(
        start_time=existing.end_time - timedelta(hours=1, minutes=31),
    )
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    _, kwargs = mock_timer_gateway.update_timer.call_args
    assert kwargs["timer"].billable_amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_update_timer_resnapshots_hourly_rate_on_project_change(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_OTHER_PROJECT_ID,
        name="Other Project",
        color=ProjectColor.GRAY,
        hourly_rate=Decimal("60.00"),
        round_to_hour=True,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    update_timer_dto = _make_dto(project_id=TEST_OTHER_PROJECT_ID)
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    timer = mock_timer_gateway.update_timer.call_args.kwargs["timer"]
    assert timer.project_id == TEST_OTHER_PROJECT_ID
    assert timer.hourly_rate == Decimal("60.00")
    assert timer.round_to_hour is True
    assert timer.billable_amount == Decimal("60.00")


@pytest.mark.asyncio
async def test_update_timer_reassign_to_non_billable_project(
    update_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
        billable_amount=Decimal("50.00"),
    )
    update_timer_dto = _make_dto(project_id=TEST_OTHER_PROJECT_ID)
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    timer = mock_timer_gateway.update_timer.call_args.kwargs["timer"]
    assert timer.project_id == TEST_OTHER_PROJECT_ID
    assert timer.hourly_rate is None
    assert timer.round_to_hour is False
    assert timer.billable_amount is None


@pytest.mark.asyncio
async def test_update_timer_keeps_omitted_fields(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    existing = _make_timer()
    mock_timer_gateway.get_timer_by_id.return_value = existing
    new_end_time = existing.end_time + timedelta(minutes=30)
    update_timer_dto = _make_dto(end_time=new_end_time)
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    timer = mock_timer_gateway.update_timer.call_args.kwargs["timer"]
    assert timer.id == TEST_TIMER_ID
    assert timer.start_time == existing.start_time
    assert timer.end_time == new_end_time
    assert timer.project_id == TEST_PROJECT_ID
    assert timer.user_id == TEST_USER_ID
    mock_timer_gateway.has_overlapping_timer.assert_called_once_with(
        user_id=TEST_USER_ID,
        start_time=existing.start_time,
        end_time=new_end_time,
        exclude_id=TEST_TIMER_ID,
    )
    mock_project_gateway.get_project_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_update_timer_same_project_id_does_not_refetch_project(
    update_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_timer_gateway.get_timer_by_id.return_value = _make_timer(
        hourly_rate=Decimal("30.00"),
    )
    update_timer_dto = _make_dto(project_id=TEST_PROJECT_ID)
    await update_timer_interactor(
        current_user_id=TEST_USER_ID,
        update_timer_dto=update_timer_dto,
    )
    mock_project_gateway.get_project_by_id.assert_not_called()
    timer = mock_timer_gateway.update_timer.call_args.kwargs["timer"]
    assert timer.hourly_rate == Decimal("30.00")

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerOverlapError,
)
from timegrip.application.timer.add_manual_timer import (
    AddManualTimerInteractor,
    AddManualTimerRequestDTO,
)
from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.project import Project, ProjectColor, ProjectStatus
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.has_overlapping_timer.return_value = False
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
def add_manual_timer_interactor(
    mock_timer_gateway,
    mock_project_gateway,
    mock_permission_gateway,
):
    return AddManualTimerInteractor(
        timer_gateway=mock_timer_gateway,
        project_gateway=mock_project_gateway,
        permission_gateway=mock_permission_gateway,
    )


def _make_dto(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "project_id": TEST_PROJECT_ID,
        "user_id": TEST_USER_ID,
        "start_time": now - timedelta(hours=2),
        "end_time": now - timedelta(hours=1),
    }
    defaults.update(overrides)
    return AddManualTimerRequestDTO(**defaults)


@pytest.mark.asyncio
async def test_add_manual_timer_success(
    add_manual_timer_interactor,
    mock_timer_gateway,
):
    add_timer_dto = _make_dto()
    mock_timer_gateway.add_manual_timer.return_value = Timer(
        id=UUID("00000000-0000-0000-0000-000000000099"),
        start_time=add_timer_dto.start_time,
        end_time=add_timer_dto.end_time,
        duration=add_timer_dto.end_time - add_timer_dto.start_time,
        hourly_rate=None,
        round_to_hour=False,
        billable_amount=None,
        user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    result = await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    assert result.end_time == add_timer_dto.end_time
    timer = mock_timer_gateway.add_manual_timer.call_args.kwargs["timer"]
    assert timer.hourly_rate is None
    assert timer.billable_amount is None


@pytest.mark.asyncio
async def test_add_manual_timer_start_in_future(
    add_manual_timer_interactor,
    mock_timer_gateway,
):
    now = datetime.now(UTC)
    add_timer_dto = _make_dto(
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    assert exc_info.value.code == "start_time_in_future"
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_end_in_future(
    add_manual_timer_interactor,
    mock_timer_gateway,
):
    now = datetime.now(UTC)
    add_timer_dto = _make_dto(
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    assert exc_info.value.code == "end_time_in_future"
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_end_before_start(
    add_manual_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    now = datetime.now(UTC)
    add_timer_dto = _make_dto(
        start_time=now - timedelta(hours=1),
        end_time=now - timedelta(hours=2),
    )
    with pytest.raises(InvalidTimerRangeError) as exc_info:
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    assert exc_info.value.code == "end_time_before_start"
    mock_project_gateway.get_project_by_id.assert_not_called()
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_project_not_found(
    add_manual_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    add_timer_dto = _make_dto()
    with pytest.raises(ProjectNotFoundError):
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_project_not_owned(
    add_manual_timer_interactor,
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
    add_timer_dto = _make_dto()
    with pytest.raises(ProjectNotFoundError):
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_archived_project(
    add_manual_timer_interactor,
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
    add_timer_dto = _make_dto()
    with pytest.raises(ProjectArchivedError):
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    mock_timer_gateway.has_overlapping_timer.assert_not_called()
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_computes_billable_amount(
    add_manual_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=Decimal("50.00"),
        round_to_hour=False,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    now = datetime.now(UTC)
    add_timer_dto = _make_dto(
        start_time=now - timedelta(hours=1, minutes=30),
        end_time=now,
    )
    await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    _, kwargs = mock_timer_gateway.add_manual_timer.call_args
    assert kwargs["timer"].billable_amount == Decimal("75.00")


@pytest.mark.asyncio
async def test_add_manual_timer_rounds_billable_amount_to_hour(
    add_manual_timer_interactor,
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
    now = datetime.now(UTC)
    add_timer_dto = _make_dto(
        start_time=now - timedelta(hours=1, minutes=31),
        end_time=now,
    )
    await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    _, kwargs = mock_timer_gateway.add_manual_timer.call_args
    assert kwargs["timer"].billable_amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_add_manual_timer_overlap(
    add_manual_timer_interactor,
    mock_timer_gateway,
):
    mock_timer_gateway.has_overlapping_timer.return_value = True
    add_timer_dto = _make_dto()
    with pytest.raises(TimerOverlapError):
        await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    mock_timer_gateway.has_overlapping_timer.assert_called_once_with(
        user_id=TEST_USER_ID,
        start_time=add_timer_dto.start_time,
        end_time=add_timer_dto.end_time,
    )
    mock_timer_gateway.add_manual_timer.assert_not_called()


@pytest.mark.asyncio
async def test_add_manual_timer_snapshots_project_billing_settings(
    add_manual_timer_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = Project(
        id=TEST_PROJECT_ID,
        name="Website Redesign",
        color=ProjectColor.GRAY,
        hourly_rate=Decimal("42.50"),
        round_to_hour=True,
        status=ProjectStatus.ACTIVE,
        user_id=TEST_USER_ID,
        created_at=datetime.now(UTC),
    )
    add_timer_dto = _make_dto()
    await add_manual_timer_interactor(add_timer_dto=add_timer_dto)
    timer = mock_timer_gateway.add_manual_timer.call_args.kwargs["timer"]
    assert timer.id is None
    assert timer.start_time == add_timer_dto.start_time
    assert timer.end_time == add_timer_dto.end_time
    assert timer.hourly_rate == Decimal("42.50")
    assert timer.round_to_hour is True
    assert timer.billable_amount == Decimal("42.50")
    assert timer.user_id == TEST_USER_ID
    assert timer.project_id == TEST_PROJECT_ID

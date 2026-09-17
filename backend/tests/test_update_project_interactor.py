from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidProjectColorError,
    InvalidProjectStatusError,
    ProjectHasRunningTimerError,
    ProjectNotFoundError,
)
from timegrip.application.project.update_project import (
    UpdateProjectInteractor,
    UpdateProjectRequestDTO,
)
from timegrip.entities.exceptions import InvalidHourlyRateError
from timegrip.entities.project import Project, ProjectColor, ProjectStatus
from timegrip.entities.timer import Timer

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_OTHER_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000011")


def _make_project(**overrides):
    defaults = {
        "id": TEST_PROJECT_ID,
        "name": "Website Redesign",
        "color": ProjectColor.GRAY,
        "hourly_rate": None,
        "round_to_hour": False,
        "status": ProjectStatus.ACTIVE,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Project(**defaults)


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_project_by_id.return_value = _make_project()
    gateway.update_project.side_effect = lambda project: project
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_running_timer_by_user.return_value = None
    return gateway


@pytest.fixture
def update_project_interactor(
    mock_project_gateway,
    mock_timer_gateway,
    mock_permission_gateway,
):
    return UpdateProjectInteractor(
        project_gateway=mock_project_gateway,
        timer_gateway=mock_timer_gateway,
        permission_gateway=mock_permission_gateway,
    )


def _make_running_timer(project_id):
    return Timer(
        id=UUID("00000000-0000-0000-0000-000000000099"),
        start_time=datetime.now(UTC) - timedelta(minutes=5),
        end_time=None,
        duration=None,
        hourly_rate=None,
        round_to_hour=False,
        billable_amount=None,
        user_id=TEST_USER_ID,
        project_id=project_id,
    )


@pytest.mark.asyncio
async def test_update_project_archive_rejected_while_its_timer_runs(
    update_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = (
        _make_running_timer(project_id=TEST_PROJECT_ID)
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        status=ProjectStatus.ARCHIVED.value,
    )
    with pytest.raises(ProjectHasRunningTimerError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )
    mock_project_gateway.update_project.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_timer",
    [None, _make_running_timer(project_id=TEST_OTHER_PROJECT_ID)],
    ids=["no_running_timer", "other_project_timer_runs"],
)
async def test_update_project_archive_allowed(
    update_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
    running_timer,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = running_timer
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        status=ProjectStatus.ARCHIVED.value,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.status == ProjectStatus.ARCHIVED
    mock_timer_gateway.get_running_timer_by_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_project_gateway.update_project.assert_called_once()


@pytest.mark.asyncio
async def test_update_project_skips_timer_check_when_already_archived(
    update_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        status=ProjectStatus.ARCHIVED,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="Renamed",
        status=ProjectStatus.ARCHIVED.value,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.name == "Renamed"
    mock_timer_gateway.get_running_timer_by_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_project_set_color(
    update_project_interactor,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        color=ProjectColor.GREEN.value,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.color == ProjectColor.GREEN


@pytest.mark.asyncio
async def test_update_project_keeps_existing_color_when_omitted(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        color=ProjectColor.RED,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="New name",
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.color == ProjectColor.RED


@pytest.mark.asyncio
async def test_update_project_invalid_color(
    update_project_interactor,
    mock_project_gateway,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        color="not-a-color",
    )
    with pytest.raises(InvalidProjectColorError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )
    mock_project_gateway.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_update_project_not_found(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    update_project_dto = UpdateProjectRequestDTO(id=TEST_PROJECT_ID)
    with pytest.raises(ProjectNotFoundError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )


@pytest.mark.asyncio
async def test_update_project_set_hourly_rate(
    update_project_interactor,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        hourly_rate=Decimal("75.00"),
        hourly_rate_set=True,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.hourly_rate == Decimal("75.00")


@pytest.mark.asyncio
async def test_update_project_keeps_existing_hourly_rate_when_omitted(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        hourly_rate=Decimal("40.00"),
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="New name",
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.hourly_rate == Decimal("40.00")


@pytest.mark.asyncio
async def test_update_project_set_round_to_hour(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        hourly_rate=Decimal("40.00"),
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        round_to_hour=True,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.round_to_hour is True


@pytest.mark.asyncio
async def test_update_project_round_to_hour_ignored_without_hourly_rate(
    update_project_interactor,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        round_to_hour=True,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.hourly_rate is None
    assert result.round_to_hour is False


@pytest.mark.asyncio
async def test_update_project_sets_hourly_rate_and_round_to_hour_together(
    update_project_interactor,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        hourly_rate=Decimal("40.00"),
        hourly_rate_set=True,
        round_to_hour=True,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.hourly_rate == Decimal("40.00")
    assert result.round_to_hour is True


@pytest.mark.asyncio
@pytest.mark.parametrize("hourly_rate", [None, Decimal("0")])
async def test_update_project_clearing_hourly_rate_resets_round_to_hour(
    update_project_interactor,
    mock_project_gateway,
    hourly_rate,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        hourly_rate=Decimal("40.00"),
        round_to_hour=True,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        hourly_rate=hourly_rate,
        hourly_rate_set=True,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.hourly_rate is None
    assert result.round_to_hour is False


@pytest.mark.asyncio
async def test_update_project_keeps_existing_round_to_hour_when_omitted(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        hourly_rate=Decimal("40.00"),
        round_to_hour=True,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="New name",
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.round_to_hour is True


@pytest.mark.asyncio
async def test_update_project_restore(
    update_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        status=ProjectStatus.ARCHIVED,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        status=ProjectStatus.ACTIVE.value,
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.status == ProjectStatus.ACTIVE
    mock_timer_gateway.get_running_timer_by_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_project_keeps_existing_status_when_omitted(
    update_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        status=ProjectStatus.ARCHIVED,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="New name",
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    assert result.status == ProjectStatus.ARCHIVED


@pytest.mark.asyncio
async def test_update_project_invalid_status(
    update_project_interactor,
    mock_project_gateway,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        status="not-a-status",
    )
    with pytest.raises(InvalidProjectStatusError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )
    mock_project_gateway.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_update_project_negative_hourly_rate(
    update_project_interactor,
    mock_project_gateway,
):
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        hourly_rate=Decimal("-5"),
        hourly_rate_set=True,
    )
    with pytest.raises(InvalidHourlyRateError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )
    mock_project_gateway.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_update_project_preserves_identity_fields(
    update_project_interactor,
    mock_project_gateway,
):
    existing = _make_project()
    mock_project_gateway.get_project_by_id.return_value = existing
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        name="Renamed",
    )
    result = await update_project_interactor(
        current_user_id=TEST_USER_ID,
        update_project_dto=update_project_dto,
    )
    stored = mock_project_gateway.update_project.call_args.kwargs["project"]
    assert stored.id == TEST_PROJECT_ID
    assert stored.user_id == TEST_USER_ID
    assert stored.created_at == existing.created_at
    assert result.name == "Renamed"
    assert result.user_id == TEST_USER_ID


@pytest.mark.asyncio
async def test_update_project_not_owned(
    update_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        user_id=TEST_OTHER_USER_ID,
    )
    update_project_dto = UpdateProjectRequestDTO(
        id=TEST_PROJECT_ID,
        status=ProjectStatus.ARCHIVED.value,
    )
    with pytest.raises(ProjectNotFoundError):
        await update_project_interactor(
            current_user_id=TEST_USER_ID,
            update_project_dto=update_project_dto,
        )
    mock_timer_gateway.get_running_timer_by_user.assert_not_called()
    mock_project_gateway.update_project.assert_not_called()

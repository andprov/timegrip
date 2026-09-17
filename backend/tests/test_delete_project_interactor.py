from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    ProjectHasRunningTimerError,
    ProjectNotFoundError,
)
from timegrip.application.project.delete_project import (
    DeleteProjectInteractor,
)
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


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_project_by_id.return_value = _make_project()
    return gateway


@pytest.fixture
def mock_timer_gateway():
    gateway = AsyncMock()
    gateway.get_running_timer_by_user.return_value = None
    return gateway


@pytest.fixture
def delete_project_interactor(mock_project_gateway, mock_timer_gateway):
    return DeleteProjectInteractor(
        project_gateway=mock_project_gateway,
        timer_gateway=mock_timer_gateway,
        permission_gateway=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_delete_project_success(
    delete_project_interactor,
    mock_project_gateway,
):
    await delete_project_interactor(
        current_user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    mock_project_gateway.delete_project.assert_called_once_with(
        id=TEST_PROJECT_ID,
    )


@pytest.mark.asyncio
async def test_delete_project_allowed_while_other_project_timer_runs(
    delete_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = (
        _make_running_timer(project_id=TEST_OTHER_PROJECT_ID)
    )
    await delete_project_interactor(
        current_user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    mock_project_gateway.delete_project.assert_called_once_with(
        id=TEST_PROJECT_ID,
    )


@pytest.mark.asyncio
async def test_delete_project_rejected_while_its_timer_runs(
    delete_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_timer_gateway.get_running_timer_by_user.return_value = (
        _make_running_timer(project_id=TEST_PROJECT_ID)
    )
    with pytest.raises(ProjectHasRunningTimerError) as exc_info:
        await delete_project_interactor(
            current_user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        )
    assert exc_info.value.code == "project_has_running_timer"
    mock_project_gateway.delete_project.assert_not_called()


@pytest.mark.asyncio
async def test_delete_project_not_found(
    delete_project_interactor,
    mock_project_gateway,
    mock_timer_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    with pytest.raises(ProjectNotFoundError):
        await delete_project_interactor(
            current_user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        )
    mock_timer_gateway.get_running_timer_by_user.assert_not_called()
    mock_project_gateway.delete_project.assert_not_called()


@pytest.mark.asyncio
async def test_delete_project_not_owned(
    delete_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        user_id=TEST_OTHER_USER_ID,
    )
    with pytest.raises(ProjectNotFoundError):
        await delete_project_interactor(
            current_user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        )
    mock_project_gateway.delete_project.assert_not_called()

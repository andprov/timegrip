from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import AccessDeniedError
from timegrip.application.project.add_project import (
    AddProjectInteractor,
    AddProjectRequestDTO,
)
from timegrip.application.project.delete_project import (
    DeleteProjectInteractor,
)
from timegrip.application.project.get_all_user_projects import (
    GetAllUserProjectsInteractor,
)
from timegrip.application.project.get_project import GetProjectByIdInteractor
from timegrip.application.project.update_project import (
    UpdateProjectInteractor,
    UpdateProjectRequestDTO,
)
from timegrip.application.timer.add_manual_timer import (
    AddManualTimerInteractor,
    AddManualTimerRequestDTO,
)
from timegrip.application.timer.bulk_delete_timer import (
    BulkDeleteTimerInteractor,
)
from timegrip.application.timer.delete_timer import DeleteTimerInteractor
from timegrip.application.timer.get_all_user_timers import (
    GetAllUserTimersInteractor,
)
from timegrip.application.timer.get_running_timer import (
    GetRunningTimerInteractor,
)
from timegrip.application.timer.get_timer import GetTimerByIdInteractor
from timegrip.application.timer.start_timer import (
    StartTimerInteractor,
    StartTimerRequestDTO,
)
from timegrip.application.timer.stop_timer import StopTimerInteractor
from timegrip.application.timer.update_timer import (
    UpdateTimerInteractor,
    UpdateTimerRequestDTO,
)

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_TIMER_ID = UUID("00000000-0000-0000-0000-000000000099")


def _add_manual_timer(timers, projects, permissions):
    now = datetime.now(UTC)
    return AddManualTimerInteractor(
        timer_gateway=timers,
        project_gateway=projects,
        permission_gateway=permissions,
    )(
        add_timer_dto=AddManualTimerRequestDTO(
            project_id=TEST_PROJECT_ID,
            user_id=TEST_USER_ID,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
        ),
    )


def _start_timer(timers, projects, permissions):
    return StartTimerInteractor(
        timer_gateway=timers,
        project_gateway=projects,
        permission_gateway=permissions,
    )(
        start_timer_dto=StartTimerRequestDTO(
            project_id=TEST_PROJECT_ID,
            user_id=TEST_USER_ID,
        ),
    )


def _stop_timer(timers, projects, permissions):
    return StopTimerInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID)


def _update_timer(timers, projects, permissions):
    return UpdateTimerInteractor(
        timer_gateway=timers,
        project_gateway=projects,
        permission_gateway=permissions,
    )(
        current_user_id=TEST_USER_ID,
        update_timer_dto=UpdateTimerRequestDTO(id=TEST_TIMER_ID),
    )


def _delete_timer(timers, projects, permissions):
    return DeleteTimerInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, timer_id=TEST_TIMER_ID)


def _bulk_delete_timers(timers, projects, permissions):
    return BulkDeleteTimerInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, timer_ids=[TEST_TIMER_ID])


def _get_timer(timers, projects, permissions):
    return GetTimerByIdInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, timer_id=TEST_TIMER_ID)


def _get_running_timer(timers, projects, permissions):
    return GetRunningTimerInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID)


def _get_all_user_timers(timers, projects, permissions):
    return GetAllUserTimersInteractor(
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, page=1, page_size=10)


def _add_project(timers, projects, permissions):
    return AddProjectInteractor(
        project_gateway=projects,
        permission_gateway=permissions,
    )(
        add_project_dto=AddProjectRequestDTO(
            name="Website Redesign",
            user_id=TEST_USER_ID,
        ),
    )


def _update_project(timers, projects, permissions):
    return UpdateProjectInteractor(
        project_gateway=projects,
        timer_gateway=timers,
        permission_gateway=permissions,
    )(
        current_user_id=TEST_USER_ID,
        update_project_dto=UpdateProjectRequestDTO(id=TEST_PROJECT_ID),
    )


def _delete_project(timers, projects, permissions):
    return DeleteProjectInteractor(
        project_gateway=projects,
        timer_gateway=timers,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, project_id=TEST_PROJECT_ID)


def _get_project(timers, projects, permissions):
    return GetProjectByIdInteractor(
        project_gateway=projects,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, project_id=TEST_PROJECT_ID)


def _get_all_user_projects(timers, projects, permissions):
    return GetAllUserProjectsInteractor(
        project_gateway=projects,
        permission_gateway=permissions,
    )(current_user_id=TEST_USER_ID, page=1, page_size=10)


PROTECTED_USE_CASES = [
    _add_manual_timer,
    _start_timer,
    _stop_timer,
    _update_timer,
    _delete_timer,
    _bulk_delete_timers,
    _get_timer,
    _get_running_timer,
    _get_all_user_timers,
    _add_project,
    _update_project,
    _delete_project,
    _get_project,
    _get_all_user_projects,
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_case",
    PROTECTED_USE_CASES,
    ids=lambda use_case: use_case.__name__.lstrip("_"),
)
async def test_use_case_denied_for_user_without_permission(use_case):
    timers = AsyncMock()
    projects = AsyncMock()
    permissions = AsyncMock()
    permissions.check_permission.side_effect = AccessDeniedError(
        "Access denied",
    )
    with pytest.raises(AccessDeniedError):
        await use_case(timers, projects, permissions)
    permissions.check_permission.assert_called_once_with(user_id=TEST_USER_ID)
    assert timers.mock_calls == []
    assert projects.mock_calls == []

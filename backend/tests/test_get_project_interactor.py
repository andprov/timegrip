from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import ProjectNotFoundError
from timegrip.application.project.get_project import GetProjectByIdInteractor
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


def _make_project(**overrides):
    defaults = {
        "id": TEST_PROJECT_ID,
        "name": "Website Redesign",
        "color": ProjectColor.BLUE,
        "hourly_rate": Decimal("50.00"),
        "round_to_hour": True,
        "status": ProjectStatus.ARCHIVED,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Project(**defaults)


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_project_by_id.return_value = _make_project()
    return gateway


@pytest.fixture
def get_project_interactor(mock_project_gateway):
    return GetProjectByIdInteractor(
        project_gateway=mock_project_gateway,
        permission_gateway=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_project_success(
    get_project_interactor,
    mock_project_gateway,
):
    result = await get_project_interactor(
        current_user_id=TEST_USER_ID,
        project_id=TEST_PROJECT_ID,
    )
    mock_project_gateway.get_project_by_id.assert_called_once_with(
        id=TEST_PROJECT_ID,
    )
    assert result.id == TEST_PROJECT_ID
    assert result.name == "Website Redesign"
    assert result.color == ProjectColor.BLUE
    assert result.hourly_rate == Decimal("50.00")
    assert result.round_to_hour is True
    assert result.status == ProjectStatus.ARCHIVED
    assert result.user_id == TEST_USER_ID


@pytest.mark.asyncio
async def test_get_project_not_found(
    get_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = None
    with pytest.raises(ProjectNotFoundError):
        await get_project_interactor(
            current_user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        )


@pytest.mark.asyncio
async def test_get_project_not_owned_is_reported_as_not_found(
    get_project_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_project_by_id.return_value = _make_project(
        user_id=TEST_OTHER_USER_ID,
    )
    with pytest.raises(ProjectNotFoundError) as exc_info:
        await get_project_interactor(
            current_user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
        )
    assert str(exc_info.value) == (
        f"Project with id {TEST_PROJECT_ID} not found"
    )

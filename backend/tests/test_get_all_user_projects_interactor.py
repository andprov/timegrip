from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.project.get_all_user_projects import (
    GetAllUserProjectsInteractor,
)
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.get_all_user_projects.return_value = [
        Project(
            id=TEST_PROJECT_ID,
            name="Website Redesign",
            color=ProjectColor.GRAY,
            hourly_rate=None,
            round_to_hour=False,
            status=ProjectStatus.ACTIVE,
            user_id=TEST_USER_ID,
            created_at=datetime.now(UTC),
        ),
    ]
    gateway.count_user_projects.return_value = 1
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def get_all_user_projects_interactor(
    mock_project_gateway,
    mock_permission_gateway,
):
    return GetAllUserProjectsInteractor(
        project_gateway=mock_project_gateway,
        permission_gateway=mock_permission_gateway,
    )


@pytest.mark.asyncio
async def test_get_all_user_projects_returns_total(
    get_all_user_projects_interactor,
    mock_project_gateway,
):
    result = await get_all_user_projects_interactor(
        current_user_id=TEST_USER_ID,
        page=1,
        page_size=10,
    )
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == TEST_PROJECT_ID
    assert result.items[0].status == ProjectStatus.ACTIVE
    mock_project_gateway.count_user_projects.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_get_all_user_projects_total_independent_of_page_slice(
    get_all_user_projects_interactor,
    mock_project_gateway,
):
    mock_project_gateway.count_user_projects.return_value = 42
    result = await get_all_user_projects_interactor(
        current_user_id=TEST_USER_ID,
        page=2,
        page_size=10,
    )
    assert result.total == 42
    assert len(result.items) == 1
    mock_project_gateway.get_all_user_projects.assert_called_once_with(
        user_id=TEST_USER_ID,
        offset=10,
        limit=10,
    )


@pytest.mark.asyncio
async def test_get_all_user_projects_maps_all_fields(
    get_all_user_projects_interactor,
    mock_project_gateway,
):
    mock_project_gateway.get_all_user_projects.return_value = [
        Project(
            id=TEST_PROJECT_ID,
            name="Old Project",
            color=ProjectColor.RED,
            hourly_rate=Decimal("25.00"),
            round_to_hour=True,
            status=ProjectStatus.ARCHIVED,
            user_id=TEST_USER_ID,
            created_at=datetime.now(UTC),
        ),
    ]
    result = await get_all_user_projects_interactor(
        current_user_id=TEST_USER_ID,
        page=1,
        page_size=10,
    )
    item = result.items[0]
    assert item.name == "Old Project"
    assert item.color == ProjectColor.RED
    assert item.hourly_rate == Decimal("25.00")
    assert item.round_to_hour is True
    assert item.status == ProjectStatus.ARCHIVED

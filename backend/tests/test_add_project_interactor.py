from dataclasses import replace
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import InvalidProjectColorError
from timegrip.application.project.add_project import (
    AddProjectInteractor,
    AddProjectRequestDTO,
)
from timegrip.entities.exceptions import InvalidHourlyRateError
from timegrip.entities.project import ProjectColor, ProjectStatus

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000010")


@pytest.fixture
def mock_project_gateway():
    gateway = AsyncMock()
    gateway.add_project.side_effect = lambda project: replace(
        project,
        id=TEST_PROJECT_ID,
    )
    return gateway


@pytest.fixture
def mock_permission_gateway():
    return AsyncMock()


@pytest.fixture
def add_project_interactor(mock_project_gateway, mock_permission_gateway):
    return AddProjectInteractor(
        project_gateway=mock_project_gateway,
        permission_gateway=mock_permission_gateway,
    )


@pytest.mark.asyncio
async def test_add_project_with_defaults(
    add_project_interactor,
    mock_project_gateway,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
    )
    result = await add_project_interactor(add_project_dto=add_project_dto)
    stored = mock_project_gateway.add_project.call_args.kwargs["project"]
    assert stored.id is None
    assert stored.name == "Website Redesign"
    assert stored.color == ProjectColor.GRAY
    assert stored.hourly_rate is None
    assert stored.round_to_hour is False
    assert stored.status == ProjectStatus.ACTIVE
    assert stored.user_id == TEST_USER_ID
    assert result.id == TEST_PROJECT_ID
    assert result.color == ProjectColor.GRAY
    assert result.status == ProjectStatus.ACTIVE
    assert result.user_id == TEST_USER_ID


@pytest.mark.asyncio
async def test_add_project_with_valid_color(
    add_project_interactor,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
        color=ProjectColor.BLUE.value,
    )
    result = await add_project_interactor(add_project_dto=add_project_dto)
    assert result.color == ProjectColor.BLUE


@pytest.mark.asyncio
async def test_add_project_with_invalid_color(
    add_project_interactor,
    mock_project_gateway,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
        color="#123456",
    )
    with pytest.raises(InvalidProjectColorError):
        await add_project_interactor(add_project_dto=add_project_dto)
    mock_project_gateway.add_project.assert_not_called()


@pytest.mark.asyncio
async def test_add_project_with_billing_settings(
    add_project_interactor,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
        hourly_rate=Decimal("50.00"),
        round_to_hour=True,
    )
    result = await add_project_interactor(add_project_dto=add_project_dto)
    assert result.hourly_rate == Decimal("50.00")
    assert result.round_to_hour is True


@pytest.mark.asyncio
@pytest.mark.parametrize("hourly_rate", [None, Decimal("0")])
async def test_add_project_without_hourly_rate_ignores_round_to_hour(
    add_project_interactor,
    hourly_rate,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
        hourly_rate=hourly_rate,
        round_to_hour=True,
    )
    result = await add_project_interactor(add_project_dto=add_project_dto)
    assert result.hourly_rate is None
    assert result.round_to_hour is False


@pytest.mark.asyncio
async def test_add_project_with_negative_hourly_rate(
    add_project_interactor,
    mock_project_gateway,
):
    add_project_dto = AddProjectRequestDTO(
        name="Website Redesign",
        user_id=TEST_USER_ID,
        hourly_rate=Decimal("-1"),
    )
    with pytest.raises(InvalidHourlyRateError):
        await add_project_interactor(add_project_dto=add_project_dto)
    mock_project_gateway.add_project.assert_not_called()

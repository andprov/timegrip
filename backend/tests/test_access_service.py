from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.common.access_service import AccessService
from timegrip.application.exceptions import (
    AccessDeniedError,
    UserNotFoundError,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(is_active):
    return User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=is_active,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def access_service(mock_user_gateway):
    return AccessService(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
async def test_ensure_active_user_allows_active_user(
    access_service,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user(is_active=True)
    await access_service.ensure_active_user(user_id=TEST_USER_ID)
    mock_user_gateway.get_user_by_id.assert_called_once_with(id=TEST_USER_ID)


@pytest.mark.asyncio
async def test_ensure_active_user_denies_inactive_user(
    access_service,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user(is_active=False)
    with pytest.raises(AccessDeniedError) as exc_info:
        await access_service.ensure_active_user(user_id=TEST_USER_ID)
    assert exc_info.value.code == "access_denied"


@pytest.mark.asyncio
async def test_ensure_active_user_unknown_user(
    access_service,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await access_service.ensure_active_user(user_id=TEST_USER_ID)

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import UserNotFoundError
from timegrip.application.user.get_user import GetUserByIdInteractor
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def get_user_interactor(mock_user_gateway):
    return GetUserByIdInteractor(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
async def test_get_user_success(get_user_interactor, mock_user_gateway):
    mock_user_gateway.get_user_by_id.return_value = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=False,
        time_format=TimeFormat.TWELVE_HOUR,
        locale=Locale.RU,
    )
    result = await get_user_interactor(current_user_id=TEST_USER_ID)
    mock_user_gateway.get_user_by_id.assert_called_once_with(id=TEST_USER_ID)
    assert result.id == TEST_USER_ID
    assert result.email == "user@example.com"
    assert result.is_active is False
    assert result.time_format == TimeFormat.TWELVE_HOUR
    assert result.locale == Locale.RU
    assert not hasattr(result, "hashed_password")


@pytest.mark.asyncio
async def test_get_user_not_found(get_user_interactor, mock_user_gateway):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await get_user_interactor(current_user_id=TEST_USER_ID)

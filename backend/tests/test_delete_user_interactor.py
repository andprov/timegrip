from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import UserNotFoundError
from timegrip.application.user.delete_user import DeleteUserInteractor
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_id.return_value = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    return gateway


@pytest.fixture
def delete_user_interactor(mock_user_gateway):
    return DeleteUserInteractor(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
async def test_delete_user_success(delete_user_interactor, mock_user_gateway):
    await delete_user_interactor(current_user_id=TEST_USER_ID)
    mock_user_gateway.delete_user.assert_called_once_with(id=TEST_USER_ID)


@pytest.mark.asyncio
async def test_delete_user_not_found(
    delete_user_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await delete_user_interactor(current_user_id=TEST_USER_ID)
    mock_user_gateway.delete_user.assert_not_called()

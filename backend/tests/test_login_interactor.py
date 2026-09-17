from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.auth.login import (
    AuthRequestDTO,
    AuthUserInteractor,
)
from timegrip.application.exceptions import InvalidCredentialsError
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_email.return_value = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    return gateway


@pytest.fixture
def mock_password_hasher():
    hasher = AsyncMock()
    hasher.verify_password.return_value = True
    return hasher


@pytest.fixture
def login_interactor(mock_user_gateway, mock_password_hasher):
    return AuthUserInteractor(
        user_gateway=mock_user_gateway,
        password_hasher=mock_password_hasher,
    )


@pytest.mark.asyncio
async def test_login_looks_user_up_by_normalized_email(
    login_interactor,
    mock_user_gateway,
):
    user_id = await login_interactor(
        auth_dto=AuthRequestDTO(email="USER@Example.com", password="Passw0rd"),
    )
    assert user_id == TEST_USER_ID
    mock_user_gateway.get_user_by_email.assert_called_once_with(
        email=Email("user@example.com"),
    )


@pytest.mark.asyncio
async def test_login_rejects_unknown_email(
    login_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = None
    with pytest.raises(InvalidCredentialsError) as exc_info:
        await login_interactor(
            auth_dto=AuthRequestDTO(
                email="nobody@example.com",
                password="Passw0rd",
            ),
        )
    assert str(exc_info.value) == "Invalid email or password"
    assert exc_info.value.code == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(
    login_interactor,
    mock_password_hasher,
):
    mock_password_hasher.verify_password.return_value = False
    with pytest.raises(InvalidCredentialsError) as exc_info:
        await login_interactor(
            auth_dto=AuthRequestDTO(
                email="user@example.com",
                password="Wr0ngPass",
            ),
        )
    assert str(exc_info.value) == "Invalid email or password"
    assert exc_info.value.code == "invalid_credentials"
    mock_password_hasher.verify_password.assert_called_once_with(
        password="Wr0ngPass",
        hashed_password="hash",
    )


@pytest.mark.asyncio
async def test_login_allows_inactive_user(
    login_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=False,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    user_id = await login_interactor(
        auth_dto=AuthRequestDTO(email="user@example.com", password="Passw0rd"),
    )
    assert user_id == TEST_USER_ID

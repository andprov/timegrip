from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    WeakPasswordError,
)
from timegrip.application.user.update_password import (
    UpdatePasswordInteractor,
    UpdatePasswordRequestDTO,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def mock_password_hasher():
    mock = AsyncMock()
    mock.verify_password.return_value = True
    mock.hash_password.return_value = "new_hash"
    return mock


@pytest.fixture
def mock_refresh_token_gateway():
    return AsyncMock()


@pytest.fixture
def update_password_interactor(
    mock_user_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    return UpdatePasswordInteractor(
        user_gateway=mock_user_gateway,
        password_hasher=mock_password_hasher,
        refresh_token_gateway=mock_refresh_token_gateway,
    )


def _make_user(**overrides):
    defaults = {
        "id": TEST_USER_ID,
        "email": Email("user@example.com"),
        "hashed_password": "old_hash",
        "is_active": True,
        "time_format": TimeFormat.TWENTY_FOUR_HOUR,
        "locale": Locale.EN,
    }
    defaults.update(overrides)
    return User(**defaults)


@pytest.mark.asyncio
async def test_update_password_success(
    update_password_interactor,
    mock_user_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user()
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="OldPassw0rd",
        new_password="NewPassw0rd",
    )
    await update_password_interactor(
        current_user_id=TEST_USER_ID,
        update_password_dto=update_password_dto,
    )
    mock_password_hasher.verify_password.assert_called_once_with(
        password="OldPassw0rd",
        hashed_password="old_hash",
    )
    updated_user = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert updated_user.hashed_password == "new_hash"
    mock_refresh_token_gateway.revoke_all_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_update_password_revokes_sessions_before_update(
    update_password_interactor,
    mock_user_gateway,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user()
    calls = Mock()
    calls.attach_mock(
        mock_refresh_token_gateway.revoke_all_for_user,
        "revoke_all_for_user",
    )
    calls.attach_mock(mock_user_gateway.update_user, "update_user")
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="OldPassw0rd",
        new_password="NewPassw0rd",
    )
    await update_password_interactor(
        current_user_id=TEST_USER_ID,
        update_password_dto=update_password_dto,
    )
    assert [name for name, _, _ in calls.mock_calls] == [
        "revoke_all_for_user",
        "update_user",
    ]


@pytest.mark.asyncio
async def test_update_password_wrong_current_password(
    update_password_interactor,
    mock_user_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user()
    mock_password_hasher.verify_password.return_value = False
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="WrongPassw0rd",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidCredentialsError) as exc_info:
        await update_password_interactor(
            current_user_id=TEST_USER_ID,
            update_password_dto=update_password_dto,
        )
    assert exc_info.value.code == "invalid_current_password"
    mock_password_hasher.hash_password.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_weak_new_password(
    update_password_interactor,
    mock_user_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user()
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="OldPassw0rd",
        new_password="weak",
    )
    with pytest.raises(WeakPasswordError):
        await update_password_interactor(
            current_user_id=TEST_USER_ID,
            update_password_dto=update_password_dto,
        )
    mock_password_hasher.hash_password.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_user_not_found(
    update_password_interactor,
    mock_user_gateway,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="OldPassw0rd",
        new_password="NewPassw0rd",
    )
    with pytest.raises(UserNotFoundError):
        await update_password_interactor(
            current_user_id=TEST_USER_ID,
            update_password_dto=update_password_dto,
        )
    mock_user_gateway.update_user.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_keeps_other_user_fields(
    update_password_interactor,
    mock_user_gateway,
):
    user = _make_user(
        is_active=False,
        time_format=TimeFormat.TWELVE_HOUR,
        locale=Locale.RU,
    )
    mock_user_gateway.get_user_by_id.return_value = user
    update_password_dto = UpdatePasswordRequestDTO(
        current_password="OldPassw0rd",
        new_password="NewPassw0rd",
    )
    await update_password_interactor(
        current_user_id=TEST_USER_ID,
        update_password_dto=update_password_dto,
    )
    updated_user = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert updated_user.id == user.id
    assert updated_user.email == user.email
    assert updated_user.is_active is False
    assert updated_user.time_format == TimeFormat.TWELVE_HOUR
    assert updated_user.locale == Locale.RU

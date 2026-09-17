from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidPasswordResetCodeError,
    WeakPasswordError,
)
from timegrip.application.password_reset.password_reset_code_manager import (
    MAX_PASSWORD_RESET_ATTEMPTS,
)
from timegrip.application.password_reset.reset_password import (
    ResetPasswordInteractor,
    ResetPasswordRequestDTO,
)
from timegrip.entities.password_reset_code import PasswordResetCode
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def mock_password_reset_code_gateway():
    return AsyncMock()


@pytest.fixture
def mock_password_hasher():
    mock = AsyncMock()
    mock.hash_password.return_value = "new_hash"
    return mock


@pytest.fixture
def mock_refresh_token_gateway():
    return AsyncMock()


@pytest.fixture
def reset_password_interactor(
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    return ResetPasswordInteractor(
        user_gateway=mock_user_gateway,
        password_reset_code_gateway=mock_password_reset_code_gateway,
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


def _make_code(**overrides):
    defaults = {
        "id": 10,
        "user_id": TEST_USER_ID,
        "code": "123456",
        "expires_at": datetime.now(UTC) + timedelta(minutes=15),
        "used_at": None,
        "attempts": 0,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return PasswordResetCode(**defaults)


@pytest.mark.asyncio
async def test_reset_password_success(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    reset_code = _make_code()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        reset_code
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    await reset_password_interactor(reset_dto=reset_dto)
    mock_refresh_token_gateway.revoke_all_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_password_hasher.hash_password.assert_called_once_with(
        password="NewPassw0rd",
    )
    updated_user = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert updated_user.hashed_password == "new_hash"
    mock_password_reset_code_gateway.mark_code_used.assert_called_once_with(
        id=reset_code.id,
    )
    mock_password_reset_code_gateway.delete_codes_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_password_reset_code_gateway.increment_attempts.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_wrong_code_increments_attempts(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    reset_code = _make_code(code="123456")
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        reset_code
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="000000",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_reset_code_gateway.increment_attempts.assert_called_once_with(
        id=reset_code.id,
    )
    mock_user_gateway.update_user.assert_not_called()
    mock_password_hasher.hash_password.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_expired_code(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_user_gateway.update_user.assert_not_called()
    mock_password_reset_code_gateway.increment_attempts.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_already_used_code(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(used_at=datetime.now(UTC))
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_no_code(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        None
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_reset_code_gateway.increment_attempts.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_wrong_code_checked_before_password_strength(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(code="123456")
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="000000",
        new_password="weak",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_reset_code_gateway.increment_attempts.assert_called_once_with(
        id=10,
    )
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_attempts_exhausted(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(attempts=MAX_PASSWORD_RESET_ATTEMPTS)
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_reset_code_gateway.increment_attempts.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_unknown_email(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = None
    reset_dto = ResetPasswordRequestDTO(
        email="unknown@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    with pytest.raises(InvalidPasswordResetCodeError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_reset_code_gateway.get_latest_code_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_weak_new_password(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_hasher,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    reset_code = _make_code()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        reset_code
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="weak",
    )
    with pytest.raises(WeakPasswordError):
        await reset_password_interactor(reset_dto=reset_dto)
    mock_password_hasher.hash_password.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()
    mock_password_reset_code_gateway.mark_code_used.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_last_allowed_attempt_succeeds(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(attempts=MAX_PASSWORD_RESET_ATTEMPTS - 1)
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    await reset_password_interactor(reset_dto=reset_dto)
    mock_user_gateway.update_user.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_looks_user_up_by_normalized_email(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code()
    )
    reset_dto = ResetPasswordRequestDTO(
        email="User@Example.COM",
        code="123456",
        new_password="NewPassw0rd",
    )
    await reset_password_interactor(reset_dto=reset_dto)
    mock_user_gateway.get_user_by_email.assert_called_once_with(
        email=Email("user@example.com"),
    )
    mock_password_reset_code_gateway.get_latest_code_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_reset_password_keeps_other_user_fields(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
):
    user = _make_user(
        is_active=False,
        time_format=TimeFormat.TWELVE_HOUR,
        locale=Locale.RU,
    )
    mock_user_gateway.get_user_by_email.return_value = user
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code()
    )
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    await reset_password_interactor(reset_dto=reset_dto)
    updated_user = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert updated_user.id == user.id
    assert updated_user.email == user.email
    assert updated_user.is_active is False
    assert updated_user.time_format == TimeFormat.TWELVE_HOUR
    assert updated_user.locale == Locale.RU


@pytest.mark.asyncio
async def test_reset_password_revokes_sessions_before_update(
    reset_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_refresh_token_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code()
    )
    calls = Mock()
    calls.attach_mock(
        mock_refresh_token_gateway.revoke_all_for_user,
        "revoke_all_for_user",
    )
    calls.attach_mock(mock_user_gateway.update_user, "update_user")
    reset_dto = ResetPasswordRequestDTO(
        email="user@example.com",
        code="123456",
        new_password="NewPassw0rd",
    )
    await reset_password_interactor(reset_dto=reset_dto)
    assert [name for name, _, _ in calls.mock_calls] == [
        "revoke_all_for_user",
        "update_user",
    ]

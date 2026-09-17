from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.user.activate_user import (
    ActivateUserInteractor,
    ActivateUserRequestDTO,
)
from timegrip.application.user_activation.activation_code_manager import (
    MAX_ACTIVATION_ATTEMPTS,
)
from timegrip.entities.activation_code import ActivationCode
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(**overrides):
    defaults = {
        "id": TEST_USER_ID,
        "email": Email("user@example.com"),
        "hashed_password": "hash",
        "is_active": False,
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
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "used_at": None,
        "attempts": 0,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return ActivationCode(**defaults)


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_id.return_value = _make_user()
    return gateway


@pytest.fixture
def mock_activation_code_gateway():
    gateway = AsyncMock()
    gateway.get_latest_code_for_user.return_value = _make_code()
    return gateway


@pytest.fixture
def activate_user_interactor(mock_user_gateway, mock_activation_code_gateway):
    return ActivateUserInteractor(
        user_gateway=mock_user_gateway,
        activation_code_gateway=mock_activation_code_gateway,
    )


@pytest.mark.asyncio
async def test_activate_user_success(
    activate_user_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    await activate_user_interactor(
        current_user_id=TEST_USER_ID,
        activate_dto=ActivateUserRequestDTO(code="123456"),
    )
    get_latest_code = mock_activation_code_gateway.get_latest_code_for_user
    get_latest_code.assert_called_once_with(user_id=TEST_USER_ID)
    mock_activation_code_gateway.mark_code_used.assert_called_once_with(id=10)
    mock_user_gateway.activate_user.assert_called_once_with(id=TEST_USER_ID)
    mock_activation_code_gateway.delete_codes_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_activation_code_gateway.increment_attempts.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "activation_code",
    [
        None,
        _make_code(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
        _make_code(used_at=datetime.now(UTC)),
        _make_code(attempts=MAX_ACTIVATION_ATTEMPTS),
    ],
    ids=["no_code", "expired_code", "used_code", "attempts_exhausted"],
)
async def test_activate_user_rejects_invalid_code(
    activate_user_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
    activation_code,
):
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        activation_code
    )
    with pytest.raises(InvalidActivationCodeError) as exc_info:
        await activate_user_interactor(
            current_user_id=TEST_USER_ID,
            activate_dto=ActivateUserRequestDTO(code="123456"),
        )
    assert exc_info.value.code == "invalid_activation_code"
    mock_activation_code_gateway.increment_attempts.assert_not_called()
    mock_activation_code_gateway.mark_code_used.assert_not_called()
    mock_user_gateway.activate_user.assert_not_called()
    mock_activation_code_gateway.delete_codes_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_activate_user_wrong_code_increments_attempts(
    activate_user_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(code="654321", attempts=MAX_ACTIVATION_ATTEMPTS - 1)
    )
    with pytest.raises(InvalidActivationCodeError):
        await activate_user_interactor(
            current_user_id=TEST_USER_ID,
            activate_dto=ActivateUserRequestDTO(code="123456"),
        )
    mock_activation_code_gateway.increment_attempts.assert_called_once_with(
        id=10,
    )
    mock_activation_code_gateway.mark_code_used.assert_not_called()
    mock_user_gateway.activate_user.assert_not_called()


@pytest.mark.asyncio
async def test_activate_user_already_active(
    activate_user_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user(is_active=True)
    with pytest.raises(UserAlreadyActiveError):
        await activate_user_interactor(
            current_user_id=TEST_USER_ID,
            activate_dto=ActivateUserRequestDTO(code="123456"),
        )
    mock_activation_code_gateway.get_latest_code_for_user.assert_not_called()
    mock_user_gateway.activate_user.assert_not_called()
    mock_activation_code_gateway.delete_codes_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_activate_user_not_found(
    activate_user_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await activate_user_interactor(
            current_user_id=TEST_USER_ID,
            activate_dto=ActivateUserRequestDTO(code="123456"),
        )
    mock_activation_code_gateway.get_latest_code_for_user.assert_not_called()
    mock_user_gateway.activate_user.assert_not_called()

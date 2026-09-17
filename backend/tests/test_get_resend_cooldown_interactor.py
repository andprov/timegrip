from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.user_activation.activation_code_manager import (
    ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS,
)
from timegrip.application.user_activation.get_resend_cooldown import (
    GetResendCooldownInteractor,
)
from timegrip.entities.activation_code import ActivationCode
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(is_active=False):
    return User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=is_active,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )


def _make_code(created_at):
    return ActivationCode(
        id=10,
        user_id=TEST_USER_ID,
        code="123456",
        expires_at=created_at + timedelta(hours=1),
        used_at=None,
        attempts=0,
        created_at=created_at,
    )


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_id.return_value = _make_user()
    return gateway


@pytest.fixture
def mock_activation_code_gateway():
    gateway = AsyncMock()
    gateway.get_latest_code_for_user.return_value = None
    return gateway


@pytest.fixture
def get_resend_cooldown_interactor(
    mock_user_gateway,
    mock_activation_code_gateway,
):
    return GetResendCooldownInteractor(
        user_gateway=mock_user_gateway,
        activation_code_gateway=mock_activation_code_gateway,
    )


@pytest.mark.asyncio
async def test_get_resend_cooldown_for_recently_sent_code(
    get_resend_cooldown_interactor,
    mock_activation_code_gateway,
):
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=datetime.now(UTC) - timedelta(seconds=10))
    )
    result = await get_resend_cooldown_interactor(
        current_user_id=TEST_USER_ID,
    )
    assert result.retry_after_seconds == (
        ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS - 10
    )
    mock_activation_code_gateway.get_latest_code_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_get_resend_cooldown_after_cooldown(
    get_resend_cooldown_interactor,
    mock_activation_code_gateway,
):
    cooldown = timedelta(seconds=ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS)
    created_at = datetime.now(UTC) - cooldown - timedelta(seconds=1)
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=created_at)
    )
    result = await get_resend_cooldown_interactor(
        current_user_id=TEST_USER_ID,
    )
    assert result.retry_after_seconds == 0


@pytest.mark.asyncio
async def test_get_resend_cooldown_without_code(
    get_resend_cooldown_interactor,
):
    result = await get_resend_cooldown_interactor(
        current_user_id=TEST_USER_ID,
    )
    assert result.retry_after_seconds == 0


@pytest.mark.asyncio
async def test_get_resend_cooldown_user_not_found(
    get_resend_cooldown_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await get_resend_cooldown_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_gateway.get_latest_code_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_get_resend_cooldown_already_active(
    get_resend_cooldown_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user(is_active=True)
    with pytest.raises(UserAlreadyActiveError):
        await get_resend_cooldown_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_gateway.get_latest_code_for_user.assert_not_called()

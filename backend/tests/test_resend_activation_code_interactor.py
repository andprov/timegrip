from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.exceptions import (
    ActivationCodeRecentlySentError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from timegrip.application.user_activation.activation_code_manager import (
    ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS,
)
from timegrip.application.user_activation.activation_email import (
    build_activation_email,
)
from timegrip.application.user_activation.resend_activation_code import (
    ResendActivationCodeInteractor,
)
from timegrip.entities.activation_code import ActivationCode
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


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
    return AsyncMock()


@pytest.fixture
def mock_activation_code_gateway():
    gateway = AsyncMock()
    gateway.get_latest_code_for_user.return_value = None
    return gateway


@pytest.fixture
def mock_activation_code_manager():
    return AsyncMock()


@pytest.fixture
def mock_email_queue_gateway():
    return AsyncMock()


@pytest.fixture
def resend_activation_code_interactor(
    mock_user_gateway,
    mock_activation_code_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    return ResendActivationCodeInteractor(
        user_gateway=mock_user_gateway,
        activation_code_gateway=mock_activation_code_gateway,
        activation_code_manager=mock_activation_code_manager,
        email_queue_gateway=mock_email_queue_gateway,
        frontend_config=FrontendConfig(url="https://timegrip.test"),
    )


@pytest.mark.asyncio
async def test_resend_activation_code_success(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    user = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=False,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    mock_user_gateway.get_user_by_id.return_value = user
    mock_activation_code_manager.return_value = "654321"
    await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_manager.assert_called_once_with(user_id=TEST_USER_ID)
    mock_email_queue_gateway.enqueue.assert_called_once()
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    assert call_kwargs["to_email"] == "user@example.com"
    assert "654321" in call_kwargs["body"]
    assert "https://timegrip.test/dashboard?code=654321" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_resend_activation_code_user_not_found(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_resend_activation_code_already_active(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    user = User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    mock_user_gateway.get_user_by_id.return_value = user
    with pytest.raises(UserAlreadyActiveError):
        await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


def _inactive_user():
    return User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=False,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )


@pytest.mark.asyncio
async def test_resend_activation_code_rejects_recently_sent_code(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _inactive_user()
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=datetime.now(UTC) - timedelta(seconds=10))
    )
    with pytest.raises(ActivationCodeRecentlySentError) as exc_info:
        await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    assert exc_info.value.code == "activation_code_recently_sent"
    assert exc_info.value.retry_after_seconds == (
        ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS - 10
    )
    mock_activation_code_gateway.get_latest_code_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_activation_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_resend_activation_code_after_cooldown(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _inactive_user()
    cooldown = timedelta(seconds=ACTIVATION_CODE_RESEND_COOLDOWN_SECONDS)
    created_at = datetime.now(UTC) - cooldown - timedelta(seconds=1)
    mock_activation_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=created_at)
    )
    mock_activation_code_manager.return_value = "654321"
    await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    mock_activation_code_manager.assert_called_once_with(user_id=TEST_USER_ID)
    mock_email_queue_gateway.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_resend_activation_code_uses_user_locale(
    resend_activation_code_interactor,
    mock_user_gateway,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    user = replace(_inactive_user(), locale=Locale.RU)
    mock_user_gateway.get_user_by_id.return_value = user
    mock_activation_code_manager.return_value = "654321"
    await resend_activation_code_interactor(current_user_id=TEST_USER_ID)
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    expected_email = build_activation_email(
        "654321",
        activation_url="https://timegrip.test/dashboard?code=654321",
        locale=Locale.RU,
    )
    assert call_kwargs["subject"] == expected_email.subject
    assert call_kwargs["body"] == expected_email.body

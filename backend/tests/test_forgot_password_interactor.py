from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.password_reset.forgot_password import (
    ForgotPasswordInteractor,
)
from timegrip.application.password_reset.password_reset_code_manager import (
    PASSWORD_RESET_CODE_RESEND_COOLDOWN_SECONDS,
)
from timegrip.application.password_reset.password_reset_email import (
    build_password_reset_email,
)
from timegrip.entities.password_reset_code import PasswordResetCode
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user():
    return User(
        id=TEST_USER_ID,
        email=Email("user@example.com"),
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )


def _make_code(created_at):
    return PasswordResetCode(
        id=10,
        user_id=TEST_USER_ID,
        code="123456",
        expires_at=created_at + timedelta(minutes=15),
        used_at=None,
        attempts=0,
        created_at=created_at,
    )


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def mock_password_reset_code_gateway():
    gateway = AsyncMock()
    gateway.get_latest_code_for_user.return_value = None
    return gateway


@pytest.fixture
def mock_password_reset_code_manager():
    return AsyncMock()


@pytest.fixture
def mock_email_queue_gateway():
    return AsyncMock()


@pytest.fixture
def forgot_password_interactor(
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_reset_code_manager,
    mock_email_queue_gateway,
):
    return ForgotPasswordInteractor(
        user_gateway=mock_user_gateway,
        password_reset_code_gateway=mock_password_reset_code_gateway,
        password_reset_code_manager=mock_password_reset_code_manager,
        email_queue_gateway=mock_email_queue_gateway,
        frontend_config=FrontendConfig(url="https://timegrip.test"),
    )


@pytest.mark.asyncio
async def test_forgot_password_known_email(
    forgot_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_manager,
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
    mock_user_gateway.get_user_by_email.return_value = user
    mock_password_reset_code_manager.return_value = "654321"
    await forgot_password_interactor(email="user@example.com")
    mock_password_reset_code_manager.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_email_queue_gateway.enqueue.assert_called_once()
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    assert call_kwargs["to_email"] == "user@example.com"
    assert "654321" in call_kwargs["body"]
    assert (
        "https://timegrip.test/reset-password"
        "?email=user%40example.com&code=654321"
    ) in call_kwargs["body"]


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_is_silent(
    forgot_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = None
    await forgot_password_interactor(email="unknown@example.com")
    mock_password_reset_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_looks_user_up_by_normalized_email(
    forgot_password_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = None
    await forgot_password_interactor(email="User@Example.COM")
    mock_user_gateway.get_user_by_email.assert_called_once_with(
        email=Email("user@example.com"),
    )


@pytest.mark.asyncio
async def test_forgot_password_recently_sent_code_is_silent(
    forgot_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_reset_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=datetime.now(UTC) - timedelta(seconds=10))
    )
    await forgot_password_interactor(email="user@example.com")
    mock_password_reset_code_gateway.get_latest_code_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_password_reset_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_after_cooldown_sends_new_code(
    forgot_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_gateway,
    mock_password_reset_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    cooldown = timedelta(seconds=PASSWORD_RESET_CODE_RESEND_COOLDOWN_SECONDS)
    created_at = datetime.now(UTC) - cooldown - timedelta(seconds=1)
    mock_password_reset_code_gateway.get_latest_code_for_user.return_value = (
        _make_code(created_at=created_at)
    )
    mock_password_reset_code_manager.return_value = "654321"
    await forgot_password_interactor(email="user@example.com")
    mock_password_reset_code_manager.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_email_queue_gateway.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_forgot_password_uses_user_locale(
    forgot_password_interactor,
    mock_user_gateway,
    mock_password_reset_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = replace(
        _make_user(),
        locale=Locale.RU,
    )
    mock_password_reset_code_manager.return_value = "654321"
    await forgot_password_interactor(email="user@example.com")
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    expected_email = build_password_reset_email(
        "654321",
        reset_url=(
            "https://timegrip.test/reset-password"
            "?email=user%40example.com&code=654321"
        ),
        locale=Locale.RU,
    )
    assert call_kwargs["subject"] == expected_email.subject
    assert call_kwargs["body"] == expected_email.body

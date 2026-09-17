from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.auth.add_user import (
    AddUserInteractor,
    AddUserRequestDTO,
)
from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.application.exceptions import (
    UserAlreadyExistsError,
    WeakPasswordError,
)
from timegrip.application.user_activation.activation_email import (
    build_activation_email,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_email.return_value = None
    gateway.add_user.side_effect = lambda user: replace(user, id=TEST_USER_ID)
    return gateway


@pytest.fixture
def mock_password_hasher():
    hasher = AsyncMock()
    hasher.hash_password.return_value = "hash"
    return hasher


@pytest.fixture
def mock_activation_code_manager():
    return AsyncMock(return_value="123456")


@pytest.fixture
def mock_email_queue_gateway():
    return AsyncMock()


@pytest.fixture
def add_user_interactor(
    mock_user_gateway,
    mock_password_hasher,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    return AddUserInteractor(
        user_gateway=mock_user_gateway,
        password_hasher=mock_password_hasher,
        activation_code_manager=mock_activation_code_manager,
        email_queue_gateway=mock_email_queue_gateway,
        frontend_config=FrontendConfig(url="https://timegrip.test"),
    )


def _make_dto(**overrides):
    defaults = {"email": "new.user@example.com", "password": "Passw0rd"}
    defaults.update(overrides)
    return AddUserRequestDTO(**defaults)


@pytest.mark.asyncio
async def test_add_user_stores_email_in_lowercase(
    add_user_interactor,
    mock_user_gateway,
):
    result = await add_user_interactor(
        add_user_dto=_make_dto(email="New.User@Example.com"),
    )
    mock_user_gateway.get_user_by_email.assert_called_once_with(
        email=Email("new.user@example.com"),
    )
    stored = mock_user_gateway.add_user.call_args.kwargs["user"]
    assert stored.email == Email("new.user@example.com")
    assert result.email == "new.user@example.com"


@pytest.mark.asyncio
async def test_add_user_creates_inactive_user_with_hashed_password(
    add_user_interactor,
    mock_user_gateway,
    mock_password_hasher,
):
    result = await add_user_interactor(add_user_dto=_make_dto())
    mock_password_hasher.hash_password.assert_called_once_with(
        password="Passw0rd",
    )
    stored = mock_user_gateway.add_user.call_args.kwargs["user"]
    assert stored.id is None
    assert stored.hashed_password == "hash"
    assert stored.is_active is False
    assert stored.time_format == TimeFormat.TWENTY_FOUR_HOUR
    assert result.id == TEST_USER_ID
    assert result.is_active is False
    assert result.time_format == TimeFormat.TWENTY_FOUR_HOUR


@pytest.mark.asyncio
async def test_add_user_sends_activation_code(
    add_user_interactor,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    await add_user_interactor(
        add_user_dto=_make_dto(email="New.User@Example.com"),
    )
    mock_activation_code_manager.assert_called_once_with(user_id=TEST_USER_ID)
    mock_email_queue_gateway.enqueue.assert_called_once()
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    assert call_kwargs["to_email"] == "new.user@example.com"
    assert "123456" in call_kwargs["body"]
    assert "https://timegrip.test/dashboard?code=123456" in call_kwargs["body"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        ("ru", Locale.RU),
        (None, Locale.EN),
        ("de", Locale.EN),
    ],
)
async def test_add_user_locale(
    add_user_interactor,
    mock_user_gateway,
    mock_email_queue_gateway,
    locale,
    expected,
):
    result = await add_user_interactor(add_user_dto=_make_dto(locale=locale))
    stored = mock_user_gateway.add_user.call_args.kwargs["user"]
    assert stored.locale == expected
    assert result.locale == expected
    call_kwargs = mock_email_queue_gateway.enqueue.call_args.kwargs
    expected_email = build_activation_email(
        "123456",
        activation_url="https://timegrip.test/dashboard?code=123456",
        locale=expected,
    )
    assert call_kwargs["subject"] == expected_email.subject
    assert call_kwargs["body"] == expected_email.body


@pytest.mark.asyncio
async def test_add_user_existing_email(
    add_user_interactor,
    mock_user_gateway,
    mock_password_hasher,
    mock_activation_code_manager,
    mock_email_queue_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = User(
        id=TEST_USER_ID,
        email=Email("new.user@example.com"),
        hashed_password="hash",
        is_active=True,
        time_format=TimeFormat.TWENTY_FOUR_HOUR,
        locale=Locale.EN,
    )
    with pytest.raises(UserAlreadyExistsError):
        await add_user_interactor(
            add_user_dto=_make_dto(email="NEW.USER@example.com"),
        )
    mock_password_hasher.hash_password.assert_not_called()
    mock_user_gateway.add_user.assert_not_called()
    mock_activation_code_manager.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_add_user_weak_password(
    add_user_interactor,
    mock_user_gateway,
    mock_password_hasher,
    mock_email_queue_gateway,
):
    with pytest.raises(WeakPasswordError):
        await add_user_interactor(add_user_dto=_make_dto(password="weak"))
    mock_password_hasher.hash_password.assert_not_called()
    mock_user_gateway.add_user.assert_not_called()
    mock_email_queue_gateway.enqueue.assert_not_called()

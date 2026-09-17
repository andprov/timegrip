from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from timegrip.application.user.update_email import (
    UpdateEmailInteractor,
    UpdateEmailRequestDTO,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def _make_user(**overrides):
    defaults = {
        "id": TEST_USER_ID,
        "email": Email("user@example.com"),
        "hashed_password": "hash",
        "is_active": True,
        "time_format": TimeFormat.TWENTY_FOUR_HOUR,
        "locale": Locale.EN,
    }
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_id.return_value = _make_user()
    gateway.get_user_by_email.return_value = None
    gateway.update_user.side_effect = lambda user: user
    return gateway


@pytest.fixture
def mock_password_hasher():
    hasher = AsyncMock()
    hasher.verify_password.return_value = True
    return hasher


@pytest.fixture
def update_email_interactor(mock_user_gateway, mock_password_hasher):
    return UpdateEmailInteractor(
        user_gateway=mock_user_gateway,
        password_hasher=mock_password_hasher,
    )


@pytest.mark.asyncio
async def test_update_email_stores_new_email_in_lowercase(
    update_email_interactor,
    mock_user_gateway,
):
    result = await update_email_interactor(
        current_user_id=TEST_USER_ID,
        update_email_dto=UpdateEmailRequestDTO(
            password="Passw0rd",
            new_email="New.User@Example.com",
        ),
    )
    assert result.email == "new.user@example.com"
    mock_user_gateway.get_user_by_email.assert_called_once_with(
        email=Email("new.user@example.com"),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.email.value == "new.user@example.com"


@pytest.mark.asyncio
async def test_update_email_allows_changing_only_letter_case_of_own_email(
    update_email_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user()
    result = await update_email_interactor(
        current_user_id=TEST_USER_ID,
        update_email_dto=UpdateEmailRequestDTO(
            password="Passw0rd",
            new_email="USER@example.com",
        ),
    )
    assert result.email == "user@example.com"
    mock_user_gateway.update_user.assert_called_once()


@pytest.mark.asyncio
async def test_update_email_rejects_email_of_other_user_in_other_case(
    update_email_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_email.return_value = _make_user(
        id=TEST_OTHER_USER_ID,
        email=Email("taken@example.com"),
    )
    with pytest.raises(UserAlreadyExistsError):
        await update_email_interactor(
            current_user_id=TEST_USER_ID,
            update_email_dto=UpdateEmailRequestDTO(
                password="Passw0rd",
                new_email="Taken@Example.com",
            ),
        )
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_email_rejects_wrong_password(
    update_email_interactor,
    mock_user_gateway,
    mock_password_hasher,
):
    mock_password_hasher.verify_password.return_value = False
    with pytest.raises(InvalidCredentialsError) as exc_info:
        await update_email_interactor(
            current_user_id=TEST_USER_ID,
            update_email_dto=UpdateEmailRequestDTO(
                password="Wrong1pass",
                new_email="new@example.com",
            ),
        )
    assert exc_info.value.code == "invalid_password"
    mock_password_hasher.verify_password.assert_called_once_with(
        password="Wrong1pass",
        hashed_password="hash",
    )
    mock_user_gateway.get_user_by_email.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_email_user_not_found(
    update_email_interactor,
    mock_user_gateway,
    mock_password_hasher,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await update_email_interactor(
            current_user_id=TEST_USER_ID,
            update_email_dto=UpdateEmailRequestDTO(
                password="Passw0rd",
                new_email="new@example.com",
            ),
        )
    mock_password_hasher.verify_password.assert_not_called()
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_email_keeps_other_user_fields(
    update_email_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = _make_user(
        is_active=False,
        time_format=TimeFormat.TWELVE_HOUR,
        locale=Locale.RU,
    )
    result = await update_email_interactor(
        current_user_id=TEST_USER_ID,
        update_email_dto=UpdateEmailRequestDTO(
            password="Passw0rd",
            new_email="new@example.com",
        ),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.id == TEST_USER_ID
    assert stored.hashed_password == "hash"
    assert stored.is_active is False
    assert stored.time_format == TimeFormat.TWELVE_HOUR
    assert stored.locale == Locale.RU
    assert result.is_active is False
    assert result.time_format == TimeFormat.TWELVE_HOUR
    assert result.locale == Locale.RU

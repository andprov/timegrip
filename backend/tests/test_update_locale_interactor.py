from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidLocaleError,
    UserNotFoundError,
)
from timegrip.application.user.update_locale import (
    UpdateLocaleInteractor,
    UpdateLocaleRequestDTO,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(**overrides):
    defaults = {
        "id": TEST_USER_ID,
        "email": Email("user@example.com"),
        "hashed_password": "hash",
        "is_active": True,
        "time_format": TimeFormat.TWELVE_HOUR,
        "locale": Locale.EN,
    }
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def mock_user_gateway():
    gateway = AsyncMock()
    gateway.get_user_by_id.return_value = _make_user()
    gateway.update_user.side_effect = lambda user: user
    return gateway


@pytest.fixture
def update_locale_interactor(mock_user_gateway):
    return UpdateLocaleInteractor(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
@pytest.mark.parametrize("locale", [loc.value for loc in Locale])
async def test_update_locale_success(
    update_locale_interactor,
    mock_user_gateway,
    locale,
):
    result = await update_locale_interactor(
        current_user_id=TEST_USER_ID,
        update_locale_dto=UpdateLocaleRequestDTO(locale=locale),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.locale == Locale(locale)
    assert result.locale == Locale(locale)


@pytest.mark.asyncio
async def test_update_locale_keeps_other_user_fields(
    update_locale_interactor,
    mock_user_gateway,
):
    await update_locale_interactor(
        current_user_id=TEST_USER_ID,
        update_locale_dto=UpdateLocaleRequestDTO(locale="ru"),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.id == TEST_USER_ID
    assert stored.email == Email("user@example.com")
    assert stored.hashed_password == "hash"
    assert stored.is_active is True
    assert stored.time_format == TimeFormat.TWELVE_HOUR


@pytest.mark.asyncio
@pytest.mark.parametrize("locale", ["de", "EN", ""])
async def test_update_locale_invalid(
    update_locale_interactor,
    mock_user_gateway,
    locale,
):
    with pytest.raises(InvalidLocaleError) as exc_info:
        await update_locale_interactor(
            current_user_id=TEST_USER_ID,
            update_locale_dto=UpdateLocaleRequestDTO(locale=locale),
        )
    assert exc_info.value.code == "invalid_locale"
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_locale_user_not_found(
    update_locale_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await update_locale_interactor(
            current_user_id=TEST_USER_ID,
            update_locale_dto=UpdateLocaleRequestDTO(locale="ru"),
        )
    mock_user_gateway.update_user.assert_not_called()

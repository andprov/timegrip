from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.exceptions import (
    InvalidTimeFormatError,
    UserNotFoundError,
)
from timegrip.application.user.update_time_format import (
    UpdateTimeFormatInteractor,
    UpdateTimeFormatRequestDTO,
)
from timegrip.entities.user import Email, Locale, TimeFormat, User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_user(**overrides):
    defaults = {
        "id": TEST_USER_ID,
        "email": Email("user@example.com"),
        "hashed_password": "hash",
        "is_active": True,
        "time_format": TimeFormat.TWENTY_FOUR_HOUR,
        "locale": Locale.RU,
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
def update_time_format_interactor(mock_user_gateway):
    return UpdateTimeFormatInteractor(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
@pytest.mark.parametrize("time_format", [tf.value for tf in TimeFormat])
async def test_update_time_format_success(
    update_time_format_interactor,
    mock_user_gateway,
    time_format,
):
    result = await update_time_format_interactor(
        current_user_id=TEST_USER_ID,
        update_time_format_dto=UpdateTimeFormatRequestDTO(
            time_format=time_format,
        ),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.time_format == TimeFormat(time_format)
    assert result.time_format == TimeFormat(time_format)


@pytest.mark.asyncio
async def test_update_time_format_keeps_other_user_fields(
    update_time_format_interactor,
    mock_user_gateway,
):
    await update_time_format_interactor(
        current_user_id=TEST_USER_ID,
        update_time_format_dto=UpdateTimeFormatRequestDTO(time_format="12h"),
    )
    stored = mock_user_gateway.update_user.call_args.kwargs["user"]
    assert stored.id == TEST_USER_ID
    assert stored.email == Email("user@example.com")
    assert stored.hashed_password == "hash"
    assert stored.is_active is True
    assert stored.locale == Locale.RU


@pytest.mark.asyncio
@pytest.mark.parametrize("time_format", ["12", "24H", ""])
async def test_update_time_format_invalid(
    update_time_format_interactor,
    mock_user_gateway,
    time_format,
):
    with pytest.raises(InvalidTimeFormatError) as exc_info:
        await update_time_format_interactor(
            current_user_id=TEST_USER_ID,
            update_time_format_dto=UpdateTimeFormatRequestDTO(
                time_format=time_format,
            ),
        )
    assert exc_info.value.code == "invalid_time_format"
    mock_user_gateway.update_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_time_format_user_not_found(
    update_time_format_interactor,
    mock_user_gateway,
):
    mock_user_gateway.get_user_by_id.return_value = None
    with pytest.raises(UserNotFoundError):
        await update_time_format_interactor(
            current_user_id=TEST_USER_ID,
            update_time_format_dto=UpdateTimeFormatRequestDTO(
                time_format="12h",
            ),
        )
    mock_user_gateway.update_user.assert_not_called()

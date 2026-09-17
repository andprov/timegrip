from unittest.mock import AsyncMock

import pytest

from timegrip.application.cleanup.cleanup_unconfirmed_users import (
    CleanupUnconfirmedUsersInteractor,
)


@pytest.fixture
def mock_user_gateway():
    return AsyncMock()


@pytest.fixture
def cleanup_unconfirmed_users_interactor(mock_user_gateway):
    return CleanupUnconfirmedUsersInteractor(user_gateway=mock_user_gateway)


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [0, 3])
async def test_cleanup_deletes_unconfirmed_users(
    cleanup_unconfirmed_users_interactor,
    mock_user_gateway,
    count,
):
    mock_delete = mock_user_gateway.delete_inactive_users_after_grace_period
    mock_delete.return_value = count
    deleted_count = await cleanup_unconfirmed_users_interactor()
    assert deleted_count == count
    mock_delete.assert_called_once_with(grace_period_days=10)

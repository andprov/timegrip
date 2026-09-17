from unittest.mock import AsyncMock

import pytest

from timegrip.application.cleanup.cleanup_refresh_tokens import (
    CleanupRefreshTokensInteractor,
)


@pytest.fixture
def mock_refresh_token_gateway():
    return AsyncMock()


@pytest.fixture
def cleanup_refresh_tokens_interactor(mock_refresh_token_gateway):
    return CleanupRefreshTokensInteractor(
        refresh_token_gateway=mock_refresh_token_gateway,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [0, 7])
async def test_cleanup_deletes_expired_and_old_revoked_tokens(
    cleanup_refresh_tokens_interactor,
    mock_refresh_token_gateway,
    count,
):
    gateway_call = mock_refresh_token_gateway.delete_expired_and_old_revoked
    gateway_call.return_value = count
    deleted_count = await cleanup_refresh_tokens_interactor()
    assert deleted_count == count
    gateway_call.assert_called_once_with(revoked_retention_days=1)

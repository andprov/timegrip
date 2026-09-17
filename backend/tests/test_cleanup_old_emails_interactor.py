from unittest.mock import AsyncMock

import pytest

from timegrip.application.cleanup.cleanup_old_emails import (
    CleanupOldEmailsInteractor,
)


@pytest.fixture
def mock_email_outbox_gateway():
    return AsyncMock()


@pytest.fixture
def cleanup_old_emails_interactor(mock_email_outbox_gateway):
    return CleanupOldEmailsInteractor(
        email_outbox_gateway=mock_email_outbox_gateway,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [0, 5])
async def test_cleanup_deletes_old_emails(
    cleanup_old_emails_interactor,
    mock_email_outbox_gateway,
    count,
):
    mock_email_outbox_gateway.delete_old_emails.return_value = count
    deleted_count = await cleanup_old_emails_interactor()
    assert deleted_count == count
    mock_email_outbox_gateway.delete_old_emails.assert_called_once_with(
        retention_days=10,
    )

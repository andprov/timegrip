from unittest.mock import AsyncMock

import pytest

from timegrip.application.outbox.send_pending_emails import (
    SendPendingEmailsInteractor,
)
from timegrip.entities.outbox_email import OutboxEmail


@pytest.fixture
def mock_email_outbox_gateway():
    return AsyncMock()


@pytest.fixture
def mock_email_sender():
    return AsyncMock()


@pytest.fixture
def send_pending_emails_interactor(
    mock_email_outbox_gateway,
    mock_email_sender,
):
    return SendPendingEmailsInteractor(
        email_outbox_gateway=mock_email_outbox_gateway,
        email_sender=mock_email_sender,
    )


@pytest.mark.asyncio
async def test_send_pending_emails_marks_sent(
    send_pending_emails_interactor,
    mock_email_outbox_gateway,
    mock_email_sender,
):
    outbox_email = OutboxEmail(
        id=1,
        to_email="user@example.com",
        subject="Activate your Timegrip account",
        body="Your activation code is: 123456",
    )
    mock_email_outbox_gateway.fetch_pending.return_value = [outbox_email]
    processed = await send_pending_emails_interactor()
    assert processed == 1
    mock_email_outbox_gateway.fetch_pending.assert_called_once_with(
        limit=10,
        stale_after_minutes=5,
    )
    mock_email_sender.send.assert_called_once_with(
        to_email="user@example.com",
        subject="Activate your Timegrip account",
        body="Your activation code is: 123456",
    )
    mock_email_outbox_gateway.mark_sent.assert_called_once_with(id=1)
    mock_email_outbox_gateway.mark_failed.assert_not_called()


@pytest.mark.asyncio
async def test_send_pending_emails_empty_batch(
    send_pending_emails_interactor,
    mock_email_outbox_gateway,
    mock_email_sender,
):
    mock_email_outbox_gateway.fetch_pending.return_value = []
    processed = await send_pending_emails_interactor()
    assert processed == 0
    mock_email_sender.send.assert_not_called()
    mock_email_outbox_gateway.mark_sent.assert_not_called()
    mock_email_outbox_gateway.mark_failed.assert_not_called()


@pytest.mark.asyncio
async def test_send_pending_emails_continues_after_failure(
    send_pending_emails_interactor,
    mock_email_outbox_gateway,
    mock_email_sender,
):
    mock_email_outbox_gateway.fetch_pending.return_value = [
        OutboxEmail(id=1, to_email="a@example.com", subject="s", body="b"),
        OutboxEmail(id=2, to_email="b@example.com", subject="s", body="b"),
        OutboxEmail(id=3, to_email="c@example.com", subject="s", body="b"),
    ]
    mock_email_sender.send.side_effect = [None, OSError("boom"), None]
    processed = await send_pending_emails_interactor()
    assert processed == 3
    assert mock_email_sender.send.call_count == 3
    assert [
        c.kwargs["id"] for c in mock_email_outbox_gateway.mark_sent.mock_calls
    ] == [1, 3]
    mock_email_outbox_gateway.mark_failed.assert_called_once_with(
        id=2,
        max_attempts=5,
    )

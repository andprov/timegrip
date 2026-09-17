import logging

from timegrip.application.outbox.email_outbox_gateway import (
    EmailOutboxGateway,
)
from timegrip.application.outbox.email_sender_gateway import (
    EmailSenderGateway,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
STALE_PROCESSING_MINUTES = 5
MAX_ATTEMPTS = 5


class SendPendingEmailsInteractor:
    def __init__(
        self,
        email_outbox_gateway: EmailOutboxGateway,
        email_sender: EmailSenderGateway,
    ) -> None:
        self.email_outbox_gateway = email_outbox_gateway
        self.email_sender = email_sender

    async def __call__(self) -> int:
        outbox_emails = await self.email_outbox_gateway.fetch_pending(
            limit=BATCH_SIZE,
            stale_after_minutes=STALE_PROCESSING_MINUTES,
        )
        for outbox_email in outbox_emails:
            try:
                await self.email_sender.send(
                    to_email=outbox_email.to_email,
                    subject=outbox_email.subject,
                    body=outbox_email.body,
                )
            except Exception:
                logger.exception(
                    f"Send email failed | [id: {outbox_email.id}]",
                )
                await self.email_outbox_gateway.mark_failed(
                    id=outbox_email.id,
                    max_attempts=MAX_ATTEMPTS,
                )
            else:
                await self.email_outbox_gateway.mark_sent(id=outbox_email.id)

        return len(outbox_emails)

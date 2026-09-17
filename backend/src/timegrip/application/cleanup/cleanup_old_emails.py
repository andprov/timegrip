import logging

from timegrip.application.outbox.email_outbox_gateway import (
    EmailOutboxGateway,
)

logger = logging.getLogger(__name__)

OUTBOX_RETENTION_DAYS = 10


class CleanupOldEmailsInteractor:
    def __init__(self, email_outbox_gateway: EmailOutboxGateway) -> None:
        self.email_outbox_gateway = email_outbox_gateway

    async def __call__(self) -> int:
        deleted_count = await self.email_outbox_gateway.delete_old_emails(
            retention_days=OUTBOX_RETENTION_DAYS,
        )
        if deleted_count:
            logger.info(f"Cleanup old emails | [count: {deleted_count}]")
        return deleted_count

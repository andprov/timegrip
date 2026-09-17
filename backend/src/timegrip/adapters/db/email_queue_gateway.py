import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import OutboxEmailDBModel
from timegrip.application.outbox.email_queue_gateway import (
    EmailQueueGateway,
)

logger = logging.getLogger(__name__)

OUTBOX_EMAIL_CHANNEL = "outbox_email_channel"


class DatabaseEmailQueueGateway(EmailQueueGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(self, to_email: str, subject: str, body: str) -> None:
        outbox_email = OutboxEmailDBModel(
            to_email=to_email,
            subject=subject,
            body=body,
        )
        self.session.add(outbox_email)
        await self.session.execute(text(f"NOTIFY {OUTBOX_EMAIL_CHANNEL}"))
        await self.session.commit()
        logger.info(f"Enqueue email | [to: {to_email}]")

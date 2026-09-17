import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import OutboxEmailDBModel
from timegrip.application.outbox.email_outbox_gateway import (
    EmailOutboxGateway,
)
from timegrip.entities.outbox_email import OutboxEmail

logger = logging.getLogger(__name__)


class DatabaseEmailOutboxGateway(EmailOutboxGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_pending(
        self,
        limit: int,
        stale_after_minutes: int,
    ) -> list[OutboxEmail]:
        stale_before = datetime.now(UTC) - timedelta(
            minutes=stale_after_minutes,
        )
        stmt = (
            select(OutboxEmailDBModel)
            .where(
                or_(
                    OutboxEmailDBModel.status == "pending",
                    (OutboxEmailDBModel.status == "processing")
                    & (OutboxEmailDBModel.claimed_at < stale_before),
                ),
            )
            .order_by(OutboxEmailDBModel.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.scalars(stmt)
        rows = result.all()
        if not rows:
            return []

        ids = [row.id for row in rows]
        stmt = (
            update(OutboxEmailDBModel)
            .where(OutboxEmailDBModel.id.in_(ids))
            .values(status="processing", claimed_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return [
            OutboxEmail(
                id=row.id,
                to_email=row.to_email,
                subject=row.subject,
                body=row.body,
            )
            for row in rows
        ]

    async def mark_sent(self, id: int) -> None:
        stmt = (
            update(OutboxEmailDBModel)
            .where(OutboxEmailDBModel.id == id)
            .values(status="sent", sent_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Mark email sent | [id: {id}]")

    async def mark_failed(self, id: int, max_attempts: int) -> None:
        outbox_email = await self.session.get(
            entity=OutboxEmailDBModel,
            ident=id,
        )
        if outbox_email is None:
            return

        attempts = outbox_email.attempts + 1
        status = "failed" if attempts >= max_attempts else "pending"
        stmt = (
            update(OutboxEmailDBModel)
            .where(OutboxEmailDBModel.id == id)
            .values(attempts=attempts, status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.warning(
            f"Mark email failed | [id: {id} attempts: {attempts} "
            f"status: {status}]",
        )

    async def delete_old_emails(self, retention_days: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        stmt = (
            delete(OutboxEmailDBModel)
            .where(OutboxEmailDBModel.status.in_(["sent", "failed"]))
            .where(OutboxEmailDBModel.created_at < cutoff)
            .returning(OutboxEmailDBModel.id)
        )
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        await self.session.commit()
        if deleted_ids:
            logger.info(
                f"Delete old outbox emails | [count: {len(deleted_ids)}]",
            )
        return len(deleted_ids)

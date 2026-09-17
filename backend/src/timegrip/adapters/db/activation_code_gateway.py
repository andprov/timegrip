import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import ActivationCodeDBModel
from timegrip.application.user_activation.gateway import (
    ActivationCodeGateway,
)
from timegrip.entities.activation_code import ActivationCode

logger = logging.getLogger(__name__)


class DatabaseActivationCodeGateway(ActivationCodeGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_code(
        self,
        activation_code: ActivationCode,
    ) -> ActivationCode:
        row = ActivationCodeDBModel(
            user_id=activation_code.user_id,
            code=activation_code.code,
            expires_at=activation_code.expires_at,
        )
        self.session.add(row)
        await self.session.commit()
        logger.info(f"Add activation code | [user_id: {row.user_id}]")
        return ActivationCode(
            id=row.id,
            user_id=row.user_id,
            code=row.code,
            expires_at=row.expires_at,
            used_at=row.used_at,
            attempts=row.attempts,
            created_at=row.created_at,
        )

    async def get_latest_code_for_user(
        self,
        user_id: UUID,
    ) -> ActivationCode | None:
        stmt = (
            select(ActivationCodeDBModel)
            .filter_by(user_id=user_id)
            .order_by(ActivationCodeDBModel.id.desc())
            .limit(1)
        )
        result = await self.session.scalars(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return ActivationCode(
            id=row.id,
            user_id=row.user_id,
            code=row.code,
            expires_at=row.expires_at,
            used_at=row.used_at,
            attempts=row.attempts,
            created_at=row.created_at,
        )

    async def increment_attempts(self, id: int) -> None:
        stmt = (
            update(ActivationCodeDBModel)
            .where(ActivationCodeDBModel.id == id)
            .values(
                attempts=ActivationCodeDBModel.attempts + 1,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Increment activation code attempts | [id: {id}]")

    async def mark_code_used(self, id: int) -> None:
        stmt = (
            update(ActivationCodeDBModel)
            .where(ActivationCodeDBModel.id == id)
            .values(used_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Mark activation code used | [id: {id}]")

    async def delete_codes_for_user(self, user_id: UUID) -> None:
        stmt = delete(ActivationCodeDBModel).filter_by(user_id=user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete activation codes | [user_id: {user_id}]")

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import PasswordResetCodeDBModel
from timegrip.application.password_reset.gateway import (
    PasswordResetCodeGateway,
)
from timegrip.entities.password_reset_code import PasswordResetCode

logger = logging.getLogger(__name__)


class DatabasePasswordResetCodeGateway(PasswordResetCodeGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_code(
        self,
        reset_code: PasswordResetCode,
    ) -> PasswordResetCode:
        row = PasswordResetCodeDBModel(
            user_id=reset_code.user_id,
            code=reset_code.code,
            expires_at=reset_code.expires_at,
        )
        self.session.add(row)
        await self.session.commit()
        logger.info(f"Add password reset code | [user_id: {row.user_id}]")
        return PasswordResetCode(
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
    ) -> PasswordResetCode | None:
        stmt = (
            select(PasswordResetCodeDBModel)
            .filter_by(user_id=user_id)
            .order_by(PasswordResetCodeDBModel.id.desc())
            .limit(1)
        )
        result = await self.session.scalars(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return PasswordResetCode(
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
            update(PasswordResetCodeDBModel)
            .where(PasswordResetCodeDBModel.id == id)
            .values(
                attempts=PasswordResetCodeDBModel.attempts + 1,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Increment password reset code attempts | [id: {id}]")

    async def mark_code_used(self, id: int) -> None:
        stmt = (
            update(PasswordResetCodeDBModel)
            .where(PasswordResetCodeDBModel.id == id)
            .values(used_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Mark password reset code used | [id: {id}]")

    async def delete_codes_for_user(self, user_id: UUID) -> None:
        stmt = delete(PasswordResetCodeDBModel).filter_by(user_id=user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete password reset codes | [user_id: {user_id}]")

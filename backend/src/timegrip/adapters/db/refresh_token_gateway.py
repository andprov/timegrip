import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import RefreshTokenDBModel
from timegrip.application.auth.gateway import RefreshTokenGateway
from timegrip.entities.refresh_token import (
    RefreshToken,
    RefreshTokenRevokeReason,
)

logger = logging.getLogger(__name__)


def _to_entity(row: RefreshTokenDBModel) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        family_id=row.family_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        revoke_reason=(
            RefreshTokenRevokeReason(row.revoke_reason)
            if row.revoke_reason is not None
            else None
        ),
        user_agent=row.user_agent,
        ip_address=row.ip_address,
        created_at=row.created_at,
    )


class DatabaseRefreshTokenGateway(RefreshTokenGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_token(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        row = RefreshTokenDBModel(
            user_id=refresh_token.user_id,
            token_hash=refresh_token.token_hash,
            expires_at=refresh_token.expires_at,
            user_agent=refresh_token.user_agent,
            ip_address=refresh_token.ip_address,
        )
        if refresh_token.family_id is not None:
            row.family_id = refresh_token.family_id
        self.session.add(row)
        await self.session.commit()
        logger.info(f"Add refresh token | [user_id: {row.user_id}]")
        return _to_entity(row)

    async def get_token_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        stmt = select(RefreshTokenDBModel).filter_by(token_hash=token_hash)
        result = await self.session.scalars(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return _to_entity(row)

    async def rotate_token(self, id: int) -> None:
        stmt = (
            update(RefreshTokenDBModel)
            .where(RefreshTokenDBModel.id == id)
            .values(
                revoked_at=datetime.now(UTC),
                revoke_reason=RefreshTokenRevokeReason.ROTATED.value,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Rotate refresh token | [id: {id}]")

    async def revoke_family(self, family_id: UUID) -> None:
        stmt = self._revoke_stmt().where(
            RefreshTokenDBModel.family_id == family_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Revoke refresh token family | [family_id: {family_id}]")

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        stmt = self._revoke_stmt().where(
            RefreshTokenDBModel.user_id == user_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Revoke all refresh tokens | [user_id: {user_id}]")

    async def get_active_for_user(
        self,
        user_id: UUID,
    ) -> list[RefreshToken]:
        stmt = (
            select(RefreshTokenDBModel)
            .where(
                RefreshTokenDBModel.user_id == user_id,
                RefreshTokenDBModel.revoked_at.is_(None),
                RefreshTokenDBModel.expires_at > datetime.now(UTC),
            )
            .order_by(RefreshTokenDBModel.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return [_to_entity(row) for row in result.all()]

    async def get_active_token_for_user(
        self,
        id: int,
        user_id: UUID,
    ) -> RefreshToken | None:
        stmt = select(RefreshTokenDBModel).where(
            RefreshTokenDBModel.id == id,
            RefreshTokenDBModel.user_id == user_id,
            RefreshTokenDBModel.revoked_at.is_(None),
        )
        row = await self.session.scalar(stmt)
        if row is None:
            return None

        return _to_entity(row)

    async def delete_expired_and_old_revoked(
        self,
        revoked_retention_days: int,
    ) -> int:
        now = datetime.now(UTC)
        revoked_cutoff = now - timedelta(days=revoked_retention_days)
        stmt = (
            delete(RefreshTokenDBModel)
            .where(
                or_(
                    RefreshTokenDBModel.expires_at < now,
                    RefreshTokenDBModel.revoked_at < revoked_cutoff,
                ),
            )
            .returning(RefreshTokenDBModel.id)
        )
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        await self.session.commit()
        if deleted_ids:
            logger.info(
                f"Delete expired/revoked refresh tokens | "
                f"[count: {len(deleted_ids)}]",
            )
        return len(deleted_ids)

    @staticmethod
    def _revoke_stmt():
        return (
            update(RefreshTokenDBModel)
            .where(
                RefreshTokenDBModel.revoke_reason.is_distinct_from(
                    RefreshTokenRevokeReason.REVOKED.value,
                ),
            )
            .values(
                revoked_at=func.coalesce(
                    RefreshTokenDBModel.revoked_at,
                    datetime.now(UTC),
                ),
                revoke_reason=RefreshTokenRevokeReason.REVOKED.value,
            )
        )

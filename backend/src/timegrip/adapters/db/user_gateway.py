import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import UserDBModel
from timegrip.application.exceptions import UserNotFoundError
from timegrip.application.user.gateway import UserGateway
from timegrip.entities.user import Email, Locale, TimeFormat, User

logger = logging.getLogger(__name__)


class DatabaseUserGateway(UserGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(self, user: User) -> User:
        new_user = UserDBModel(
            email=user.email.value,
            hashed_password=user.hashed_password,
            time_format=user.time_format,
            locale=user.locale,
        )
        self.session.add(new_user)
        await self.session.commit()
        logger.info(f"Add user | [id: {new_user.id}]")
        return User(
            id=new_user.id,
            email=Email(new_user.email),
            hashed_password=new_user.hashed_password,
            is_active=new_user.is_active,
            time_format=TimeFormat(new_user.time_format),
            locale=Locale(new_user.locale),
        )

    async def get_user_by_id(self, id: UUID) -> User | None:
        user = await self.session.get(entity=UserDBModel, ident=id)
        if user is None:
            logger.info(f"Get user by id | [id: {id} Not Found]")
            return None

        logger.info(f"Get user by id | [user: {user}]")
        return User(
            id=user.id,
            email=Email(user.email),
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            time_format=TimeFormat(user.time_format),
            locale=Locale(user.locale),
        )

    async def get_user_by_email(self, email: Email) -> User | None:
        stmt = select(UserDBModel).filter_by(email=email.value)
        result = await self.session.scalars(stmt)
        user = result.one_or_none()
        if user is None:
            logger.info(f"Get user by email | [email: {email} Not Found]")
            return None

        logger.info(f"Get user by email | [user: {user}]")
        return User(
            id=user.id,
            email=Email(user.email),
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            time_format=TimeFormat(user.time_format),
            locale=Locale(user.locale),
        )

    async def activate_user(self, id: UUID) -> None:
        stmt = (
            update(UserDBModel)
            .where(UserDBModel.id == id)
            .values(is_active=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Activate user | [id: {id}]")

    async def update_user(self, user: User) -> User:
        stmt = (
            update(UserDBModel)
            .where(UserDBModel.id == user.id)
            .values(
                email=user.email.value,
                hashed_password=user.hashed_password,
                time_format=user.time_format,
                locale=user.locale,
            )
            .returning(UserDBModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        try:
            updated_user = result.scalar_one()
        except NoResultFound:
            logger.warning(f"Update user | [id: {user.id} Not Found]")
            raise UserNotFoundError(
                f"User with id {user.id} not found",
            ) from None

        logger.info(f"Update user | [user_id: {updated_user.id}]")
        return User(
            id=updated_user.id,
            email=Email(updated_user.email),
            hashed_password=updated_user.hashed_password,
            is_active=updated_user.is_active,
            time_format=TimeFormat(updated_user.time_format),
            locale=Locale(updated_user.locale),
        )

    async def delete_user(self, id: UUID) -> None:
        stmt = delete(UserDBModel).filter_by(id=id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete user | [user_id: {id}]")

    async def delete_inactive_users_after_grace_period(
        self,
        grace_period_days: int,
    ) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=grace_period_days)
        stmt = (
            delete(UserDBModel)
            .where(UserDBModel.is_active.is_(False))
            .where(UserDBModel.created_at < cutoff)
            .returning(UserDBModel.id)
        )
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        await self.session.commit()
        if deleted_ids:
            logger.info(f"Delete unconfirmed users | [ids: {deleted_ids}]")
        return len(deleted_ids)

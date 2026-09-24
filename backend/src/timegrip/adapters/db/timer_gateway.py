import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from timegrip.adapters.db.db_tables import ProjectDBModel, TimerDBModel
from timegrip.application.exceptions import TimerNotFoundError
from timegrip.application.timer.gateway import TimerGateway
from timegrip.entities.project import ProjectStatus
from timegrip.entities.timer import Timer

logger = logging.getLogger(__name__)


class DatabaseTimerGateway(TimerGateway):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _build_filter_conditions(
        self,
        user_id: UUID,
        project_ids: list[UUID] | None,
        date_from: datetime | None,
        date_to: datetime | None,
        billable: bool | None,
        include_archived_projects: bool = False,
    ) -> list:
        conditions = [TimerDBModel.user_id == user_id]
        if project_ids:
            conditions.append(TimerDBModel.project_id.in_(project_ids))
        if date_from is not None:
            conditions.append(TimerDBModel.start_time >= date_from)
        if date_to is not None:
            conditions.append(TimerDBModel.start_time <= date_to)
        if billable is True:
            conditions.append(TimerDBModel.hourly_rate.is_not(None))
        elif billable is False:
            conditions.append(TimerDBModel.hourly_rate.is_(None))
        if not include_archived_projects:
            conditions.append(
                TimerDBModel.project_id.in_(
                    select(ProjectDBModel.id).where(
                        ProjectDBModel.status == ProjectStatus.ACTIVE.value,
                    ),
                ),
            )
        return conditions

    async def add_timer(self, timer: Timer) -> Timer:
        new_timer = TimerDBModel(
            user_id=timer.user_id,
            project_id=timer.project_id,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
        )
        if timer.start_time is not None:
            new_timer.start_time = timer.start_time
        self.session.add(new_timer)
        await self.session.commit()
        logger.info(f"Add timer | [id: {new_timer.id}]")
        return Timer(
            id=new_timer.id,
            start_time=new_timer.start_time,
            end_time=new_timer.end_time,
            duration=new_timer.duration,
            hourly_rate=new_timer.hourly_rate,
            round_to_hour=new_timer.round_to_hour,
            billable_amount=new_timer.billable_amount,
            user_id=new_timer.user_id,
            project_id=new_timer.project_id,
        )

    async def add_manual_timer(self, timer: Timer) -> Timer:
        new_timer = TimerDBModel(
            user_id=timer.user_id,
            project_id=timer.project_id,
            start_time=timer.start_time,
            end_time=timer.end_time,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            billable_amount=timer.billable_amount,
        )
        self.session.add(new_timer)
        await self.session.flush()
        await self.session.refresh(new_timer)
        added_timer = Timer(
            id=new_timer.id,
            start_time=new_timer.start_time,
            end_time=new_timer.end_time,
            duration=new_timer.duration,
            hourly_rate=new_timer.hourly_rate,
            round_to_hour=new_timer.round_to_hour,
            billable_amount=new_timer.billable_amount,
            user_id=new_timer.user_id,
            project_id=new_timer.project_id,
        )
        await self.session.commit()
        logger.info(f"Add manual timer | [id: {added_timer.id}]")
        return added_timer

    async def get_all_user_timers(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
        project_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        billable: bool | None = None,
        include_archived_projects: bool = False,
    ) -> list[Timer]:
        conditions = self._build_filter_conditions(
            user_id=user_id,
            project_ids=project_ids,
            date_from=date_from,
            date_to=date_to,
            billable=billable,
            include_archived_projects=include_archived_projects,
        )
        stmt = (
            select(TimerDBModel)
            .where(*conditions)
            .order_by(TimerDBModel.start_time.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        timers = result.all()
        logger.info(
            f"Get all timers | "
            f"[count: {len(timers)}, offset: {offset}, page_size: {limit}]",
        )
        return [
            Timer(
                id=timer.id,
                start_time=timer.start_time,
                end_time=timer.end_time,
                duration=timer.duration,
                hourly_rate=timer.hourly_rate,
                round_to_hour=timer.round_to_hour,
                billable_amount=timer.billable_amount,
                user_id=timer.user_id,
                project_id=timer.project_id,
            )
            for timer in timers
        ]

    async def count_user_timers(
        self,
        user_id: UUID,
        project_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        billable: bool | None = None,
        include_archived_projects: bool = False,
    ) -> int:
        conditions = self._build_filter_conditions(
            user_id=user_id,
            project_ids=project_ids,
            date_from=date_from,
            date_to=date_to,
            billable=billable,
            include_archived_projects=include_archived_projects,
        )
        stmt = (
            select(func.count()).select_from(TimerDBModel).where(*conditions)
        )
        total = await self.session.scalar(stmt)
        logger.info(f"Count timers | [user_id: {user_id}, total: {total}]")
        return total or 0

    async def get_timer_by_id(self, id: UUID) -> Timer | None:
        timer = await self.session.get(entity=TimerDBModel, ident=id)
        if timer is None:
            logger.info(f"Get timer by id | [id: {id} Not Found]")
            return None

        logger.info(f"Get timer by id | [timer: {timer}]")
        return Timer(
            id=timer.id,
            start_time=timer.start_time,
            end_time=timer.end_time,
            duration=timer.duration,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            billable_amount=timer.billable_amount,
            user_id=timer.user_id,
            project_id=timer.project_id,
        )

    async def get_timers_by_ids(self, ids: list[UUID]) -> list[Timer]:
        stmt = select(TimerDBModel).where(TimerDBModel.id.in_(ids))
        result = await self.session.scalars(stmt)
        timers = result.all()
        logger.info(f"Get timers by ids | [count: {len(timers)}]")
        return [
            Timer(
                id=timer.id,
                start_time=timer.start_time,
                end_time=timer.end_time,
                duration=timer.duration,
                hourly_rate=timer.hourly_rate,
                round_to_hour=timer.round_to_hour,
                billable_amount=timer.billable_amount,
                user_id=timer.user_id,
                project_id=timer.project_id,
            )
            for timer in timers
        ]

    async def get_running_timer_by_user(
        self,
        user_id: UUID,
    ) -> Timer | None:
        stmt = select(TimerDBModel).where(
            TimerDBModel.user_id == user_id,
            TimerDBModel.end_time.is_(None),
        )
        timer = await self.session.scalar(stmt)
        if timer is None:
            logger.info(
                f"Get running timer | [user_id: {user_id} Not Found]",
            )
            return None

        logger.info(f"Get running timer | [timer: {timer}]")
        return Timer(
            id=timer.id,
            start_time=timer.start_time,
            end_time=timer.end_time,
            duration=timer.duration,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            billable_amount=timer.billable_amount,
            user_id=timer.user_id,
            project_id=timer.project_id,
        )

    async def stop_timer(
        self,
        id: UUID,
        end_time: datetime,
        billable_amount: Decimal | None,
    ) -> Timer:
        stmt = (
            update(TimerDBModel)
            .where(TimerDBModel.id == id)
            .values(
                end_time=end_time,
                billable_amount=billable_amount,
            )
            .returning(TimerDBModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        try:
            stopped_timer = result.scalar_one()
        except NoResultFound:
            logger.warning(f"Stop timer | [id: {id} Not Found]")
            raise TimerNotFoundError(f"Timer with id {id} not found") from None

        logger.info(f"Stop timer | [timer_id: {stopped_timer.id}]")
        return Timer(
            id=stopped_timer.id,
            start_time=stopped_timer.start_time,
            end_time=stopped_timer.end_time,
            duration=stopped_timer.duration,
            hourly_rate=stopped_timer.hourly_rate,
            round_to_hour=stopped_timer.round_to_hour,
            billable_amount=stopped_timer.billable_amount,
            user_id=stopped_timer.user_id,
            project_id=stopped_timer.project_id,
        )

    async def update_timer(self, timer: Timer) -> Timer:
        stmt = (
            update(TimerDBModel)
            .where(TimerDBModel.id == timer.id)
            .values(
                project_id=timer.project_id,
                start_time=timer.start_time,
                end_time=timer.end_time,
                hourly_rate=timer.hourly_rate,
                round_to_hour=timer.round_to_hour,
                billable_amount=timer.billable_amount,
            )
            .returning(TimerDBModel)
        )
        result = await self.session.execute(stmt)
        try:
            updated_row = result.scalar_one()
        except NoResultFound:
            logger.warning(f"Update timer | [id: {timer.id} Not Found]")
            raise TimerNotFoundError(
                f"Timer with id {timer.id} not found",
            ) from None

        updated_timer = Timer(
            id=updated_row.id,
            start_time=updated_row.start_time,
            end_time=updated_row.end_time,
            duration=updated_row.duration,
            hourly_rate=updated_row.hourly_rate,
            round_to_hour=updated_row.round_to_hour,
            billable_amount=updated_row.billable_amount,
            user_id=updated_row.user_id,
            project_id=updated_row.project_id,
        )
        await self.session.commit()
        logger.info(f"Update timer | [timer_id: {updated_timer.id}]")
        return updated_timer

    async def delete_timer(self, id: UUID) -> None:
        stmt = delete(TimerDBModel).filter_by(id=id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete timer | [timer_id: {id}]")

    async def delete_timers(self, ids: list[UUID]) -> None:
        stmt = delete(TimerDBModel).where(TimerDBModel.id.in_(ids))
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Delete timers | [count: {len(ids)}]")

    async def has_overlapping_timer(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime | None,
        exclude_id: UUID | None = None,
    ) -> bool:
        conditions = [
            TimerDBModel.user_id == user_id,
            or_(
                TimerDBModel.end_time.is_(None),
                TimerDBModel.end_time > start_time,
            ),
        ]
        if end_time is not None:
            conditions.append(TimerDBModel.start_time < end_time)

        if exclude_id is not None:
            conditions.append(TimerDBModel.id != exclude_id)

        stmt = select(TimerDBModel.id).where(*conditions).limit(1)
        result = await self.session.scalar(stmt)
        return result is not None

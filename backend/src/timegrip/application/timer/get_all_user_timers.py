from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.pagination import Page, paginate
from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.timer.gateway import TimerGateway


@dataclass
class GetTimersResponseDTO:
    id: UUID
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID


class GetAllUserTimersInteractor:
    def __init__(
        self,
        timer_gateway: TimerGateway,
        permission_gateway: PermissionGateway,
    ) -> None:
        self.timer_gateway = timer_gateway
        self.permission_gateway = permission_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        page: int,
        page_size: int,
        project_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        billable: bool | None = None,
        include_archived_projects: bool = False,
    ) -> Page[GetTimersResponseDTO]:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        pagination = paginate(page=page, page_size=page_size)
        timers = await self.timer_gateway.get_all_user_timers(
            user_id=current_user_id,
            offset=pagination.offset,
            limit=pagination.limit,
            project_ids=project_ids,
            date_from=date_from,
            date_to=date_to,
            billable=billable,
            include_archived_projects=include_archived_projects,
        )
        total = await self.timer_gateway.count_user_timers(
            user_id=current_user_id,
            project_ids=project_ids,
            date_from=date_from,
            date_to=date_to,
            billable=billable,
            include_archived_projects=include_archived_projects,
        )
        items = [
            GetTimersResponseDTO(
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
        return Page(items=items, total=total)

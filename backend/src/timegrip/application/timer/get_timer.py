import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import TimerNotFoundError
from timegrip.application.timer.gateway import TimerGateway

logger = logging.getLogger(__name__)


@dataclass
class GetTimerResponseDTO:
    id: UUID
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID


class GetTimerByIdInteractor:
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
        timer_id: UUID,
    ) -> GetTimerResponseDTO:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        timer = await self.timer_gateway.get_timer_by_id(id=timer_id)
        if timer is None:
            logger.warning(f"Timer with id {timer_id} not found")
            raise TimerNotFoundError(f"Timer with id {timer_id} not found")

        if timer.user_id != current_user_id:
            logger.warning(
                f"User with id {current_user_id} does not have access to "
                f"timer with id {timer_id}",
            )
            raise TimerNotFoundError(f"Timer with id {timer_id} not found")

        return GetTimerResponseDTO(
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

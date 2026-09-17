import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import TimerNotRunningError
from timegrip.application.timer.billing import calculate_billable_amount
from timegrip.application.timer.gateway import TimerGateway

logger = logging.getLogger(__name__)


@dataclass
class StopTimerResponseDTO:
    id: UUID
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID


class StopTimerInteractor:
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
    ) -> StopTimerResponseDTO:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        running_timer = await self.timer_gateway.get_running_timer_by_user(
            user_id=current_user_id,
        )
        if running_timer is None:
            logger.warning(
                f"User with id {current_user_id} has no running timer",
            )
            raise TimerNotRunningError("No running timer")

        end_time = datetime.now(UTC)
        duration = end_time - running_timer.start_time
        billable_amount = calculate_billable_amount(
            duration=duration,
            hourly_rate=running_timer.hourly_rate,
            round_to_hour=running_timer.round_to_hour,
        )

        timer = await self.timer_gateway.stop_timer(
            id=running_timer.id,
            end_time=end_time,
            billable_amount=billable_amount,
        )
        return StopTimerResponseDTO(
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

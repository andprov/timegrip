from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.timer.gateway import TimerGateway


@dataclass
class GetRunningTimerResponseDTO:
    id: UUID
    start_time: datetime
    hourly_rate: Decimal | None
    round_to_hour: bool
    user_id: UUID
    project_id: UUID


class GetRunningTimerInteractor:
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
    ) -> GetRunningTimerResponseDTO | None:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        timer = await self.timer_gateway.get_running_timer_by_user(
            user_id=current_user_id,
        )
        if timer is None:
            return None

        return GetRunningTimerResponseDTO(
            id=timer.id,
            start_time=timer.start_time,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            user_id=timer.user_id,
            project_id=timer.project_id,
        )

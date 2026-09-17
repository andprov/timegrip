import logging
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    TimerNotFoundError,
    TimerRunningError,
)
from timegrip.application.timer.gateway import TimerGateway

logger = logging.getLogger(__name__)


class BulkDeleteTimerInteractor:
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
        timer_ids: list[UUID],
    ) -> None:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        timers = await self.timer_gateway.get_timers_by_ids(ids=timer_ids)
        timers_by_id = {timer.id: timer for timer in timers}
        for timer_id in timer_ids:
            timer = timers_by_id.get(timer_id)
            if timer is None:
                logger.warning(f"Timer with id {timer_id} not found")
                raise TimerNotFoundError(
                    f"Timer with id {timer_id} not found",
                )

            if timer.user_id != current_user_id:
                logger.warning(
                    f"User with id {current_user_id} does not have access "
                    f"to timer with id {timer_id}",
                )
                raise TimerNotFoundError(
                    f"Timer with id {timer_id} not found",
                )

            if timer.end_time is None:
                logger.warning(
                    f"User with id {current_user_id} tried to delete "
                    f"running timer with id {timer_id}",
                )
                raise TimerRunningError(
                    "Timer is running, stop it before deleting",
                )

        await self.timer_gateway.delete_timers(ids=timer_ids)

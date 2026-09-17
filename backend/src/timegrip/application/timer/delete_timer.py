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


class DeleteTimerInteractor:
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
    ) -> None:
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

        if timer.end_time is None:
            logger.warning(
                f"User with id {current_user_id} tried to delete running "
                f"timer with id {timer_id}",
            )
            raise TimerRunningError(
                "Timer is running, stop it before deleting",
            )

        await self.timer_gateway.delete_timer(id=timer_id)

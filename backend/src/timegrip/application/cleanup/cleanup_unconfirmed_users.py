import logging

from timegrip.application.user.gateway import UserGateway

logger = logging.getLogger(__name__)

UNCONFIRMED_USER_GRACE_PERIOD_DAYS = 10


class CleanupUnconfirmedUsersInteractor:
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def __call__(self) -> int:
        deleted_count = (
            await self.user_gateway.delete_inactive_users_after_grace_period(
                grace_period_days=UNCONFIRMED_USER_GRACE_PERIOD_DAYS,
            )
        )
        if deleted_count:
            logger.info(
                f"Cleanup unconfirmed users | [count: {deleted_count}]",
            )
        return deleted_count

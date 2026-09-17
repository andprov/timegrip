import logging
from uuid import UUID

from timegrip.application.exceptions import UserNotFoundError
from timegrip.application.user.gateway import UserGateway

logger = logging.getLogger(__name__)


class DeleteUserInteractor:
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def __call__(self, current_user_id: UUID) -> None:
        user = await self.user_gateway.get_user_by_id(id=current_user_id)
        if user is None:
            logger.warning(f"User with id {current_user_id} not found")
            raise UserNotFoundError(
                f"User with id {current_user_id} not found",
            )

        await self.user_gateway.delete_user(id=current_user_id)

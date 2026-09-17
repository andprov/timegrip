import logging
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    AccessDeniedError,
    UserNotFoundError,
)
from timegrip.application.user.gateway import UserGateway

logger = logging.getLogger(__name__)


class PermissionManager(PermissionGateway):
    def __init__(self, user_gateway: UserGateway) -> None:
        self.user_gateway = user_gateway

    async def check_permission(self, user_id: UUID) -> None:
        user = await self.user_gateway.get_user_by_id(id=user_id)
        if user is None:
            logger.warning(f"User with id {user_id} not found")
            raise UserNotFoundError(f"User with id {user_id} not found")

        if not user.is_active:
            logger.warning(f"User with id {user_id} access denied")
            raise AccessDeniedError("Access denied")

import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import ProjectNotFoundError
from timegrip.application.project.gateway import ProjectGateway

logger = logging.getLogger(__name__)


@dataclass
class GetProjectResponseDTO:
    id: UUID
    name: str
    color: str
    hourly_rate: Decimal | None
    round_to_hour: bool
    status: str
    user_id: UUID


class GetProjectByIdInteractor:
    def __init__(
        self,
        project_gateway: ProjectGateway,
        permission_gateway: PermissionGateway,
    ) -> None:
        self.project_gateway = project_gateway
        self.permission_gateway = permission_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        project_id: UUID,
    ) -> GetProjectResponseDTO:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        project = await self.project_gateway.get_project_by_id(id=project_id)
        if project is None:
            logger.warning(f"Project with id {project_id} not found")
            raise ProjectNotFoundError(
                f"Project with id {project_id} not found",
            )

        if project.user_id != current_user_id:
            logger.warning(
                f"User with id {current_user_id} does not have access to "
                f"project with id {project_id}",
            )
            raise ProjectNotFoundError(
                f"Project with id {project_id} not found",
            )

        return GetProjectResponseDTO(
            id=project.id,
            name=project.name,
            color=project.color,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            status=project.status,
            user_id=project.user_id,
        )

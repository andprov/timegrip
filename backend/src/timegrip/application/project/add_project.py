import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import InvalidProjectColorError
from timegrip.application.project.gateway import ProjectGateway
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

logger = logging.getLogger(__name__)


@dataclass
class AddProjectRequestDTO:
    name: str
    user_id: UUID
    color: str | None = None
    hourly_rate: Decimal | None = None
    round_to_hour: bool = False


@dataclass
class AddProjectResponseDTO:
    id: UUID
    name: str
    color: str
    hourly_rate: Decimal | None
    round_to_hour: bool
    status: str
    user_id: UUID


class AddProjectInteractor:
    def __init__(
        self,
        project_gateway: ProjectGateway,
        permission_gateway: PermissionGateway,
    ) -> None:
        self.project_gateway = project_gateway
        self.permission_gateway = permission_gateway

    async def __call__(
        self,
        add_project_dto: AddProjectRequestDTO,
    ) -> AddProjectResponseDTO:
        await self.permission_gateway.check_permission(
            user_id=add_project_dto.user_id,
        )

        color = ProjectColor.GRAY
        if add_project_dto.color is not None:
            try:
                color = ProjectColor(add_project_dto.color)
            except ValueError:
                logger.warning(
                    f"User with id {add_project_dto.user_id} tried to add "
                    f"a project with an invalid color "
                    f"[color: {add_project_dto.color}]",
                )
                raise InvalidProjectColorError(
                    f"Color must be one of "
                    f"{', '.join(c.value for c in ProjectColor)}",
                ) from None

        new_project = Project(
            id=None,
            name=add_project_dto.name,
            color=color,
            hourly_rate=add_project_dto.hourly_rate,
            round_to_hour=add_project_dto.round_to_hour,
            status=ProjectStatus.ACTIVE,
            user_id=add_project_dto.user_id,
            created_at=None,
        )
        project = await self.project_gateway.add_project(project=new_project)
        return AddProjectResponseDTO(
            id=project.id,
            name=project.name,
            color=project.color,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            status=project.status,
            user_id=project.user_id,
        )

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.pagination import Page, paginate
from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.project.gateway import ProjectGateway


@dataclass
class GetProjectsResponseDTO:
    id: UUID
    name: str
    color: str
    hourly_rate: Decimal | None
    round_to_hour: bool
    status: str


class GetAllUserProjectsInteractor:
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
        page: int,
        page_size: int,
    ) -> Page[GetProjectsResponseDTO]:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        pagination = paginate(page=page, page_size=page_size)
        projects = await self.project_gateway.get_all_user_projects(
            user_id=current_user_id,
            offset=pagination.offset,
            limit=pagination.limit,
        )
        total = await self.project_gateway.count_user_projects(
            user_id=current_user_id,
        )
        items = [
            GetProjectsResponseDTO(
                id=project.id,
                name=project.name,
                color=project.color,
                hourly_rate=project.hourly_rate,
                round_to_hour=project.round_to_hour,
                status=project.status,
            )
            for project in projects
        ]
        return Page(items=items, total=total)

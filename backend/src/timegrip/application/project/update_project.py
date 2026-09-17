import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    InvalidProjectColorError,
    InvalidProjectStatusError,
    ProjectHasRunningTimerError,
    ProjectNotFoundError,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.gateway import TimerGateway
from timegrip.entities.project import Project, ProjectColor, ProjectStatus

logger = logging.getLogger(__name__)


@dataclass
class UpdateProjectRequestDTO:
    id: UUID
    name: str | None = None
    color: str | None = None
    hourly_rate: Decimal | None = None
    hourly_rate_set: bool = False
    round_to_hour: bool | None = None
    status: str | None = None


@dataclass
class UpdateProjectResponseDTO:
    id: UUID
    name: str
    color: str
    hourly_rate: Decimal | None
    round_to_hour: bool
    status: str
    user_id: UUID


class UpdateProjectInteractor:
    def __init__(
        self,
        project_gateway: ProjectGateway,
        timer_gateway: TimerGateway,
        permission_gateway: PermissionGateway,
    ) -> None:
        self.project_gateway = project_gateway
        self.timer_gateway = timer_gateway
        self.permission_gateway = permission_gateway

    async def __call__(
        self,
        current_user_id: UUID,
        update_project_dto: UpdateProjectRequestDTO,
    ) -> UpdateProjectResponseDTO:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        existing_project = await self.project_gateway.get_project_by_id(
            id=update_project_dto.id,
        )
        if existing_project is None:
            logger.warning(
                f"Project with id {update_project_dto.id} not found",
            )
            raise ProjectNotFoundError(
                f"Project with id {update_project_dto.id} not found",
            )

        if existing_project.user_id != current_user_id:
            logger.warning(
                f"User with id {current_user_id} does not have access to "
                f"project with id {update_project_dto.id}",
            )
            raise ProjectNotFoundError(
                f"Project with id {update_project_dto.id} not found",
            )

        color = existing_project.color
        if update_project_dto.color is not None:
            try:
                color = ProjectColor(update_project_dto.color)
            except ValueError:
                logger.warning(
                    f"User with id {current_user_id} tried to update "
                    f"project with id {update_project_dto.id} to an "
                    f"invalid color [color: {update_project_dto.color}]",
                )
                raise InvalidProjectColorError(
                    f"Color must be one of "
                    f"{', '.join(c.value for c in ProjectColor)}",
                ) from None

        status = existing_project.status
        if update_project_dto.status is not None:
            try:
                status = ProjectStatus(update_project_dto.status)
            except ValueError:
                logger.warning(
                    f"User with id {current_user_id} tried to update "
                    f"project with id {update_project_dto.id} to an "
                    f"invalid status [status: {update_project_dto.status}]",
                )
                raise InvalidProjectStatusError(
                    f"Status must be one of "
                    f"{', '.join(s.value for s in ProjectStatus)}",
                ) from None

        if (
            status == ProjectStatus.ARCHIVED
            and existing_project.status != ProjectStatus.ARCHIVED
        ):
            running_timer = await self.timer_gateway.get_running_timer_by_user(
                user_id=current_user_id,
            )
            if (
                running_timer is not None
                and running_timer.project_id == existing_project.id
            ):
                logger.warning(
                    f"User with id {current_user_id} tried to archive "
                    f"project with id {update_project_dto.id} while its "
                    f"timer is running [timer_id: {running_timer.id}]",
                )
                raise ProjectHasRunningTimerError(
                    "Cannot archive a project with a running timer",
                )

        hourly_rate = (
            update_project_dto.hourly_rate
            if update_project_dto.hourly_rate_set
            else existing_project.hourly_rate
        )
        round_to_hour = self._coalesce(
            new_value=update_project_dto.round_to_hour,
            old_value=existing_project.round_to_hour,
        )

        new_project = Project(
            id=existing_project.id,
            name=self._coalesce(
                new_value=update_project_dto.name,
                old_value=existing_project.name,
            ),
            color=color,
            hourly_rate=hourly_rate,
            round_to_hour=round_to_hour,
            status=status,
            user_id=existing_project.user_id,
            created_at=existing_project.created_at,
        )
        project = await self.project_gateway.update_project(
            project=new_project,
        )
        return UpdateProjectResponseDTO(
            id=project.id,
            name=project.name,
            color=project.color,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            status=project.status,
            user_id=project.user_id,
        )

    @staticmethod
    def _coalesce(new_value: Any, old_value: Any) -> Any:
        return new_value if new_value is not None else old_value

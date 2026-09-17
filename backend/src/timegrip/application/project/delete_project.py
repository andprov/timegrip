import logging
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    ProjectHasRunningTimerError,
    ProjectNotFoundError,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.gateway import TimerGateway

logger = logging.getLogger(__name__)


class DeleteProjectInteractor:
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
        project_id: UUID,
    ) -> None:
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

        running_timer = await self.timer_gateway.get_running_timer_by_user(
            user_id=current_user_id,
        )
        if (
            running_timer is not None
            and running_timer.project_id == project_id
        ):
            logger.warning(
                f"User with id {current_user_id} tried to delete project "
                f"with id {project_id} while its timer is running "
                f"[timer_id: {running_timer.id}]",
            )
            raise ProjectHasRunningTimerError(
                "Cannot delete a project with a running timer",
            )

        await self.project_gateway.delete_project(id=project_id)

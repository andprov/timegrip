import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerAlreadyRunningError,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.gateway import TimerGateway
from timegrip.entities.project import ProjectStatus
from timegrip.entities.timer import Timer

logger = logging.getLogger(__name__)


@dataclass
class StartTimerRequestDTO:
    project_id: UUID
    user_id: UUID


@dataclass
class StartTimerResponseDTO:
    id: UUID
    start_time: datetime
    hourly_rate: Decimal | None
    round_to_hour: bool
    user_id: UUID
    project_id: UUID


class StartTimerInteractor:
    def __init__(
        self,
        timer_gateway: TimerGateway,
        project_gateway: ProjectGateway,
        permission_gateway: PermissionGateway,
    ) -> None:
        self.timer_gateway = timer_gateway
        self.project_gateway = project_gateway
        self.permission_gateway = permission_gateway

    async def __call__(
        self,
        start_timer_dto: StartTimerRequestDTO,
    ) -> StartTimerResponseDTO:
        await self.permission_gateway.check_permission(
            user_id=start_timer_dto.user_id,
        )

        project = await self.project_gateway.get_project_by_id(
            id=start_timer_dto.project_id,
        )
        if project is None:
            logger.warning(
                f"Project with id {start_timer_dto.project_id} not found",
            )
            raise ProjectNotFoundError(
                f"Project with id {start_timer_dto.project_id} not found",
            )

        if project.user_id != start_timer_dto.user_id:
            logger.warning(
                f"User with id {start_timer_dto.user_id} does not have "
                f"access to project with id {start_timer_dto.project_id}",
            )
            raise ProjectNotFoundError(
                f"Project with id {start_timer_dto.project_id} not found",
            )

        if project.status == ProjectStatus.ARCHIVED:
            logger.warning(
                f"User with id {start_timer_dto.user_id} tried to start a "
                f"timer for archived project with id "
                f"{start_timer_dto.project_id}",
            )
            raise ProjectArchivedError(
                "Cannot start a timer for an archived project",
            )

        running_timer = await self.timer_gateway.get_running_timer_by_user(
            user_id=start_timer_dto.user_id,
        )
        if running_timer is not None:
            logger.warning(
                f"User with id {start_timer_dto.user_id} already has a "
                f"running timer [id: {running_timer.id}]",
            )
            raise TimerAlreadyRunningError("A timer is already running")

        new_timer = Timer(
            id=None,
            start_time=None,
            end_time=None,
            duration=None,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            billable_amount=None,
            user_id=start_timer_dto.user_id,
            project_id=start_timer_dto.project_id,
        )
        timer = await self.timer_gateway.add_timer(timer=new_timer)
        return StartTimerResponseDTO(
            id=timer.id,
            start_time=timer.start_time,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            user_id=timer.user_id,
            project_id=timer.project_id,
        )

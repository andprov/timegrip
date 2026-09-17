import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerOverlapError,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.billing import calculate_billable_amount
from timegrip.application.timer.gateway import TimerGateway
from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.project import ProjectStatus
from timegrip.entities.timer import Timer, validate_timer_range

logger = logging.getLogger(__name__)


@dataclass
class AddManualTimerRequestDTO:
    project_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime


@dataclass
class AddManualTimerResponseDTO:
    id: UUID
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID


class AddManualTimerInteractor:
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
        add_timer_dto: AddManualTimerRequestDTO,
    ) -> AddManualTimerResponseDTO:
        await self.permission_gateway.check_permission(
            user_id=add_timer_dto.user_id,
        )

        now = datetime.now(UTC)
        if add_timer_dto.start_time > now:
            logger.warning(
                f"User with id {add_timer_dto.user_id} tried to add a "
                "timer with a start time in the future",
            )
            raise InvalidTimerRangeError(
                message="Start time must not be in the future",
                code="start_time_in_future",
            )

        if add_timer_dto.end_time > now:
            logger.warning(
                f"User with id {add_timer_dto.user_id} tried to add a "
                "timer with an end time in the future",
            )
            raise InvalidTimerRangeError(
                message="End time must not be in the future",
                code="end_time_in_future",
            )

        validate_timer_range(
            start_time=add_timer_dto.start_time,
            end_time=add_timer_dto.end_time,
        )

        project = await self.project_gateway.get_project_by_id(
            id=add_timer_dto.project_id,
        )
        if project is None:
            logger.warning(
                f"Project with id {add_timer_dto.project_id} not found",
            )
            raise ProjectNotFoundError(
                f"Project with id {add_timer_dto.project_id} not found",
            )

        if project.user_id != add_timer_dto.user_id:
            logger.warning(
                f"User with id {add_timer_dto.user_id} does not have "
                f"access to project with id {add_timer_dto.project_id}",
            )
            raise ProjectNotFoundError(
                f"Project with id {add_timer_dto.project_id} not found",
            )

        if project.status == ProjectStatus.ARCHIVED:
            logger.warning(
                f"User with id {add_timer_dto.user_id} tried to add a "
                f"time entry for archived project with id "
                f"{add_timer_dto.project_id}",
            )
            raise ProjectArchivedError(
                "Cannot add a time entry for an archived project",
            )

        has_overlap = await self.timer_gateway.has_overlapping_timer(
            user_id=add_timer_dto.user_id,
            start_time=add_timer_dto.start_time,
            end_time=add_timer_dto.end_time,
        )
        if has_overlap:
            logger.warning(
                f"User with id {add_timer_dto.user_id} tried to add a "
                "timer that overlaps with an existing one",
            )
            raise TimerOverlapError(
                "Timer overlaps with an existing time entry",
            )

        duration = add_timer_dto.end_time - add_timer_dto.start_time
        billable_amount = calculate_billable_amount(
            duration=duration,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
        )

        new_timer = Timer(
            id=None,
            start_time=add_timer_dto.start_time,
            end_time=add_timer_dto.end_time,
            duration=None,
            hourly_rate=project.hourly_rate,
            round_to_hour=project.round_to_hour,
            billable_amount=billable_amount,
            user_id=add_timer_dto.user_id,
            project_id=add_timer_dto.project_id,
        )
        timer = await self.timer_gateway.add_manual_timer(timer=new_timer)
        return AddManualTimerResponseDTO(
            id=timer.id,
            start_time=timer.start_time,
            end_time=timer.end_time,
            duration=timer.duration,
            hourly_rate=timer.hourly_rate,
            round_to_hour=timer.round_to_hour,
            billable_amount=timer.billable_amount,
            user_id=timer.user_id,
            project_id=timer.project_id,
        )

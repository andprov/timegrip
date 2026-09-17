import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from timegrip.application.common.permission_gateway import (
    PermissionGateway,
)
from timegrip.application.exceptions import (
    ProjectArchivedError,
    ProjectNotFoundError,
    TimerNotFoundError,
    TimerOverlapError,
    TimerRunningError,
)
from timegrip.application.project.gateway import ProjectGateway
from timegrip.application.timer.billing import calculate_billable_amount
from timegrip.application.timer.gateway import TimerGateway
from timegrip.entities.exceptions import InvalidTimerRangeError
from timegrip.entities.project import ProjectStatus
from timegrip.entities.timer import Timer, validate_timer_range

logger = logging.getLogger(__name__)


@dataclass
class UpdateTimerRequestDTO:
    id: UUID
    project_id: UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass
class UpdateTimerResponseDTO:
    id: UUID
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    hourly_rate: Decimal | None
    round_to_hour: bool
    billable_amount: Decimal | None
    user_id: UUID
    project_id: UUID


class UpdateTimerInteractor:
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
        current_user_id: UUID,
        update_timer_dto: UpdateTimerRequestDTO,
    ) -> UpdateTimerResponseDTO:
        await self.permission_gateway.check_permission(user_id=current_user_id)
        existing_timer = await self.timer_gateway.get_timer_by_id(
            id=update_timer_dto.id,
        )
        if existing_timer is None:
            logger.warning(f"Timer with id {update_timer_dto.id} not found")
            raise TimerNotFoundError(
                f"Timer with id {update_timer_dto.id} not found",
            )

        if existing_timer.user_id != current_user_id:
            logger.warning(
                f"User with id {current_user_id} does not have access to "
                f"timer with id {update_timer_dto.id}",
            )
            raise TimerNotFoundError(
                f"Timer with id {update_timer_dto.id} not found",
            )

        if existing_timer.end_time is None:
            logger.warning(
                f"User with id {current_user_id} tried to edit running "
                f"timer with id {update_timer_dto.id}",
            )
            raise TimerRunningError(
                "Timer is running, stop it before editing",
            )

        new_project_id = self._coalesce(
            new_value=update_timer_dto.project_id,
            old_value=existing_timer.project_id,
        )
        new_start_time = self._coalesce(
            new_value=update_timer_dto.start_time,
            old_value=existing_timer.start_time,
        )
        new_end_time = self._coalesce(
            new_value=update_timer_dto.end_time,
            old_value=existing_timer.end_time,
        )

        now = datetime.now(UTC)
        if new_start_time > now:
            raise InvalidTimerRangeError(
                message="Start time must not be in the future",
                code="start_time_in_future",
            )

        if new_end_time > now:
            raise InvalidTimerRangeError(
                message="End time must not be in the future",
                code="end_time_in_future",
            )

        validate_timer_range(
            start_time=new_start_time,
            end_time=new_end_time,
        )

        hourly_rate = existing_timer.hourly_rate
        round_to_hour = existing_timer.round_to_hour
        if new_project_id != existing_timer.project_id:
            project = await self.project_gateway.get_project_by_id(
                id=new_project_id,
            )
            if project is None:
                logger.warning(f"Project with id {new_project_id} not found")
                raise ProjectNotFoundError(
                    f"Project with id {new_project_id} not found",
                )

            if project.user_id != current_user_id:
                logger.warning(
                    f"User with id {current_user_id} does not have access "
                    f"to project with id {new_project_id}",
                )
                raise ProjectNotFoundError(
                    f"Project with id {new_project_id} not found",
                )

            if project.status == ProjectStatus.ARCHIVED:
                logger.warning(
                    f"User with id {current_user_id} tried to reassign "
                    f"timer with id {update_timer_dto.id} to archived "
                    f"project with id {new_project_id}",
                )
                raise ProjectArchivedError(
                    "Cannot reassign a time entry to an archived project",
                )

            hourly_rate = project.hourly_rate
            round_to_hour = project.round_to_hour

        has_overlap = await self.timer_gateway.has_overlapping_timer(
            user_id=current_user_id,
            start_time=new_start_time,
            end_time=new_end_time,
            exclude_id=existing_timer.id,
        )
        if has_overlap:
            logger.warning(
                f"User with id {current_user_id} tried to update timer "
                f"with id {update_timer_dto.id} to overlap with an "
                "existing one",
            )
            raise TimerOverlapError(
                "Timer overlaps with an existing time entry",
            )

        duration = new_end_time - new_start_time
        billable_amount = calculate_billable_amount(
            duration=duration,
            hourly_rate=hourly_rate,
            round_to_hour=round_to_hour,
        )

        new_timer = Timer(
            id=existing_timer.id,
            start_time=new_start_time,
            end_time=new_end_time,
            duration=None,
            hourly_rate=hourly_rate,
            round_to_hour=round_to_hour,
            billable_amount=billable_amount,
            user_id=existing_timer.user_id,
            project_id=new_project_id,
        )
        timer = await self.timer_gateway.update_timer(timer=new_timer)
        return UpdateTimerResponseDTO(
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

    @staticmethod
    def _coalesce(new_value: Any, old_value: Any) -> Any:
        return new_value if new_value is not None else old_value

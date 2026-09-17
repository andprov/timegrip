from abc import abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from timegrip.entities.timer import Timer


class TimerGateway(Protocol):
    @abstractmethod
    async def add_timer(self, timer: Timer) -> Timer:
        raise NotImplementedError

    @abstractmethod
    async def add_manual_timer(self, timer: Timer) -> Timer:
        raise NotImplementedError

    @abstractmethod
    async def get_all_user_timers(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
        project_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        billable: bool | None = None,
        include_archived_projects: bool = False,
    ) -> list[Timer]:
        raise NotImplementedError

    @abstractmethod
    async def count_user_timers(
        self,
        user_id: UUID,
        project_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        billable: bool | None = None,
        include_archived_projects: bool = False,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_timer_by_id(self, id: UUID) -> Timer | None:
        raise NotImplementedError

    @abstractmethod
    async def get_timers_by_ids(self, ids: list[UUID]) -> list[Timer]:
        raise NotImplementedError

    @abstractmethod
    async def get_running_timer_by_user(
        self,
        user_id: UUID,
    ) -> Timer | None:
        raise NotImplementedError

    @abstractmethod
    async def stop_timer(
        self,
        id: UUID,
        end_time: datetime,
        billable_amount: Decimal | None,
    ) -> Timer:
        raise NotImplementedError

    @abstractmethod
    async def update_timer(self, timer: Timer) -> Timer:
        raise NotImplementedError

    @abstractmethod
    async def delete_timer(self, id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_timers(self, ids: list[UUID]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def has_overlapping_timer(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime | None,
        exclude_id: UUID | None = None,
    ) -> bool:
        raise NotImplementedError

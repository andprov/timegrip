from abc import abstractmethod
from typing import Protocol

from timegrip.entities.outbox_email import OutboxEmail


class EmailOutboxGateway(Protocol):
    @abstractmethod
    async def fetch_pending(
        self,
        limit: int,
        stale_after_minutes: int,
    ) -> list[OutboxEmail]:
        raise NotImplementedError

    @abstractmethod
    async def mark_sent(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(self, id: int, max_attempts: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_old_emails(self, retention_days: int) -> int:
        raise NotImplementedError

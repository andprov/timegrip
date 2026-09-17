from abc import abstractmethod
from typing import Protocol


class EmailQueueGateway(Protocol):
    @abstractmethod
    async def enqueue(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        raise NotImplementedError

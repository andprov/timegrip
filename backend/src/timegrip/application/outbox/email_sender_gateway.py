from abc import abstractmethod
from typing import Protocol


class EmailSenderGateway(Protocol):
    @abstractmethod
    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        raise NotImplementedError

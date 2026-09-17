from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class IdProviderGateway(Protocol):
    @abstractmethod
    def get_id(self) -> UUID:
        raise NotImplementedError

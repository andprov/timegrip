from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class PermissionGateway(Protocol):
    @abstractmethod
    async def check_permission(self, user_id: UUID) -> None:
        raise NotImplementedError

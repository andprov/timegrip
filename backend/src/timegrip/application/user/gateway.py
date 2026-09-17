from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from timegrip.entities.user import Email, User


class UserGateway(Protocol):
    @abstractmethod
    async def add_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(self, id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_email(self, email: Email) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def activate_user(self, id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_inactive_users_after_grace_period(
        self,
        grace_period_days: int,
    ) -> int:
        raise NotImplementedError

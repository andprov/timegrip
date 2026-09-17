from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from timegrip.entities.password_reset_code import PasswordResetCode


class PasswordResetCodeGateway(Protocol):
    @abstractmethod
    async def add_code(
        self,
        reset_code: PasswordResetCode,
    ) -> PasswordResetCode:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_code_for_user(
        self,
        user_id: UUID,
    ) -> PasswordResetCode | None:
        raise NotImplementedError

    @abstractmethod
    async def increment_attempts(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_code_used(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_codes_for_user(self, user_id: UUID) -> None:
        raise NotImplementedError

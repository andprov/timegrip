from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from timegrip.entities.activation_code import ActivationCode


class ActivationCodeGateway(Protocol):
    @abstractmethod
    async def add_code(
        self,
        activation_code: ActivationCode,
    ) -> ActivationCode:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_code_for_user(
        self,
        user_id: UUID,
    ) -> ActivationCode | None:
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

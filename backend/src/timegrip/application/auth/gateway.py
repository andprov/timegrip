from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from timegrip.entities.refresh_token import RefreshToken


class RefreshTokenGateway(Protocol):
    @abstractmethod
    async def add_token(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        raise NotImplementedError

    @abstractmethod
    async def get_token_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        raise NotImplementedError

    @abstractmethod
    async def rotate_token(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_family(self, family_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_for_user(
        self,
        user_id: UUID,
    ) -> list[RefreshToken]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_token_for_user(
        self,
        id: int,
        user_id: UUID,
    ) -> RefreshToken | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_expired_and_old_revoked(
        self,
        revoked_retention_days: int,
    ) -> int:
        raise NotImplementedError

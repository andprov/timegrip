from abc import abstractmethod
from typing import Protocol


class PasswordHasherGateway(Protocol):
    @abstractmethod
    async def hash_password(self, password: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def verify_password(
        self,
        password: str,
        hashed_password: str,
    ) -> bool:
        raise NotImplementedError

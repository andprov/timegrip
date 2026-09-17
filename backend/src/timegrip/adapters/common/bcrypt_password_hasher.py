import asyncio

import bcrypt

from timegrip.application.common.password_hasher_gateway import (
    PasswordHasherGateway,
)
from timegrip.application.common.password_policy import MAX_PASSWORD_BYTES


class BcryptPasswordHasher(PasswordHasherGateway):
    async def hash_password(self, password: str) -> str:
        hashed_password = await asyncio.to_thread(
            bcrypt.hashpw,
            password.encode(),
            bcrypt.gensalt(),
        )
        return hashed_password.decode()

    async def verify_password(
        self,
        password: str,
        hashed_password: str,
    ) -> bool:
        if len(password.encode()) > MAX_PASSWORD_BYTES:
            return False

        return await asyncio.to_thread(
            bcrypt.checkpw,
            password.encode(),
            hashed_password.encode(),
        )

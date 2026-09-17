import bcrypt
import pytest

from timegrip.adapters.common.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from timegrip.application.common.password_policy import MAX_PASSWORD_BYTES

_gensalt = bcrypt.gensalt


@pytest.fixture
def password_hasher(monkeypatch):
    monkeypatch.setattr(bcrypt, "gensalt", lambda: _gensalt(rounds=4))
    return BcryptPasswordHasher()


@pytest.mark.asyncio
async def test_hash_password_does_not_store_plain_text(password_hasher):
    hashed_password = await password_hasher.hash_password("Passw0rd")
    assert hashed_password != "Passw0rd"
    assert await password_hasher.verify_password("Passw0rd", hashed_password)


@pytest.mark.asyncio
async def test_verify_password_rejects_wrong_password(password_hasher):
    hashed_password = await password_hasher.hash_password("Passw0rd")
    assert not await password_hasher.verify_password(
        "passw0rd",
        hashed_password,
    )


@pytest.mark.asyncio
async def test_verify_password_rejects_password_over_byte_limit(
    password_hasher,
):
    password = "A1" + "a" * (MAX_PASSWORD_BYTES - 2)
    hashed_password = await password_hasher.hash_password(password)
    assert await password_hasher.verify_password(password, hashed_password)
    assert not await password_hasher.verify_password(
        password + "extra",
        hashed_password,
    )

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID

import jwt
import pytest

from timegrip.adapters.common.token_id_provider import (
    JWTTokenManager,
    TokenIdProvider,
)
from timegrip.application.common.jwt_token_config import JWTTokenConfig
from timegrip.application.exceptions import UnauthorizedError

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def token_manager():
    return JWTTokenManager(
        config=JWTTokenConfig(
            secret_key="test-secret",
            expire_time=15,
            algorithm="HS256",
        ),
    )


def _make_provider(token_manager, headers):
    request = MagicMock()
    request.headers = headers
    return TokenIdProvider(token_manager=token_manager, request=request)


@pytest.mark.parametrize(
    "header_template",
    ["Bearer {token}", "bearer {token}"],
)
def test_get_id_accepts_bearer_scheme_case_insensitively(
    token_manager,
    header_template,
):
    token = token_manager.create_token(user_id=TEST_USER_ID)
    provider = _make_provider(
        token_manager,
        {"authorization": header_template.format(token=token)},
    )
    assert provider.get_id() == TEST_USER_ID


@pytest.mark.parametrize(
    "header_template",
    ["Basic {token}", "Bearer", ""],
)
def test_get_id_rejects_header_without_bearer_token(
    token_manager,
    header_template,
):
    token = token_manager.create_token(user_id=TEST_USER_ID)
    provider = _make_provider(
        token_manager,
        {"authorization": header_template.format(token=token)},
    )
    with pytest.raises(UnauthorizedError) as exc_info:
        provider.get_id()
    assert exc_info.value.code == "unauthorized"


def test_get_id_rejects_missing_authorization_header(token_manager):
    provider = _make_provider(token_manager, {})
    with pytest.raises(UnauthorizedError) as exc_info:
        provider.get_id()
    assert exc_info.value.code == "unauthorized"


def test_create_token_round_trips_user_id_and_expiry(token_manager):
    before = datetime.now(UTC).replace(microsecond=0)
    token = token_manager.create_token(user_id=TEST_USER_ID)
    token_data = token_manager.decode_token(token)
    after = datetime.now(UTC)
    assert token_data.user_id == TEST_USER_ID
    assert (
        before + timedelta(minutes=15)
        <= token_data.expire_time
        <= after + timedelta(minutes=15)
    )


def _encode(payload, secret_key="test-secret"):
    return jwt.encode(payload, secret_key, algorithm="HS256")


@pytest.mark.parametrize(
    "token",
    [
        _encode(
            {
                "sub": str(TEST_USER_ID),
                "exp": datetime.now(UTC) - timedelta(seconds=1),
            },
        ),
        _encode(
            {
                "sub": str(TEST_USER_ID),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            secret_key="other-secret",
        ),
        _encode({"exp": datetime.now(UTC) + timedelta(minutes=15)}),
        _encode(
            {
                "sub": "not-a-uuid",
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
        ),
        jwt.encode(
            {
                "sub": str(TEST_USER_ID),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            "test-secret",
            algorithm="HS512",
        ),
        "not-a-jwt",
    ],
    ids=[
        "expired",
        "wrong_signature",
        "missing_sub",
        "invalid_sub",
        "other_algorithm",
        "malformed",
    ],
)
def test_get_id_raises_unauthorized_for_unacceptable_token(
    token_manager,
    token,
):
    provider = _make_provider(
        token_manager,
        {"authorization": f"Bearer {token}"},
    )
    with pytest.raises(UnauthorizedError) as exc_info:
        provider.get_id()
    assert exc_info.value.code == "unauthorized"

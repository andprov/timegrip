from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.auth.refresh_token_manager import (
    REFRESH_TOKEN_GRACE_SECONDS,
    REFRESH_TOKEN_TTL_DAYS,
    ActiveSessionDTO,
    RefreshTokenManager,
    _hash_token,
)
from timegrip.application.exceptions import (
    InvalidRefreshTokenError,
    RefreshTokenNotFoundError,
)
from timegrip.entities.refresh_token import (
    RefreshToken,
    RefreshTokenRevokeReason,
)

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_FAMILY_ID = UUID("00000000-0000-0000-0000-0000000000f1")
RAW_TOKEN = "some-raw-refresh-token"


@pytest.fixture
def mock_refresh_token_gateway():
    return AsyncMock()


@pytest.fixture
def refresh_token_manager(mock_refresh_token_gateway):
    return RefreshTokenManager(
        refresh_token_gateway=mock_refresh_token_gateway,
    )


def _make_record(**overrides):
    defaults = {
        "id": 10,
        "user_id": TEST_USER_ID,
        "family_id": TEST_FAMILY_ID,
        "token_hash": _hash_token(RAW_TOKEN),
        "expires_at": datetime.now(UTC) + timedelta(days=30),
        "revoked_at": None,
        "revoke_reason": None,
        "user_agent": None,
        "ip_address": None,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return RefreshToken(**defaults)


@pytest.mark.asyncio
async def test_issue_stores_hashed_token(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    raw_token = await refresh_token_manager.issue(user_id=TEST_USER_ID)
    stored = mock_refresh_token_gateway.add_token.call_args.kwargs[
        "refresh_token"
    ]
    assert stored.user_id == TEST_USER_ID
    assert stored.token_hash == _hash_token(raw_token)
    assert stored.token_hash != raw_token
    assert stored.revoked_at is None
    assert stored.revoke_reason is None
    assert stored.family_id is None


@pytest.mark.asyncio
async def test_issue_keeps_given_family(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    await refresh_token_manager.issue(
        user_id=TEST_USER_ID,
        family_id=TEST_FAMILY_ID,
    )
    stored = mock_refresh_token_gateway.add_token.call_args.kwargs[
        "refresh_token"
    ]
    assert stored.family_id == TEST_FAMILY_ID


@pytest.mark.asyncio
async def test_issue_sets_ttl_and_client_info(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    before = datetime.now(UTC)
    await refresh_token_manager.issue(
        user_id=TEST_USER_ID,
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1",
    )
    after = datetime.now(UTC)
    stored = mock_refresh_token_gateway.add_token.call_args.kwargs[
        "refresh_token"
    ]
    ttl = timedelta(days=REFRESH_TOKEN_TTL_DAYS)
    assert before + ttl <= stored.expires_at <= after + ttl
    assert stored.user_agent == "Mozilla/5.0"
    assert stored.ip_address == "192.168.1.1"


@pytest.mark.asyncio
async def test_rotate_success(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record()
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    rotated = await refresh_token_manager.rotate(
        raw_token=RAW_TOKEN,
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1",
    )
    mock_refresh_token_gateway.get_token_by_hash.assert_called_once_with(
        token_hash=_hash_token(RAW_TOKEN),
    )
    mock_refresh_token_gateway.rotate_token.assert_called_once_with(
        id=record.id,
    )
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()
    assert rotated.user_id == TEST_USER_ID
    assert rotated.refresh_token != RAW_TOKEN
    stored = mock_refresh_token_gateway.add_token.call_args.kwargs[
        "refresh_token"
    ]
    assert stored.token_hash == _hash_token(rotated.refresh_token)
    assert stored.family_id == TEST_FAMILY_ID
    assert stored.user_agent == "Mozilla/5.0"
    assert stored.ip_address == "192.168.1.1"


@pytest.mark.asyncio
async def test_rotate_unknown_token(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_token_by_hash.return_value = None
    with pytest.raises(InvalidRefreshTokenError):
        await refresh_token_manager.rotate(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_rotate_expired_token(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record(
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    with pytest.raises(InvalidRefreshTokenError):
        await refresh_token_manager.rotate(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.rotate_token.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_rotate_reuse_within_grace_period_is_benign(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record(
        revoked_at=datetime.now(UTC)
        - timedelta(seconds=REFRESH_TOKEN_GRACE_SECONDS - 5),
        revoke_reason=RefreshTokenRevokeReason.ROTATED,
    )
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    rotated = await refresh_token_manager.rotate(
        raw_token=RAW_TOKEN,
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1",
    )
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()
    mock_refresh_token_gateway.rotate_token.assert_not_called()
    mock_refresh_token_gateway.add_token.assert_called_once()
    assert rotated.user_id == TEST_USER_ID
    assert rotated.refresh_token != RAW_TOKEN
    stored = mock_refresh_token_gateway.add_token.call_args.kwargs[
        "refresh_token"
    ]
    assert stored.token_hash == _hash_token(rotated.refresh_token)
    assert stored.user_agent == "Mozilla/5.0"
    assert stored.ip_address == "192.168.1.1"
    assert stored.family_id == TEST_FAMILY_ID


@pytest.mark.asyncio
async def test_rotate_reuse_outside_grace_period_revokes_all(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record(
        revoked_at=datetime.now(UTC)
        - timedelta(seconds=REFRESH_TOKEN_GRACE_SECONDS + 5),
        revoke_reason=RefreshTokenRevokeReason.ROTATED,
    )
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    with pytest.raises(InvalidRefreshTokenError):
        await refresh_token_manager.rotate(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_all_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )
    mock_refresh_token_gateway.add_token.assert_not_called()


@pytest.mark.asyncio
async def test_rotate_explicitly_revoked_token_has_no_grace_period(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record(
        revoked_at=datetime.now(UTC) - timedelta(seconds=1),
        revoke_reason=RefreshTokenRevokeReason.REVOKED,
    )
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    with pytest.raises(InvalidRefreshTokenError):
        await refresh_token_manager.rotate(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.add_token.assert_not_called()
    mock_refresh_token_gateway.rotate_token.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_revokes_active_token(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    record = _make_record()
    mock_refresh_token_gateway.get_token_by_hash.return_value = record
    await refresh_token_manager.revoke(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_family.assert_called_once_with(
        family_id=TEST_FAMILY_ID,
    )


@pytest.mark.asyncio
async def test_revoke_rotated_token_revokes_its_family(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_token_by_hash.return_value = _make_record(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        revoke_reason=RefreshTokenRevokeReason.ROTATED,
    )
    await refresh_token_manager.revoke(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_family.assert_called_once_with(
        family_id=TEST_FAMILY_ID,
    )


@pytest.mark.asyncio
async def test_revoke_already_revoked_token_is_noop(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_token_by_hash.return_value = _make_record(
        revoked_at=datetime.now(UTC) - timedelta(days=1),
        revoke_reason=RefreshTokenRevokeReason.REVOKED,
    )
    await refresh_token_manager.revoke(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_family.assert_not_called()
    mock_refresh_token_gateway.revoke_all_for_user.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_unknown_token_is_noop(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_token_by_hash.return_value = None
    await refresh_token_manager.revoke(raw_token=RAW_TOKEN)
    mock_refresh_token_gateway.revoke_family.assert_not_called()


@pytest.mark.asyncio
async def test_list_active_sessions_delegates_to_gateway(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    records = [_make_record(id=1), _make_record(id=2)]
    mock_refresh_token_gateway.get_active_for_user.return_value = records
    sessions = await refresh_token_manager.list_active_sessions(
        user_id=TEST_USER_ID,
    )
    assert sessions == [
        ActiveSessionDTO(
            id=record.id,
            user_agent=record.user_agent,
            ip_address=record.ip_address,
            created_at=record.created_at,
        )
        for record in records
    ]
    mock_refresh_token_gateway.get_active_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_revoke_session_success(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_active_token_for_user.return_value = (
        _make_record()
    )
    await refresh_token_manager.revoke_session(
        user_id=TEST_USER_ID,
        session_id=10,
    )
    gateway = mock_refresh_token_gateway
    gateway.get_active_token_for_user.assert_called_once_with(
        id=10,
        user_id=TEST_USER_ID,
    )
    gateway.revoke_family.assert_called_once_with(family_id=TEST_FAMILY_ID)


@pytest.mark.asyncio
async def test_revoke_session_not_found(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    mock_refresh_token_gateway.get_active_token_for_user.return_value = None
    with pytest.raises(RefreshTokenNotFoundError):
        await refresh_token_manager.revoke_session(
            user_id=TEST_USER_ID,
            session_id=10,
        )
    mock_refresh_token_gateway.revoke_family.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_all_revokes_every_session_of_user(
    refresh_token_manager,
    mock_refresh_token_gateway,
):
    await refresh_token_manager.revoke_all(user_id=TEST_USER_ID)
    mock_refresh_token_gateway.revoke_all_for_user.assert_called_once_with(
        user_id=TEST_USER_ID,
    )

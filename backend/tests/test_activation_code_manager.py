from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from timegrip.application.user_activation import activation_code_manager
from timegrip.application.user_activation.activation_code_manager import (
    ACTIVATION_CODE_TTL_HOURS,
    ActivationCodeManager,
)

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000042")


@pytest.fixture
def mock_activation_code_gateway():
    return AsyncMock()


@pytest.fixture
def code_manager(mock_activation_code_gateway):
    return ActivationCodeManager(
        activation_code_gateway=mock_activation_code_gateway,
    )


@pytest.mark.asyncio
async def test_issue_code_generates_and_persists(
    code_manager,
    mock_activation_code_gateway,
):
    code = await code_manager(user_id=TEST_USER_ID)
    assert len(code) == 6
    assert code.isdigit()
    mock_activation_code_gateway.add_code.assert_called_once()
    saved_code = mock_activation_code_gateway.add_code.call_args.kwargs[
        "activation_code"
    ]
    assert saved_code.id is None
    assert saved_code.user_id == TEST_USER_ID
    assert saved_code.code == code
    assert saved_code.used_at is None
    assert saved_code.attempts == 0
    assert saved_code.created_at is None


@pytest.mark.asyncio
async def test_issue_code_expires_after_ttl(
    code_manager,
    mock_activation_code_gateway,
):
    before = datetime.now(UTC)
    await code_manager(user_id=TEST_USER_ID)
    after = datetime.now(UTC)
    saved_code = mock_activation_code_gateway.add_code.call_args.kwargs[
        "activation_code"
    ]
    ttl = timedelta(hours=ACTIVATION_CODE_TTL_HOURS)
    assert before + ttl <= saved_code.expires_at <= after + ttl


@pytest.mark.asyncio
async def test_issue_code_pads_small_numbers_with_zeros(
    code_manager,
    monkeypatch,
):
    monkeypatch.setattr(
        activation_code_manager.secrets,
        "randbelow",
        lambda _: 7,
    )
    code = await code_manager(user_id=TEST_USER_ID)
    assert code == "000007"

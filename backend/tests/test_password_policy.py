import pytest

from timegrip.application.common.password_policy import (
    MAX_PASSWORD_BYTES,
    MIN_PASSWORD_LENGTH,
    validate_password_strength,
)
from timegrip.application.exceptions import WeakPasswordError


@pytest.mark.parametrize(
    "password",
    [
        "Abcd1",
        "A1" + "a" * (MAX_PASSWORD_BYTES - 2),
    ],
)
def test_validate_password_strength_accepts_valid_password(password):
    validate_password_strength(password=password)


@pytest.mark.parametrize(
    ("password", "code"),
    [
        ("", "password_empty"),
        ("A1" + "a" * (MIN_PASSWORD_LENGTH - 3), "password_too_short"),
        ("A1" + "a" * (MAX_PASSWORD_BYTES - 1), "password_too_long"),
        ("passw0rd", "password_no_uppercase"),
        ("Password", "password_no_digit"),
    ],
)
def test_validate_password_strength_rejects_weak_password(password, code):
    with pytest.raises(WeakPasswordError) as exc_info:
        validate_password_strength(password=password)
    assert exc_info.value.code == code


def test_validate_password_strength_limits_bytes_not_characters():
    password = "A1" + "ж" * (MAX_PASSWORD_BYTES // 2)
    assert len(password) < MAX_PASSWORD_BYTES
    with pytest.raises(WeakPasswordError) as exc_info:
        validate_password_strength(password=password)
    assert exc_info.value.code == "password_too_long"

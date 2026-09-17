import re

from timegrip.application.exceptions import WeakPasswordError

MIN_PASSWORD_LENGTH = 5
MAX_PASSWORD_BYTES = 72


def validate_password_strength(password: str) -> None:
    if not password:
        raise WeakPasswordError(
            message="Password must not be empty",
            code="password_empty",
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            message=f"Password must be at least {MIN_PASSWORD_LENGTH} "
            "characters long",
            code="password_too_short",
        )

    if len(password.encode()) > MAX_PASSWORD_BYTES:
        raise WeakPasswordError(
            message=f"Password must be at most {MAX_PASSWORD_BYTES} bytes "
            "long",
            code="password_too_long",
        )

    if not re.search(r"[A-Z]", password):
        raise WeakPasswordError(
            message="Password must contain at least one uppercase letter",
            code="password_no_uppercase",
        )

    if not re.search(r"\d", password):
        raise WeakPasswordError(
            message="Password must contain at least one digit",
            code="password_no_digit",
        )

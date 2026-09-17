import pytest

from timegrip.application.common.plural import ru_plural
from timegrip.application.password_reset.password_reset_code_manager import (
    PASSWORD_RESET_CODE_TTL_MINUTES,
)
from timegrip.application.password_reset.password_reset_email import (
    build_password_reset_email,
    build_password_reset_url,
)
from timegrip.application.user_activation.activation_code_manager import (
    ACTIVATION_CODE_TTL_HOURS,
)
from timegrip.application.user_activation.activation_email import (
    build_activation_email,
    build_activation_url,
)
from timegrip.entities.user import Locale

ACTIVATION_URL = "https://timegrip.test/dashboard?code=123456"
RESET_URL = "https://timegrip.test/reset-password?email=a%40b.c&code=654321"


def test_activation_email_contains_code_and_actual_ttl():
    email = build_activation_email(
        "123456",
        activation_url=ACTIVATION_URL,
        locale=Locale.EN,
    )
    assert email.subject == "Activate your TimeGrip account"
    assert "123456" in email.body
    assert ACTIVATION_URL in email.body
    assert f"{ACTIVATION_CODE_TTL_HOURS} hours" in email.body


def test_activation_email_ru_contains_code_and_actual_ttl():
    email = build_activation_email(
        "123456",
        activation_url=ACTIVATION_URL,
        locale=Locale.RU,
    )
    hours = ru_plural(ACTIVATION_CODE_TTL_HOURS, "час", "часа", "часов")
    assert email.subject == "Активация аккаунта TimeGrip"
    assert "123456" in email.body
    assert ACTIVATION_URL in email.body
    assert f"{ACTIVATION_CODE_TTL_HOURS} {hours}" in email.body


def test_password_reset_email_contains_code_and_actual_ttl():
    email = build_password_reset_email(
        "654321",
        reset_url=RESET_URL,
        locale=Locale.EN,
    )
    assert email.subject == "Reset your TimeGrip password"
    assert "654321" in email.body
    assert RESET_URL in email.body
    assert f"{PASSWORD_RESET_CODE_TTL_MINUTES} minutes" in email.body


def test_password_reset_email_ru_contains_code_and_actual_ttl():
    email = build_password_reset_email(
        "654321",
        reset_url=RESET_URL,
        locale=Locale.RU,
    )
    minutes = ru_plural(
        PASSWORD_RESET_CODE_TTL_MINUTES,
        "минуту",
        "минуты",
        "минут",
    )
    assert email.subject == "Сброс пароля в TimeGrip"
    assert "654321" in email.body
    assert RESET_URL in email.body
    assert f"{PASSWORD_RESET_CODE_TTL_MINUTES} {minutes}" in email.body


def test_activation_url_contains_code():
    url = build_activation_url(
        frontend_url="https://timegrip.test",
        code="123456",
    )
    assert url == "https://timegrip.test/dashboard?code=123456"


def test_password_reset_url_contains_encoded_email_and_code():
    url = build_password_reset_url(
        frontend_url="https://timegrip.test",
        email="user+tag@example.com",
        code="654321",
    )
    assert url == (
        "https://timegrip.test/reset-password"
        "?email=user%2Btag%40example.com&code=654321"
    )


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (0, "часов"),
        (1, "час"),
        (2, "часа"),
        (4, "часа"),
        (5, "часов"),
        (11, "часов"),
        (12, "часов"),
        (14, "часов"),
        (21, "час"),
        (24, "часа"),
        (25, "часов"),
        (111, "часов"),
        (122, "часа"),
    ],
)
def test_ru_plural(number, expected):
    assert ru_plural(number, "час", "часа", "часов") == expected

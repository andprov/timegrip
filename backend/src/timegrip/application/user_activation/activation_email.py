from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlencode

from timegrip.application.common.plural import ru_plural
from timegrip.application.user_activation.activation_code_manager import (
    ACTIVATION_CODE_TTL_HOURS,
)
from timegrip.entities.user import Locale

ACTIVATION_PATH = "/dashboard"


@dataclass
class ActivationEmail:
    subject: str
    body: str


def build_activation_url(frontend_url: str, code: str) -> str:
    query = urlencode({"code": code})
    return f"{frontend_url}{ACTIVATION_PATH}?{query}"


def _build_en(code: str, activation_url: str) -> ActivationEmail:
    return ActivationEmail(
        subject="Activate your TimeGrip account",
        body=(
            "Hello!\n\n"
            "You are receiving this email because this address was used "
            "to sign up for TimeGrip, a time tracking service.\n\n"
            "To activate your account, follow the link:\n\n"
            f"{activation_url}\n\n"
            "Or enter the following code on the activation page:\n\n"
            f"    {code}\n\n"
            "The link and the code expire in "
            f"{ACTIVATION_CODE_TTL_HOURS} hours.\n\n"
            "If you didn't sign up for TimeGrip, you can safely ignore "
            "this email.\n\n"
            "Best regards,\n"
            "The TimeGrip team"
        ),
    )


def _build_ru(code: str, activation_url: str) -> ActivationEmail:
    hours = ru_plural(ACTIVATION_CODE_TTL_HOURS, "час", "часа", "часов")
    return ActivationEmail(
        subject="Активация аккаунта TimeGrip",
        body=(
            "Здравствуйте!\n\n"
            "Вы получили это письмо, потому что этот адрес был указан "
            "при регистрации в TimeGrip — сервисе учёта времени.\n\n"
            "Чтобы активировать аккаунт, перейдите по ссылке:\n\n"
            f"{activation_url}\n\n"
            "Или введите на странице активации код:\n\n"
            f"    {code}\n\n"
            f"Ссылка и код действуют {ACTIVATION_CODE_TTL_HOURS} {hours}.\n\n"
            "Если вы не регистрировались в TimeGrip, просто "
            "проигнорируйте это письмо.\n\n"
            "С уважением,\n"
            "команда TimeGrip"
        ),
    )


_BUILDERS: dict[Locale, Callable[[str, str], ActivationEmail]] = {
    Locale.EN: _build_en,
    Locale.RU: _build_ru,
}


def build_activation_email(
    code: str,
    activation_url: str,
    locale: Locale,
) -> ActivationEmail:
    return _BUILDERS.get(locale, _build_en)(code, activation_url)

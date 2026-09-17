from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlencode

from timegrip.application.common.plural import ru_plural
from timegrip.application.password_reset.password_reset_code_manager import (
    PASSWORD_RESET_CODE_TTL_MINUTES,
)
from timegrip.entities.user import Locale

RESET_PASSWORD_PATH = "/reset-password"


@dataclass
class PasswordResetEmail:
    subject: str
    body: str


def build_password_reset_url(frontend_url: str, email: str, code: str) -> str:
    query = urlencode({"email": email, "code": code})
    return f"{frontend_url}{RESET_PASSWORD_PATH}?{query}"


def _build_en(code: str, reset_url: str) -> PasswordResetEmail:
    return PasswordResetEmail(
        subject="Reset your TimeGrip password",
        body=(
            "Hello!\n\n"
            "You are receiving this email because a password reset was "
            "requested for your account in TimeGrip, a time tracking "
            "service.\n\n"
            "To set a new password, follow the link:\n\n"
            f"{reset_url}\n\n"
            "Or enter the following code on the password reset page:\n\n"
            f"    {code}\n\n"
            "The link and the code expire in "
            f"{PASSWORD_RESET_CODE_TTL_MINUTES} minutes.\n\n"
            "If you didn't request a password reset, you can safely ignore "
            "this email. Your password will not be changed.\n\n"
            "Best regards,\n"
            "The TimeGrip team"
        ),
    )


def _build_ru(code: str, reset_url: str) -> PasswordResetEmail:
    minutes = ru_plural(
        PASSWORD_RESET_CODE_TTL_MINUTES,
        "минуту",
        "минуты",
        "минут",
    )
    return PasswordResetEmail(
        subject="Сброс пароля в TimeGrip",
        body=(
            "Здравствуйте!\n\n"
            "Вы получили это письмо, потому что для вашего аккаунта "
            "в TimeGrip — сервисе учёта времени — был запрошен сброс "
            "пароля.\n\n"
            "Чтобы задать новый пароль, перейдите по ссылке:\n\n"
            f"{reset_url}\n\n"
            "Или введите на странице сброса пароля код:\n\n"
            f"    {code}\n\n"
            "Ссылка и код действуют "
            f"{PASSWORD_RESET_CODE_TTL_MINUTES} {minutes}.\n\n"
            "Если вы не запрашивали сброс пароля, просто проигнорируйте "
            "это письмо. Ваш пароль останется прежним.\n\n"
            "С уважением,\n"
            "команда TimeGrip"
        ),
    )


_BUILDERS: dict[Locale, Callable[[str, str], PasswordResetEmail]] = {
    Locale.EN: _build_en,
    Locale.RU: _build_ru,
}


def build_password_reset_email(
    code: str,
    reset_url: str,
    locale: Locale,
) -> PasswordResetEmail:
    return _BUILDERS.get(locale, _build_en)(code, reset_url)

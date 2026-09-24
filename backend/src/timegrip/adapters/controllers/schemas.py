from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, EmailStr, Field

from timegrip.application.common.password_policy import (
    MAX_PASSWORD_BYTES,
    MIN_PASSWORD_LENGTH,
)
from timegrip.entities.project import ProjectColor, ProjectStatus
from timegrip.entities.timer import MIN_TIMER_START
from timegrip.entities.user import Locale, TimeFormat

EXAMPLE_UUID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
DATETIME_EXAMPLE = "2000-01-01T01:00:00Z"
TZ_DESCRIPTION = "Must include an explicit timezone offset (e.g. Z or +00:00)."
MIN_TIMER_START_TEXT = f"{MIN_TIMER_START:%Y-%m-%dT%H:%M:%SZ}"
UNAUTHORIZED_HEADERS = {
    "WWW-Authenticate": {
        "description": (
            "Sent as `Bearer` when the access token is missing, is not sent "
            "with the `Bearer` scheme, or is invalid or expired."
        ),
        "schema": {"type": "string", "example": "Bearer"},
    },
}
RETRY_AFTER_HEADERS = {
    "Retry-After": {
        "description": "Seconds to wait before a new request is accepted.",
        "schema": {"type": "integer", "example": 42},
    },
}
USER_NOT_FOUND_EXAMPLE = {
    "summary": "User no longer exists",
    "value": {
        "detail": f"User with id {EXAMPLE_UUID} not found",
        "code": "user_not_found",
    },
}
COLOR_DESCRIPTION = (
    "One of: " + ", ".join(color.value for color in ProjectColor) + "."
)
STATUS_DESCRIPTION = (
    "One of: " + ", ".join(s.value for s in ProjectStatus) + "."
)
TIME_FORMAT_DESCRIPTION = (
    "One of: " + ", ".join(tf.value for tf in TimeFormat) + "."
)
LOCALE_DESCRIPTION = "One of: " + ", ".join(loc.value for loc in Locale) + "."
EMAIL_DESCRIPTION = (
    "Case-insensitive: the address is stored and returned in lowercase."
)
HOURLY_RATE_DESCRIPTION = (
    "Must not be negative. Up to 8 digits before the decimal point and 2 "
    "after (max 99999999.99). A rate of 0 is stored as no rate, making the "
    "project non-billable."
)
ROUND_TO_HOUR_DESCRIPTION = (
    "Round each timer's billable duration to the nearest hour "
    "(under 30 minutes rounds down, 30 or more rounds up) before "
    "computing its billable amount. Ignored, and stored as false, "
    "while the project has no hourly rate. Regardless of this setting, "
    "durations are always rounded to the nearest minute first "
    "(30 seconds or more rounds up)."
)
RATE_SNAPSHOT_DESCRIPTION = (
    "Copied from the project when the entry is created — a timer start or "
    "a manual entry — and kept from then on: changing the project's rate "
    "later leaves existing entries untouched."
)
RATE_CHANGE_SCOPE_DESCRIPTION = (
    "Applies to time entries created after the change; existing entries "
    "keep the rate and rounding they were created with, and are not "
    "recalculated."
)
PASSWORD_DESCRIPTION = (
    f"At least {MIN_PASSWORD_LENGTH} characters long, with at least one "
    f"uppercase letter and one digit, and at most {MAX_PASSWORD_BYTES} "
    f"bytes long. The requirements are checked in that order and only the "
    f"first unmet one is reported."
)
PASSWORD_LENGTH_MISMATCH_NOTE = (
    f"A password longer than {MAX_PASSWORD_BYTES} bytes can never match a "
    f"stored one, so it comes back as a wrong password rather than as a "
    f"weak one."
)
WEAK_PASSWORD_EXAMPLES = {
    "password_empty": {
        "summary": "Empty password",
        "value": {
            "detail": "Password must not be empty",
            "code": "password_empty",
        },
    },
    "password_too_short": {
        "summary": "Too short",
        "value": {
            "detail": (
                f"Password must be at least {MIN_PASSWORD_LENGTH} "
                f"characters long"
            ),
            "code": "password_too_short",
        },
    },
    "password_too_long": {
        "summary": "Too long",
        "value": {
            "detail": (
                f"Password must be at most {MAX_PASSWORD_BYTES} bytes long"
            ),
            "code": "password_too_long",
        },
    },
    "password_no_uppercase": {
        "summary": "No uppercase letter",
        "value": {
            "detail": "Password must contain at least one uppercase letter",
            "code": "password_no_uppercase",
        },
    },
    "password_no_digit": {
        "summary": "No digit",
        "value": {
            "detail": "Password must contain at least one digit",
            "code": "password_no_digit",
        },
    },
}


class HTTPError(BaseModel):
    detail: str = Field(examples=["Error message"])
    code: str = Field(
        examples=["error_code"],
        description=(
            "Stable machine-readable identifier of the error, meant for "
            "clients that show the message in their own language."
        ),
    )


class ValidationErrorItem(BaseModel):
    loc: list[str | int] = Field(
        examples=[["body", "email"]],
        description="Path to the failing value, starting with its location.",
    )
    msg: str = Field(examples=["Field required"])
    type: str = Field(
        examples=["missing"],
        description=(
            "Stable machine-readable identifier of the failure, meant for "
            "clients that show the message in their own language."
        ),
    )


class ValidationHTTPError(HTTPError):
    code: str = Field(examples=["validation_error"])
    errors: list[ValidationErrorItem]


class Page[ItemT](BaseModel):
    items: list[ItemT]
    page: int = Field(examples=[1])
    page_size: int = Field(examples=[10])
    total: int = Field(examples=[42])


class LoginData(BaseModel):
    email: EmailStr = Field(
        examples=["user@example.com"],
        description=EMAIL_DESCRIPTION,
    )
    password: str = Field(examples=["Passw0rd"])


class TokenPairData(BaseModel):
    access_token: str = Field(examples=["Access_Token_Example_1234567890d"])
    refresh_token: str = Field(examples=["Refresh_Token_Example_1234567890d"])
    token_type: str = Field(default="bearer", examples=["bearer"])


class RefreshTokenRequestData(BaseModel):
    refresh_token: str = Field(examples=["Refresh_Token_Example_1234567890d"])


class SessionData(BaseModel):
    id: int = Field(
        examples=[1],
        description=(
            "Changes every time the session is refreshed via "
            "`POST /api/auth/refresh`."
        ),
    )
    user_agent: str | None = Field(
        examples=["Mozilla/5.0 (X11; Linux x86_64) ..."],
    )
    ip_address: str | None = Field(examples=["192.168.1.1"])
    created_at: AwareDatetime = Field(
        examples=[DATETIME_EXAMPLE],
        description=(
            "When the session's current refresh token was issued, i.e. the "
            "sign-in or the latest refresh, not when the session started."
        ),
    )


class UserAddData(BaseModel):
    email: EmailStr = Field(
        examples=["user@example.com"],
        description=EMAIL_DESCRIPTION,
    )
    password: str = Field(
        examples=["Passw0rd"],
        description=PASSWORD_DESCRIPTION,
    )
    locale: str | None = Field(
        default=None,
        examples=[Locale.EN.value],
        description=(
            f"Initial UI locale, carried over from the language the "
            f"client was using before signing up. {LOCALE_DESCRIPTION} "
            f"Defaults to {Locale.EN.value} if omitted or invalid."
        ),
    )


class UserData(BaseModel):
    id: UUID = Field(examples=[EXAMPLE_UUID])
    email: EmailStr = Field(
        examples=["user@example.com"],
        description="Always in lowercase.",
    )
    is_active: bool = Field(examples=[True])
    time_format: str = Field(
        examples=[TimeFormat.TWENTY_FOUR_HOUR.value],
        description=TIME_FORMAT_DESCRIPTION,
    )
    locale: str = Field(
        examples=[Locale.EN.value],
        description=LOCALE_DESCRIPTION,
    )


class UserPasswordUpdateData(BaseModel):
    current_password: str = Field(examples=["Passw0rd"])
    new_password: str = Field(
        examples=["NewPassw0rd"],
        description=PASSWORD_DESCRIPTION,
    )


class UserEmailUpdateData(BaseModel):
    password: str = Field(examples=["Passw0rd"])
    new_email: EmailStr = Field(
        examples=["new_user@example.com"],
        description=EMAIL_DESCRIPTION,
    )


class UserTimeFormatUpdateData(BaseModel):
    time_format: str = Field(
        examples=[TimeFormat.TWENTY_FOUR_HOUR.value],
        description=TIME_FORMAT_DESCRIPTION,
    )


class UserLocaleUpdateData(BaseModel):
    locale: str = Field(
        examples=[Locale.RU.value],
        description=LOCALE_DESCRIPTION,
    )


class PasswordForgotData(BaseModel):
    email: EmailStr = Field(
        examples=["user@example.com"],
        description=EMAIL_DESCRIPTION,
    )


class PasswordResetData(BaseModel):
    email: EmailStr = Field(
        examples=["user@example.com"],
        description=EMAIL_DESCRIPTION,
    )
    code: str = Field(
        examples=["123456"],
        description="Password reset code sent to your email.",
    )
    new_password: str = Field(
        examples=["NewPassw0rd"],
        description=PASSWORD_DESCRIPTION,
    )


class ActivationCodeData(BaseModel):
    code: str = Field(
        examples=["123456"],
        description="Activation code sent to your email.",
    )


class ResendCooldownData(BaseModel):
    retry_after_seconds: int = Field(
        examples=[42],
        description=(
            "Seconds to wait before a new activation code can be requested "
            "via `POST /api/users/me/activate/resend`. `0` means it can be "
            "requested right away."
        ),
    )


class ProjectAddData(BaseModel):
    name: str = Field(examples=["Website Redesign"])
    color: str | None = Field(
        default=None,
        examples=[ProjectColor.BLUE.value],
        description=f"{COLOR_DESCRIPTION} Defaults to gray if omitted.",
    )
    hourly_rate: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        examples=["50.00"],
        description=(
            f"Billable rate per hour. Omit for a non-billable project. "
            f"{HOURLY_RATE_DESCRIPTION}"
        ),
    )
    round_to_hour: bool = Field(
        default=False,
        examples=[False],
        description=ROUND_TO_HOUR_DESCRIPTION,
    )


class ProjectData(BaseModel):
    id: UUID = Field(examples=[EXAMPLE_UUID])
    name: str = Field(examples=["Website Redesign"])
    color: str = Field(examples=[ProjectColor.BLUE.value])
    hourly_rate: Decimal | None = Field(examples=["50.00"])
    round_to_hour: bool = Field(examples=[False])
    status: str = Field(examples=[ProjectStatus.ACTIVE.value])


class ProjectUpdateData(BaseModel):
    name: str | None = Field(default=None, examples=["Website Redesign v2"])
    color: str | None = Field(
        default=None,
        examples=[ProjectColor.BLUE.value],
        description=COLOR_DESCRIPTION,
    )
    hourly_rate: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        examples=["50.00"],
        description=(
            f"Billable rate per hour. Send null to clear the rate and make "
            f"the project non-billable; omit the field to keep the current "
            f"rate. {HOURLY_RATE_DESCRIPTION} "
            f"{RATE_CHANGE_SCOPE_DESCRIPTION}"
        ),
    )
    round_to_hour: bool | None = Field(
        default=None,
        examples=[False],
        description=(
            f"{ROUND_TO_HOUR_DESCRIPTION} {RATE_CHANGE_SCOPE_DESCRIPTION}"
        ),
    )
    status: str | None = Field(
        default=None,
        examples=[ProjectStatus.ARCHIVED.value],
        description=(
            f"{STATUS_DESCRIPTION} Set to archived to hide the project "
            "from new timers while keeping its history intact. A project "
            "whose timer is currently running cannot be archived."
        ),
    )


class TimerStartData(BaseModel):
    project_id: UUID = Field(examples=[EXAMPLE_UUID])


class TimerManualAddData(BaseModel):
    project_id: UUID = Field(examples=[EXAMPLE_UUID])
    start_time: AwareDatetime = Field(
        examples=[DATETIME_EXAMPLE],
        description=(
            f"Must not be before {MIN_TIMER_START_TEXT} or in the future. "
            f"{TZ_DESCRIPTION}"
        ),
    )
    end_time: AwareDatetime = Field(
        examples=[DATETIME_EXAMPLE],
        description=(
            f"Must be after `start_time` and not in the future. "
            f"{TZ_DESCRIPTION}"
        ),
    )


class TimerUpdateData(BaseModel):
    project_id: UUID | None = Field(default=None, examples=[EXAMPLE_UUID])
    start_time: AwareDatetime | None = Field(
        default=None,
        examples=[DATETIME_EXAMPLE],
        description=(
            f"Must not be before {MIN_TIMER_START_TEXT} or in the future. "
            f"Omit it to keep the current start time. {TZ_DESCRIPTION}"
        ),
    )
    end_time: AwareDatetime | None = Field(
        default=None,
        examples=[DATETIME_EXAMPLE],
        description=(
            f"Must be after `start_time` and not in the future. Omit it to "
            f"keep the current end time. {TZ_DESCRIPTION}"
        ),
    )


class TimerBulkDeleteData(BaseModel):
    ids: list[UUID] = Field(
        min_length=1,
        examples=[[EXAMPLE_UUID]],
    )


class TimerRunningData(BaseModel):
    id: UUID = Field(examples=[EXAMPLE_UUID])
    start_time: datetime = Field(examples=[DATETIME_EXAMPLE])
    hourly_rate: Decimal | None = Field(
        examples=["50.00"],
        description=(
            f"{RATE_SNAPSHOT_DESCRIPTION} Stopping the timer bills it at "
            f"this rate, even if the project's rate changed while the "
            f"timer was running."
        ),
    )
    round_to_hour: bool = Field(
        examples=[False],
        description=f"{ROUND_TO_HOUR_DESCRIPTION} {RATE_SNAPSHOT_DESCRIPTION}",
    )
    user_id: UUID = Field(examples=[EXAMPLE_UUID])
    project_id: UUID = Field(examples=[EXAMPLE_UUID])


class TimerData(BaseModel):
    id: UUID = Field(examples=[EXAMPLE_UUID])
    start_time: datetime = Field(examples=[DATETIME_EXAMPLE])
    end_time: datetime | None = Field(
        examples=[DATETIME_EXAMPLE],
        description="`null` while the timer is running.",
    )
    duration: timedelta | None = Field(
        examples=["PT1H30M"],
        description="`null` while the timer is running.",
    )
    hourly_rate: Decimal | None = Field(
        examples=["50.00"],
        description=RATE_SNAPSHOT_DESCRIPTION,
    )
    round_to_hour: bool = Field(
        examples=[False],
        description=f"{ROUND_TO_HOUR_DESCRIPTION} {RATE_SNAPSHOT_DESCRIPTION}",
    )
    billable_amount: Decimal | None = Field(
        examples=["75.00"],
        description=(
            "`null` while the timer is running or when the timer has no "
            "hourly rate. Computed from the entry's own `hourly_rate` and "
            "`round_to_hour` when the timer is stopped, when a manual "
            "entry is added, and again whenever the entry is edited via "
            "`PATCH /api/timers/{timer_id}`."
        ),
    )
    user_id: UUID = Field(examples=[EXAMPLE_UUID])
    project_id: UUID = Field(examples=[EXAMPLE_UUID])

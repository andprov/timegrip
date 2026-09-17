from timegrip.entities.exceptions import DomainError


class AppError(DomainError):
    code = "app_error"


class UserAlreadyExistsError(AppError):
    code = "user_already_exists"


class UserNotFoundError(AppError):
    code = "user_not_found"


class InvalidCredentialsError(AppError):
    code = "invalid_credentials"


class UnauthorizedError(AppError):
    code = "unauthorized"


class WeakPasswordError(AppError):
    code = "weak_password"


class AccessDeniedError(AppError):
    code = "access_denied"


class InvalidActivationCodeError(AppError):
    code = "invalid_activation_code"


class ActivationCodeRecentlySentError(AppError):
    code = "activation_code_recently_sent"

    def __init__(
        self,
        message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class InvalidPasswordResetCodeError(AppError):
    code = "invalid_password_reset_code"


class InvalidRefreshTokenError(AppError):
    code = "invalid_refresh_token"


class RefreshTokenNotFoundError(AppError):
    code = "refresh_token_not_found"


class UserAlreadyActiveError(AppError):
    code = "user_already_active"


class ProjectNotFoundError(AppError):
    code = "project_not_found"


class InvalidProjectColorError(AppError):
    code = "invalid_project_color"


class InvalidProjectStatusError(AppError):
    code = "invalid_project_status"


class ProjectArchivedError(AppError):
    code = "project_archived"


class ProjectHasRunningTimerError(AppError):
    code = "project_has_running_timer"


class InvalidTimeFormatError(AppError):
    code = "invalid_time_format"


class InvalidLocaleError(AppError):
    code = "invalid_locale"


class TimerNotFoundError(AppError):
    code = "timer_not_found"


class TimerAlreadyRunningError(AppError):
    code = "timer_already_running"


class TimerNotRunningError(AppError):
    code = "timer_not_running"


class TimerOverlapError(AppError):
    code = "timer_overlap"


class TimerRunningError(AppError):
    code = "timer_running"

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from starlette.exceptions import HTTPException as StarletteHTTPException

from timegrip.application.exceptions import (
    AccessDeniedError,
    ActivationCodeRecentlySentError,
    InvalidActivationCodeError,
    InvalidCredentialsError,
    InvalidLocaleError,
    InvalidPasswordResetCodeError,
    InvalidProjectColorError,
    InvalidProjectStatusError,
    InvalidRefreshTokenError,
    InvalidTimeFormatError,
    ProjectArchivedError,
    ProjectHasRunningTimerError,
    ProjectNotFoundError,
    RefreshTokenNotFoundError,
    TimerAlreadyRunningError,
    TimerNotFoundError,
    TimerNotRunningError,
    TimerOverlapError,
    TimerRunningError,
    UnauthorizedError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
)
from timegrip.entities.exceptions import (
    DomainError,
    InvalidHourlyRateError,
    InvalidTimerRangeError,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    InvalidRefreshTokenError: status.HTTP_401_UNAUTHORIZED,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    AccessDeniedError: status.HTTP_403_FORBIDDEN,
    RefreshTokenNotFoundError: status.HTTP_404_NOT_FOUND,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    ProjectNotFoundError: status.HTTP_404_NOT_FOUND,
    TimerNotFoundError: status.HTTP_404_NOT_FOUND,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    UserAlreadyActiveError: status.HTTP_409_CONFLICT,
    TimerAlreadyRunningError: status.HTTP_409_CONFLICT,
    TimerNotRunningError: status.HTTP_409_CONFLICT,
    TimerOverlapError: status.HTTP_409_CONFLICT,
    TimerRunningError: status.HTTP_409_CONFLICT,
    ProjectArchivedError: status.HTTP_409_CONFLICT,
    ProjectHasRunningTimerError: status.HTTP_409_CONFLICT,
    InvalidActivationCodeError: status.HTTP_400_BAD_REQUEST,
    InvalidPasswordResetCodeError: status.HTTP_400_BAD_REQUEST,
    WeakPasswordError: status.HTTP_400_BAD_REQUEST,
    InvalidProjectColorError: status.HTTP_400_BAD_REQUEST,
    InvalidProjectStatusError: status.HTTP_400_BAD_REQUEST,
    InvalidTimeFormatError: status.HTTP_400_BAD_REQUEST,
    InvalidLocaleError: status.HTTP_400_BAD_REQUEST,
    InvalidHourlyRateError: status.HTTP_400_BAD_REQUEST,
    InvalidTimerRangeError: status.HTTP_400_BAD_REQUEST,
    ActivationCodeRecentlySentError: status.HTTP_429_TOO_MANY_REQUESTS,
}

HEADERS_BY_ERROR: dict[type[DomainError], dict[str, str]] = {
    UnauthorizedError: {"WWW-Authenticate": "Bearer"},
}
VALIDATION_ERROR_CODE = "validation_error"
HTTP_ERROR_CODE = "http_error"
CODE_BY_STATUS: dict[int, str] = {
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
}
_LOC_PREFIXES = {"body", "query", "path", "header"}


def _error_headers(exc: DomainError) -> dict[str, str] | None:
    if (
        isinstance(exc, ActivationCodeRecentlySentError)
        and exc.retry_after_seconds is not None
    ):
        return {"Retry-After": str(exc.retry_after_seconds)}
    return HEADERS_BY_ERROR.get(type(exc))


def _format_validation_error(exc: RequestValidationError) -> str:
    parts = []
    for error in exc.errors():
        field = ".".join(
            str(segment)
            for segment in error["loc"]
            if segment not in _LOC_PREFIXES
        )
        parts.append(f"{field}: {error['msg']}" if field else error["msg"])
    return "; ".join(parts)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=STATUS_BY_ERROR.get(
                type(exc),
                status.HTTP_400_BAD_REQUEST,
            ),
            content={"detail": str(exc), "code": exc.code},
            headers=_error_headers(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> Response:
        if not is_body_allowed_for_status_code(exc.status_code):
            return Response(status_code=exc.status_code, headers=exc.headers)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": CODE_BY_STATUS.get(exc.status_code, HTTP_ERROR_CODE),
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": _format_validation_error(exc),
                "code": VALIDATION_ERROR_CODE,
            },
        )

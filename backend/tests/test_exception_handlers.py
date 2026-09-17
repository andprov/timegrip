import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from timegrip.application import exceptions as app_exceptions
from timegrip.application.exceptions import (
    ActivationCodeRecentlySentError,
    AppError,
)
from timegrip.entities import exceptions as domain_exceptions
from timegrip.entities.exceptions import DomainError, InvalidTimerRangeError
from timegrip.infrastructure.http.exception_handlers import (
    HTTP_ERROR_CODE,
    STATUS_BY_ERROR,
    VALIDATION_ERROR_CODE,
    register_exception_handlers,
)


def _error_type(name):
    return getattr(app_exceptions, name, None) or getattr(
        domain_exceptions,
        name,
    )


async def _raise_error(name: str):
    raise _error_type(name)("Something went wrong")


async def _raise_error_with_retry_after():
    raise ActivationCodeRecentlySentError(
        "Activation code was sent recently, try again later",
        retry_after_seconds=42,
    )


async def _raise_error_with_custom_code():
    raise InvalidTimerRangeError(
        "End time must be after start time",
        code="end_time_before_start",
    )


class _ValidationBody(BaseModel):
    name: str
    count: int = Field(ge=1)


async def _validate_body(body: _ValidationBody):
    return {"ok": True}


async def _validate_path_param(value: int):
    return {"value": value}


async def _raise_http_exception():
    raise HTTPException(status_code=418, detail="I'm a teapot")


@pytest.fixture
def client():
    app = FastAPI()
    register_exception_handlers(app=app)
    app.add_api_route("/errors/{name}", _raise_error)
    app.add_api_route("/validate", _validate_body, methods=["POST"])
    app.add_api_route("/validate-path/{value}", _validate_path_param)
    app.add_api_route("/custom-code", _raise_error_with_custom_code)
    app.add_api_route("/retry-after", _raise_error_with_retry_after)
    app.add_api_route("/http-exception", _raise_http_exception)
    return TestClient(app)


def _concrete_errors():
    return [
        value
        for module in (domain_exceptions, app_exceptions)
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, DomainError)
        and value not in (DomainError, AppError)
        and value.__module__ == module.__name__
    ]


@pytest.mark.parametrize(
    "error_type",
    _concrete_errors(),
    ids=lambda error_type: error_type.__name__,
)
def test_every_domain_error_has_explicit_status(error_type):
    assert error_type in STATUS_BY_ERROR


@pytest.mark.parametrize(
    ("name", "status_code"),
    [
        ("InvalidCredentialsError", 401),
        ("InvalidRefreshTokenError", 401),
        ("UnauthorizedError", 401),
        ("AccessDeniedError", 403),
        ("RefreshTokenNotFoundError", 404),
        ("UserNotFoundError", 404),
        ("ProjectNotFoundError", 404),
        ("TimerNotFoundError", 404),
        ("UserAlreadyExistsError", 409),
        ("UserAlreadyActiveError", 409),
        ("TimerAlreadyRunningError", 409),
        ("TimerNotRunningError", 409),
        ("TimerOverlapError", 409),
        ("TimerRunningError", 409),
        ("ProjectArchivedError", 409),
        ("ProjectHasRunningTimerError", 409),
        ("InvalidActivationCodeError", 400),
        ("InvalidPasswordResetCodeError", 400),
        ("WeakPasswordError", 400),
        ("InvalidProjectColorError", 400),
        ("InvalidProjectStatusError", 400),
        ("InvalidTimeFormatError", 400),
        ("InvalidLocaleError", 400),
        ("InvalidHourlyRateError", 400),
        ("InvalidTimerRangeError", 400),
        ("ActivationCodeRecentlySentError", 429),
    ],
)
def test_domain_error_response(client, name, status_code):
    response = client.get(f"/errors/{name}")
    assert response.status_code == status_code
    assert response.json() == {
        "detail": "Something went wrong",
        "code": _error_type(name).code,
    }
    if name == "UnauthorizedError":
        assert response.headers["www-authenticate"] == "Bearer"
    else:
        assert "www-authenticate" not in response.headers
    assert "retry-after" not in response.headers


def test_domain_error_response_sets_retry_after(client):
    response = client.get("/retry-after")
    assert response.status_code == 429
    assert response.json() == {
        "detail": "Activation code was sent recently, try again later",
        "code": "activation_code_recently_sent",
    }
    assert response.headers["retry-after"] == "42"


def test_domain_error_response_uses_instance_code(client):
    response = client.get("/custom-code")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "End time must be after start time",
        "code": "end_time_before_start",
    }


def test_unmapped_domain_error_falls_back_to_bad_request(client):
    response = client.get("/errors/AppError")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Something went wrong",
        "code": "app_error",
    }


def test_validation_error_uses_same_envelope_as_domain_errors(client):
    response = client.post("/validate", json={"name": "x", "count": 0})
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"detail", "code"}
    assert body["code"] == VALIDATION_ERROR_CODE
    assert "count" in body["detail"]


def test_validation_error_reports_missing_field(client):
    response = client.post("/validate", json={"count": 5})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == VALIDATION_ERROR_CODE
    assert "name" in body["detail"]


def test_validation_error_joins_every_failing_field(client):
    response = client.post("/validate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == VALIDATION_ERROR_CODE
    assert "name" in body["detail"]
    assert "count" in body["detail"]
    assert "; " in body["detail"]


def test_validation_error_on_path_param_omits_loc_prefix(client):
    response = client.get("/validate-path/not-a-number")
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == VALIDATION_ERROR_CODE
    assert body["detail"].startswith("value:")


def test_unknown_route_uses_same_envelope(client):
    response = client.get("/unknown")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found", "code": "not_found"}


def test_method_not_allowed_uses_same_envelope(client):
    response = client.put("/validate")
    assert response.status_code == 405
    assert response.json() == {
        "detail": "Method Not Allowed",
        "code": "method_not_allowed",
    }
    assert response.headers["allow"] == "POST"


def test_other_http_exception_falls_back_to_http_error_code(client):
    response = client.get("/http-exception")
    assert response.status_code == 418
    assert response.json() == {
        "detail": "I'm a teapot",
        "code": HTTP_ERROR_CODE,
    }

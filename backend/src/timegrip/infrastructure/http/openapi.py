from typing import Any

from fastapi import FastAPI

from timegrip.infrastructure.http.exception_handlers import (
    VALIDATION_ERROR_CODE,
)

_VALIDATION_ERROR_DESCRIPTION = (
    "Validation Error. `detail` is a human-readable summary of the "
    "problems, separated by `; `, usually in the form `field: message`."
)
_MISSING_FIELD_MESSAGE = "Field required"
_INVALID_UUID_MESSAGE = (
    "Input should be a valid UUID, invalid length: expected length 32 for "
    "simple format, found 3"
)
_INVALID_INTEGER_MESSAGE = (
    "Input should be a valid integer, unable to parse string as an integer"
)


def _validation_error_detail(
    operation: dict[str, Any],
    schemas: dict[str, Any],
) -> str | None:
    body_ref = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref")
    )
    if body_ref:
        body_schema = schemas.get(body_ref.rsplit("/", 1)[-1], {})
        required = body_schema.get("required", [])
        if required:
            return f"{required[0]}: {_MISSING_FIELD_MESSAGE}"

    parameters = operation.get("parameters", [])
    for parameter in parameters:
        if parameter.get("in") != "path":
            continue
        name = parameter["name"]
        param_schema = parameter.get("schema", {})
        if param_schema.get("format") == "uuid":
            return f"{name}: {_INVALID_UUID_MESSAGE}"
        if param_schema.get("type") == "integer":
            return f"{name}: {_INVALID_INTEGER_MESSAGE}"

    for parameter in parameters:
        minimum = parameter.get("schema", {}).get("minimum")
        if parameter.get("in") == "query" and minimum is not None:
            return (
                f"{parameter['name']}: Input should be greater than or "
                f"equal to {minimum}"
            )

    return None


def _rewrite_validation_error_responses(schema: dict[str, Any]) -> None:
    schemas = schema.get("components", {}).get("schemas", {})
    touched_any = False
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not responses or "422" not in responses:
                continue
            touched_any = True
            content: dict[str, Any] = {
                "schema": {
                    "$ref": "#/components/schemas/HTTPError",
                },
            }
            detail = _validation_error_detail(operation, schemas)
            if detail is not None:
                content["example"] = {
                    "detail": detail,
                    "code": VALIDATION_ERROR_CODE,
                }
            responses["422"] = {
                "description": _VALIDATION_ERROR_DESCRIPTION,
                "content": {"application/json": content},
            }

    if not touched_any:
        return

    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)


def setup_custom_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = FastAPI.openapi(app)
        _rewrite_validation_error_responses(schema)
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

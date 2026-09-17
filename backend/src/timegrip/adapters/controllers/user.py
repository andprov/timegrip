import textwrap

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request, Response, status

from timegrip.adapters.common.token_id_provider import JWTTokenManager
from timegrip.adapters.controllers.request_info import client_ip
from timegrip.adapters.controllers.schemas import (
    EXAMPLE_UUID,
    PASSWORD_DESCRIPTION,
    RETRY_AFTER_HEADERS,
    UNAUTHORIZED_HEADERS,
    WEAK_PASSWORD_EXAMPLES,
    ActivationCodeData,
    HTTPError,
    ResendCooldownData,
    SessionData,
    TokenPairData,
    UserData,
    UserEmailUpdateData,
    UserLocaleUpdateData,
    UserPasswordUpdateData,
    UserTimeFormatUpdateData,
)
from timegrip.application.auth.refresh_token_manager import (
    RefreshTokenManager,
)
from timegrip.application.common.id_provider_gateway import (
    IdProviderGateway,
)
from timegrip.application.user.activate_user import (
    ActivateUserInteractor,
    ActivateUserRequestDTO,
)
from timegrip.application.user.delete_user import DeleteUserInteractor
from timegrip.application.user.get_user import GetUserByIdInteractor
from timegrip.application.user.update_email import (
    UpdateEmailInteractor,
    UpdateEmailRequestDTO,
)
from timegrip.application.user.update_locale import (
    UpdateLocaleInteractor,
    UpdateLocaleRequestDTO,
)
from timegrip.application.user.update_password import (
    UpdatePasswordInteractor,
    UpdatePasswordRequestDTO,
)
from timegrip.application.user.update_time_format import (
    UpdateTimeFormatInteractor,
    UpdateTimeFormatRequestDTO,
)
from timegrip.application.user_activation.get_resend_cooldown import (
    GetResendCooldownInteractor,
)
from timegrip.application.user_activation.resend_activation_code import (
    ResendActivationCodeInteractor,
)

user_router = APIRouter()


@user_router.get(
    path="/me",
    summary="Get current user",
    description=textwrap.dedent("""\
        Return the profile of the authenticated user. Requires a valid Bearer
        token in the `Authorization` header.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def get_current_user(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetUserByIdInteractor],
) -> UserData:
    current_user_id = id_provider.get_id()
    user = await interactor(current_user_id=current_user_id)
    return UserData(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        time_format=user.time_format,
        locale=user.locale,
    )


@user_router.post(
    path="/me/activate",
    summary="Activate current user",
    description=textwrap.dedent("""\
        Activate the authenticated user's account using the code sent
        by email after registration. Requires a valid Bearer token in the
        `Authorization` header.

        The code is invalidated after 5 wrong attempts. Request a new one
        via `POST /api/users/me/activate/resend`.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired code",
                        "code": "invalid_activation_code",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User is already active",
                        "code": "user_already_active",
                    },
                },
            },
        },
    },
)
@inject
async def activate_current_user(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[ActivateUserInteractor],
    activation_code_data: ActivationCodeData,
) -> Response:
    current_user_id = id_provider.get_id()
    activate_dto = ActivateUserRequestDTO(code=activation_code_data.code)
    await interactor(
        current_user_id=current_user_id,
        activate_dto=activate_dto,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_router.post(
    path="/me/activate/resend",
    summary="Resend activation code",
    description=textwrap.dedent("""\
        Send a new activation code to the authenticated user's email, replacing
        any previously issued code. Requires a valid Bearer token in the
        `Authorization` header.

        A new code can be requested at most once per minute. An earlier
        request is rejected with `429 Too Many Requests`, the `Retry-After`
        header holds the number of seconds to wait, and the previously
        issued code stays valid. The wait time can be checked beforehand via
        `GET /api/users/me/activate/resend-cooldown`.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User is already active",
                        "code": "user_already_active",
                    },
                },
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too Many Requests",
            "model": HTTPError,
            "headers": RETRY_AFTER_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Activation code was sent recently, "
                            "try again later"
                        ),
                        "code": "activation_code_recently_sent",
                    },
                },
            },
        },
    },
)
@inject
async def resend_activation_code(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[ResendActivationCodeInteractor],
) -> Response:
    current_user_id = id_provider.get_id()
    await interactor(current_user_id=current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_router.get(
    path="/me/activate/resend-cooldown",
    summary="Get activation code resend cooldown",
    description=textwrap.dedent("""\
        Return how many seconds the authenticated user has to wait before a
        new activation code can be requested via
        `POST /api/users/me/activate/resend`. Requires a valid Bearer token in
        the `Authorization` header.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User is already active",
                        "code": "user_already_active",
                    },
                },
            },
        },
    },
)
@inject
async def get_resend_cooldown(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[GetResendCooldownInteractor],
) -> ResendCooldownData:
    current_user_id = id_provider.get_id()
    cooldown = await interactor(current_user_id=current_user_id)
    return ResendCooldownData(
        retry_after_seconds=cooldown.retry_after_seconds,
    )


@user_router.get(
    path="/me/sessions",
    summary="List active sessions",
    description=textwrap.dedent("""\
        List the authenticated user's active sessions (one per
        non-expired, non-revoked refresh token), most recent first, with
        the device and IP address recorded when each was issued or last
        refreshed. Requires a valid Bearer token in the `Authorization`
        header.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
    },
)
@inject
async def list_sessions(
    id_provider: FromDishka[IdProviderGateway],
    refresh_token_manager: FromDishka[RefreshTokenManager],
) -> list[SessionData]:
    current_user_id = id_provider.get_id()
    sessions = await refresh_token_manager.list_active_sessions(
        user_id=current_user_id,
    )
    return [
        SessionData(
            id=session.id,
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            created_at=session.created_at,
        )
        for session in sessions
    ]


@user_router.patch(
    path="/me/password",
    summary="Update password",
    description=textwrap.dedent(f"""\
        Change the authenticated user's password. Requires the current password
        for confirmation and a valid Bearer token in the `Authorization`
        header.

        New password requirements: {PASSWORD_DESCRIPTION}

        On success every session of the user is revoked, including the
        current one, and a fresh access-token and refresh-token pair is
        returned for this client. Other clients lose access once their
        access token expires.
        """),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": WEAK_PASSWORD_EXAMPLES,
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Missing or invalid access token",
                            "value": {
                                "detail": "Unauthorized",
                                "code": "unauthorized",
                            },
                        },
                        "invalid_current_password": {
                            "summary": "Wrong current password",
                            "value": {
                                "detail": "Invalid current password",
                                "code": "invalid_current_password",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def update_password(
    request: Request,
    id_provider: FromDishka[IdProviderGateway],
    token_manager: FromDishka[JWTTokenManager],
    refresh_token_manager: FromDishka[RefreshTokenManager],
    interactor: FromDishka[UpdatePasswordInteractor],
    user_password_update_data: UserPasswordUpdateData,
) -> TokenPairData:
    current_user_id = id_provider.get_id()
    update_password_dto = UpdatePasswordRequestDTO(
        current_password=user_password_update_data.current_password,
        new_password=user_password_update_data.new_password,
    )
    await interactor(
        current_user_id=current_user_id,
        update_password_dto=update_password_dto,
    )
    access_token = token_manager.create_token(user_id=current_user_id)
    refresh_token = await refresh_token_manager.issue(
        user_id=current_user_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    return TokenPairData(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@user_router.patch(
    path="/me/email",
    summary="Update email",
    description=textwrap.dedent("""\
        Change the authenticated user's email. Requires the current password
        for confirmation and a valid Bearer token in the `Authorization`
        header.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Missing or invalid access token",
                            "value": {
                                "detail": "Unauthorized",
                                "code": "unauthorized",
                            },
                        },
                        "invalid_password": {
                            "summary": "Wrong password",
                            "value": {
                                "detail": "Invalid password",
                                "code": "invalid_password",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "User with email example@example.com already"
                            " exists"
                        ),
                        "code": "user_already_exists",
                    },
                },
            },
        },
    },
)
@inject
async def update_email(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[UpdateEmailInteractor],
    user_email_update_data: UserEmailUpdateData,
) -> UserData:
    current_user_id = id_provider.get_id()
    update_email_dto = UpdateEmailRequestDTO(
        password=user_email_update_data.password,
        new_email=user_email_update_data.new_email,
    )
    user = await interactor(
        current_user_id=current_user_id,
        update_email_dto=update_email_dto,
    )
    return UserData(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        time_format=user.time_format,
        locale=user.locale,
    )


@user_router.patch(
    path="/me/time-format",
    summary="Update time format preference",
    description=textwrap.dedent("""\
        Change how the authenticated user's time is displayed on the frontend:
        `12h` or `24h`. Requires a valid Bearer token in the `Authorization`
        header.
        """),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Time format must be one of ...",
                        "code": "invalid_time_format",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def update_time_format(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[UpdateTimeFormatInteractor],
    user_time_format_update_data: UserTimeFormatUpdateData,
) -> UserData:
    current_user_id = id_provider.get_id()
    update_time_format_dto = UpdateTimeFormatRequestDTO(
        time_format=user_time_format_update_data.time_format,
    )
    user = await interactor(
        current_user_id=current_user_id,
        update_time_format_dto=update_time_format_dto,
    )
    return UserData(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        time_format=user.time_format,
        locale=user.locale,
    )


@user_router.patch(
    path="/me/locale",
    summary="Update UI locale preference",
    description=textwrap.dedent("""\
        Change the authenticated user's UI locale, so it stays in sync
        across devices. Requires a valid Bearer token in the
        `Authorization` header.
        """),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Locale must be one of ...",
                        "code": "invalid_locale",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def update_locale(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[UpdateLocaleInteractor],
    user_locale_update_data: UserLocaleUpdateData,
) -> UserData:
    current_user_id = id_provider.get_id()
    update_locale_dto = UpdateLocaleRequestDTO(
        locale=user_locale_update_data.locale,
    )
    user = await interactor(
        current_user_id=current_user_id,
        update_locale_dto=update_locale_dto,
    )
    return UserData(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        time_format=user.time_format,
        locale=user.locale,
    )


@user_router.delete(
    path="/me",
    summary="Delete current user",
    description=textwrap.dedent("""\
        Permanently delete the authenticated user's account together with all
        of its data: every project, every time entry including a running timer,
        and every session. This cannot be undone. Returns no content on
        success. Requires a valid Bearer token in the `Authorization` header.

        All refresh tokens are deleted, so `POST /api/auth/refresh` fails for
        every client. An access token already issued stays valid until it
        expires, but the account it belongs to no longer exists.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"User with id {EXAMPLE_UUID} not found",
                        "code": "user_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def delete_current_user(
    id_provider: FromDishka[IdProviderGateway],
    interactor: FromDishka[DeleteUserInteractor],
) -> Response:
    current_user_id = id_provider.get_id()
    await interactor(current_user_id=current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_router.delete(
    path="/me/sessions/{session_id}",
    summary="Revoke a session",
    description=textwrap.dedent("""\
        Revoke a single session by id, immediately invalidating its
        refresh token. Requires a valid Bearer token in the
        `Authorization` header.

        Session ids change on every refresh, so use an id from a fresh
        `GET /api/users/me/sessions` response. An outdated id, or the id of
        a session that is already revoked, returns `404`.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session not found",
                        "code": "refresh_token_not_found",
                    },
                },
            },
        },
    },
)
@inject
async def revoke_session(
    session_id: int,
    id_provider: FromDishka[IdProviderGateway],
    refresh_token_manager: FromDishka[RefreshTokenManager],
) -> Response:
    current_user_id = id_provider.get_id()
    await refresh_token_manager.revoke_session(
        user_id=current_user_id,
        session_id=session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_router.delete(
    path="/me/sessions",
    summary="Revoke all sessions",
    description=textwrap.dedent("""\
        Revoke every session for the authenticated user, invalidating all
        refresh tokens at once. An access token already issued for a
        session remains valid until it naturally expires — this only
        blocks it from being refreshed further. Requires a valid Bearer
        token in the `Authorization` header.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": HTTPError,
            "headers": UNAUTHORIZED_HEADERS,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized",
                        "code": "unauthorized",
                    },
                },
            },
        },
    },
)
@inject
async def revoke_all_sessions(
    id_provider: FromDishka[IdProviderGateway],
    refresh_token_manager: FromDishka[RefreshTokenManager],
) -> Response:
    current_user_id = id_provider.get_id()
    await refresh_token_manager.revoke_all(user_id=current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

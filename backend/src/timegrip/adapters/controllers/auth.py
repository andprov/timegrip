import textwrap

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request, Response, status

from timegrip.adapters.common.token_id_provider import JWTTokenManager
from timegrip.adapters.controllers.request_info import client_ip
from timegrip.adapters.controllers.schemas import (
    PASSWORD_DESCRIPTION,
    WEAK_PASSWORD_EXAMPLES,
    HTTPError,
    LoginData,
    PasswordForgotData,
    PasswordResetData,
    RefreshTokenRequestData,
    TokenPairData,
    UserAddData,
    UserData,
)
from timegrip.application.auth.add_user import (
    AddUserInteractor,
    AddUserRequestDTO,
)
from timegrip.application.auth.login import (
    AuthRequestDTO,
    AuthUserInteractor,
)
from timegrip.application.auth.refresh_token_manager import RefreshTokenManager
from timegrip.application.password_reset.forgot_password import (
    ForgotPasswordInteractor,
)
from timegrip.application.password_reset.reset_password import (
    ResetPasswordInteractor,
    ResetPasswordRequestDTO,
)

auth_router = APIRouter()


@auth_router.post(
    path="/signup",
    summary="Sign up",
    description=textwrap.dedent(f"""\
        Register a new user with email and password.

        Password requirements: {PASSWORD_DESCRIPTION}
        """),
    status_code=status.HTTP_201_CREATED,
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
async def add_user(
    interactor: FromDishka[AddUserInteractor],
    user_add_data: UserAddData,
) -> UserData:
    add_user_dto = AddUserRequestDTO(
        email=user_add_data.email,
        password=user_add_data.password,
        locale=user_add_data.locale,
    )
    user = await interactor(add_user_dto=add_user_dto)
    return UserData(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        time_format=user.time_format,
        locale=user.locale,
    )


@auth_router.post(
    path="/signin",
    summary="Sign in",
    description=textwrap.dedent("""\
        Authenticate a user with email and password. Returns an
        access-token and a refresh-token.

        Send the access-token as a Bearer token in the `Authorization`
        header to call protected endpoints. The refresh-token is not a
        Bearer token: send it in the request body of
        `POST /api/auth/refresh` to get a new token pair when the
        access-token expires, or of `POST /api/auth/logout` to end the
        session.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid email or password",
                        "code": "invalid_credentials",
                    },
                },
            },
        },
    },
)
@inject
async def login(
    request: Request,
    token_manager: FromDishka[JWTTokenManager],
    refresh_token_manager: FromDishka[RefreshTokenManager],
    interactor: FromDishka[AuthUserInteractor],
    login_data: LoginData,
) -> TokenPairData:
    auth_dto = AuthRequestDTO(
        email=login_data.email,
        password=login_data.password,
    )
    user_id = await interactor(auth_dto=auth_dto)
    access_token = token_manager.create_token(user_id=user_id)
    refresh_token = await refresh_token_manager.issue(
        user_id=user_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    return TokenPairData(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post(
    path="/refresh",
    summary="Refresh session",
    description=textwrap.dedent("""\
        Exchange a refresh token for a fresh access-token and
        refresh-token pair, extending the session. Every refresh replaces
        the refresh token, so use the new one for the next refresh.

        A refresh token ended explicitly — by `POST /api/auth/logout`, by
        revoking its session, or by a password change or reset — is
        rejected immediately, as is an unknown or expired one.
        """),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid refresh token",
                        "code": "invalid_refresh_token",
                    },
                },
            },
        },
    },
)
@inject
async def refresh(
    request: Request,
    token_manager: FromDishka[JWTTokenManager],
    refresh_token_manager: FromDishka[RefreshTokenManager],
    refresh_data: RefreshTokenRequestData,
) -> TokenPairData:
    rotated = await refresh_token_manager.rotate(
        raw_token=refresh_data.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    access_token = token_manager.create_token(user_id=rotated.user_id)
    return TokenPairData(
        access_token=access_token,
        refresh_token=rotated.refresh_token,
    )


@auth_router.post(
    path="/logout",
    summary="Log out",
    description=textwrap.dedent("""\
        Revoke the given refresh token, ending that session immediately:
        neither this token nor the ones it replaced can be used to refresh
        again. Always succeeds, even if the refresh token is already
        invalid.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def logout(
    refresh_token_manager: FromDishka[RefreshTokenManager],
    refresh_data: RefreshTokenRequestData,
) -> Response:
    await refresh_token_manager.revoke(raw_token=refresh_data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post(
    path="/password/forgot",
    summary="Forgot password",
    description=textwrap.dedent("""\
        Request a password reset code by email. Always responds with no
        content, whether or not an account with that email exists.

        If the account exists, a reset code is emailed. Submit it via
        `POST /api/auth/password/reset` along with a new password. The code
        expires after 15 minutes and is invalidated after 5 wrong attempts.

        A new code is emailed at most once per minute. A repeated request
        within that minute sends nothing and the previously issued code
        stays valid.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def forgot_password(
    interactor: FromDishka[ForgotPasswordInteractor],
    password_forgot_data: PasswordForgotData,
) -> Response:
    await interactor(email=password_forgot_data.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post(
    path="/password/reset",
    summary="Reset password",
    description=textwrap.dedent(f"""\
        Set a new password using the reset code emailed via
        `POST /api/auth/password/forgot`.

        New password requirements: {PASSWORD_DESCRIPTION}

        On success every session of the user is revoked, so all clients
        must sign in again with the new password. Access tokens already
        issued stay valid until they naturally expire.
        """),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": HTTPError,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_code": {
                            "summary": "Invalid or expired code",
                            "value": {
                                "detail": "Invalid or expired code",
                                "code": "invalid_password_reset_code",
                            },
                        },
                        **WEAK_PASSWORD_EXAMPLES,
                    },
                },
            },
        },
    },
)
@inject
async def reset_password(
    interactor: FromDishka[ResetPasswordInteractor],
    password_reset_data: PasswordResetData,
) -> Response:
    reset_dto = ResetPasswordRequestDTO(
        email=password_reset_data.email,
        code=password_reset_data.code,
        new_password=password_reset_data.new_password,
    )
    await interactor(reset_dto=reset_dto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

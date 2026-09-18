import textwrap
from importlib.metadata import version

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from timegrip.infrastructure.env_loader import get_env_value
from timegrip.infrastructure.http.cors import setup_cors
from timegrip.infrastructure.http.docs import setup_docs
from timegrip.infrastructure.http.exception_handlers import (
    register_exception_handlers,
)
from timegrip.infrastructure.http.openapi import setup_custom_openapi
from timegrip.infrastructure.http.routes import openapi_tags, setup_routes


def _build_api_description() -> str:
    return textwrap.dedent("""\
        TimeGrip is a REST API for tracking time spent on projects.
        Register an account, organize your work into projects, and
        start or stop timers to measure exactly how much time goes
        into each one.

        ## Authentication

        Most endpoints require a JWT access token. Obtain one via
        `POST /api/auth/signin` and send it as a Bearer token in
        the `Authorization` header: `Authorization: Bearer <token>`.

        The `Bearer` scheme name is case-insensitive, but it is
        required: a raw token without the scheme, another scheme
        (such as `Basic`), or the scheme without a token is rejected.
        A missing, malformed, invalid, or expired access token results
        in `401 Unauthorized` with the error code `unauthorized` and a
        `WWW-Authenticate: Bearer` response header.

        ## Activation

        Newly registered accounts start inactive and can only
        access the `Users` endpoints. An activation code is emailed
        on signup — submit it via `POST /api/users/me/activate` to
        activate the account, or request a new one via
        `POST /api/users/me/activate/resend`. Projects and timers
        become available once the account is activated.

        ## Resources

        - [**Auth**](#tag/auth) — register and sign in
        - [**Users**](#tag/users) — manage the authenticated
          user's own account
        - [**Projects**](#tag/projects) — list, view, create,
          update, archive, and delete projects
        - [**Timers**](#tag/timers) — start, stop, inspect, and
          manually add or edit time entries
        """)


def get_fastapi_app(container: AsyncContainer) -> FastAPI:
    debug = get_env_value(key="DEBUG", default="False") == "True"
    docs_url = "/api/swagger" if debug else None
    redoc_url = "/api/redoc" if debug else None

    fastapi_app = FastAPI(
        title="TimeGrip API",
        version=version("timegrip"),
        description=_build_api_description(),
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url="/api/openapi.json",
        openapi_tags=openapi_tags,
        redirect_slashes=False,
    )

    setup_docs(app=fastapi_app, scalar_url="/api/docs", interactive=debug)
    setup_cors(app=fastapi_app)
    register_exception_handlers(app=fastapi_app)
    setup_routes(app=fastapi_app)
    setup_custom_openapi(app=fastapi_app)
    setup_dishka(container=container, app=fastapi_app)
    return fastapi_app

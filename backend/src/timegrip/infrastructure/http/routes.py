import textwrap

from fastapi import FastAPI
from fastapi.params import Depends
from fastapi.security import HTTPBearer

from timegrip.adapters.controllers.auth import auth_router
from timegrip.adapters.controllers.project import project_router
from timegrip.adapters.controllers.timer import timer_router
from timegrip.adapters.controllers.user import user_router

swagger_bearer = HTTPBearer(auto_error=False)

openapi_tags = [
    {
        "name": "auth",
        "x-displayName": "Auth",
        "description": (
            "Registration and authentication: sign up, sign in, refresh a "
            "session, log out, and password recovery."
        ),
    },
    {
        "name": "users",
        "x-displayName": "Users",
        "description": textwrap.dedent("""\
            Manage the authenticated user's own account: profile,
            activation, password, email, display preferences, active
            sessions, and account deletion.

            The user must be registered and authorized with a valid
            Bearer token in the `Authorization` header.
            """),
    },
    {
        "name": "projects",
        "x-displayName": "Projects",
        "description": textwrap.dedent("""\
            List, view, create, update, archive, and delete projects.

            The user must be registered and authorized with a valid
            Bearer token in the `Authorization` header, and the
            account must be activated.
            """),
    },
    {
        "name": "timers",
        "x-displayName": "Timers",
        "description": textwrap.dedent("""\
            Start, stop, and inspect time tracking timers, or add and
            edit manual (backdated) time entries.

            The user must be registered and authorized with a valid
            Bearer token in the `Authorization` header, and the
            account must be activated.
            """),
    },
]


def setup_routes(app: FastAPI):
    app.include_router(
        router=auth_router,
        prefix="/api/auth",
        tags=["auth"],
    )
    app.include_router(
        router=user_router,
        prefix="/api/users",
        tags=["users"],
        dependencies=[Depends(swagger_bearer)],
    )
    app.include_router(
        router=project_router,
        prefix="/api/projects",
        tags=["projects"],
        dependencies=[Depends(swagger_bearer)],
    )
    app.include_router(
        router=timer_router,
        prefix="/api/timers",
        tags=["timers"],
        dependencies=[Depends(swagger_bearer)],
    )

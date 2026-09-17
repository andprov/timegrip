from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from timegrip.infrastructure.env_loader import get_env_value


def setup_cors(app: FastAPI) -> None:
    origin = get_env_value(key="CORS_ORIGIN", default="")
    if not origin:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

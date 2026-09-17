import uvicorn

from timegrip.infrastructure.env_loader import get_env_value


def run_app() -> None:
    debug = get_env_value(key="DEBUG", default="False") == "True"
    if debug:
        workers = 1
    else:
        workers = int(get_env_value(key="WORKERS", default="1"))

    uvicorn.run(
        app="timegrip.app:get_app",
        host=get_env_value(key="HOST", default="0.0.0.0"),
        port=int(get_env_value(key="PORT", default="8000")),
        reload=debug,
        workers=workers,
        factory=True,
        log_level="debug" if debug else "info",
    )


if __name__ == "__main__":
    run_app()

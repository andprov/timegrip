from timegrip.infrastructure.di.container import create_app_container
from timegrip.infrastructure.http.server import get_fastapi_app


def get_app():
    container = create_app_container()
    return get_fastapi_app(container=container)


app = get_app()

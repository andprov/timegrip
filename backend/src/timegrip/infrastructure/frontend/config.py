from timegrip.application.common.frontend_config import FrontendConfig
from timegrip.infrastructure.env_loader import get_env_value


def load_frontend_config() -> FrontendConfig:
    return FrontendConfig(
        url=f"https://{get_env_value(key='DOMAIN')}",
    )

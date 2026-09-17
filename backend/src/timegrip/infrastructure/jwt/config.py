from timegrip.application.common.jwt_token_config import JWTTokenConfig
from timegrip.infrastructure.env_loader import get_env_value


def load_jwt_token_config() -> JWTTokenConfig:
    return JWTTokenConfig(
        secret_key=get_env_value(key="SECRET_KEY"),
        expire_time=int(get_env_value(key="EXPIRE_TIME", default="15")),
        algorithm=get_env_value(key="ALGORITHM", default="HS256"),
    )

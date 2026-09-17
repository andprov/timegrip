from dataclasses import dataclass

from timegrip.infrastructure.env_loader import get_env_value


@dataclass
class PostgresConfig:
    user: str
    password: str
    host: str
    port: str
    database: str
    echo: bool

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


def load_postgres_config() -> PostgresConfig:
    return PostgresConfig(
        user=get_env_value(key="POSTGRES_USER", default="postgres"),
        password=get_env_value(key="POSTGRES_PASSWORD", default="postgres"),
        host=get_env_value(key="DB_HOST", default="localhost"),
        port=get_env_value(key="DB_PORT", default="5432"),
        database=get_env_value(key="POSTGRES_DB", default="timegrip"),
        echo=get_env_value(key="ECHO", default="False") == "True",
    )

from dataclasses import dataclass


@dataclass
class JWTTokenConfig:
    secret_key: str
    expire_time: int
    algorithm: str

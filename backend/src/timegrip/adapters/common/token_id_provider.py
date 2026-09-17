import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param

from timegrip.application.common.id_provider_gateway import (
    IdProviderGateway,
)
from timegrip.application.common.jwt_token_config import JWTTokenConfig
from timegrip.application.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    user_id: UUID
    expire_time: datetime


class JWTTokenManager:
    def __init__(self, config: JWTTokenConfig) -> None:
        self.secret_key = config.secret_key
        self.expire_time = config.expire_time
        self.algorithm = config.algorithm

    def create_token(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(minutes=self.expire_time),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> TokenData:
        payload = jwt.decode(
            jwt=token,
            key=self.secret_key,
            algorithms=[self.algorithm],
        )
        user_id = payload["sub"]
        expire_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        return TokenData(user_id=UUID(user_id), expire_time=expire_time)


class TokenIdProvider(IdProviderGateway):
    def __init__(
        self,
        token_manager: JWTTokenManager,
        request: Request,
    ) -> None:
        self.token_manager = token_manager
        self.request = request

    def get_id(self) -> UUID:
        scheme, token = get_authorization_scheme_param(
            self.request.headers.get("authorization"),
        )
        if not scheme:
            logger.warning("Get id | [Authorization header is missing]")
            raise UnauthorizedError("Unauthorized")

        if scheme.lower() != "bearer" or not token:
            logger.warning("Get id | [Authorization scheme is not Bearer]")
            raise UnauthorizedError("Unauthorized")

        try:
            token_data = self.token_manager.decode_token(token)
            return token_data.user_id
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            KeyError,
            ValueError,
        ) as e:
            logger.warning(f"Get id | [Invalid token {e}]")
            raise UnauthorizedError("Unauthorized") from e

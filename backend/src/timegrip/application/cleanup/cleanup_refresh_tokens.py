import logging

from timegrip.application.auth.gateway import RefreshTokenGateway

logger = logging.getLogger(__name__)

REVOKED_REFRESH_TOKEN_RETENTION_DAYS = 1


class CleanupRefreshTokensInteractor:
    def __init__(self, refresh_token_gateway: RefreshTokenGateway) -> None:
        self.refresh_token_gateway = refresh_token_gateway

    async def __call__(self) -> int:
        deleted_count = (
            await self.refresh_token_gateway.delete_expired_and_old_revoked(
                revoked_retention_days=REVOKED_REFRESH_TOKEN_RETENTION_DAYS,
            )
        )
        if deleted_count:
            logger.info(f"Cleanup refresh tokens | [count: {deleted_count}]")
        return deleted_count

import asyncio
import logging

from timegrip.application.cleanup.cleanup_old_emails import (
    CleanupOldEmailsInteractor,
)
from timegrip.application.cleanup.cleanup_refresh_tokens import (
    CleanupRefreshTokensInteractor,
)
from timegrip.application.cleanup.cleanup_unconfirmed_users import (
    CleanupUnconfirmedUsersInteractor,
)
from timegrip.infrastructure.di.container import create_worker_container

logger = logging.getLogger(__name__)


async def run_cleanup() -> None:
    logging.basicConfig(level=logging.INFO)
    container = create_worker_container()
    try:
        async with container() as request_container:
            cleanup_unconfirmed_users = await request_container.get(
                CleanupUnconfirmedUsersInteractor,
            )
            await cleanup_unconfirmed_users()

            cleanup_old_emails = await request_container.get(
                CleanupOldEmailsInteractor,
            )
            await cleanup_old_emails()

            cleanup_refresh_tokens = await request_container.get(
                CleanupRefreshTokensInteractor,
            )
            await cleanup_refresh_tokens()
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(run_cleanup())

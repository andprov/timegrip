import logging
from collections.abc import AsyncGenerator

import psycopg

from timegrip.adapters.db.email_queue_gateway import OUTBOX_EMAIL_CHANNEL
from timegrip.infrastructure.postgres.config import PostgresConfig

logger = logging.getLogger(__name__)


async def listen_for_outbox_notifies(
    config: PostgresConfig,
) -> AsyncGenerator[None, None]:
    conninfo = (
        f"host={config.host} port={config.port} user={config.user} "
        f"password={config.password} dbname={config.database}"
    )
    async with await psycopg.AsyncConnection.connect(
        conninfo,
        autocommit=True,
    ) as conn:
        await conn.execute(f"LISTEN {OUTBOX_EMAIL_CHANNEL}")
        logger.info(f"Listening on channel | [{OUTBOX_EMAIL_CHANNEL}]")
        async for _ in conn.notifies():
            yield None

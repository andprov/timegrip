import asyncio
import contextlib
import logging
import signal

from dishka import AsyncContainer

from timegrip.application.outbox.send_pending_emails import (
    SendPendingEmailsInteractor,
)
from timegrip.infrastructure.di.container import create_worker_container
from timegrip.infrastructure.postgres.config import load_postgres_config
from timegrip.infrastructure.postgres.listener import (
    listen_for_outbox_notifies,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


async def process_pending(container: AsyncContainer) -> None:
    async with container() as request_container:
        interactor = await request_container.get(SendPendingEmailsInteractor)
        processed = await interactor()
    if processed:
        logger.info(f"Processed outbox emails | [count: {processed}]")


async def poll_loop(container: AsyncContainer) -> None:
    while True:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        try:
            await process_pending(container)
        except Exception:
            logger.exception("Outbox poll failed")


async def listen_loop(container: AsyncContainer) -> None:
    postgres_config = load_postgres_config()
    async for _ in listen_for_outbox_notifies(postgres_config):
        try:
            await process_pending(container)
        except Exception:
            logger.exception("Outbox notify handling failed")


async def run_worker() -> None:
    logging.basicConfig(level=logging.INFO)
    container = create_worker_container()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await process_pending(container)
        worker_task = asyncio.gather(
            listen_loop(container),
            poll_loop(container),
        )
        await stop_event.wait()
        logger.info("Shutdown signal received, stopping worker")
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(run_worker())

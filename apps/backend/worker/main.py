"""Rollup worker entrypoint: `python -m worker.main`.

Builds the Postgres pool + Redis buffer, runs the consume loop, and shuts down
gracefully on SIGTERM/SIGINT (stop reading, let the in-flight batch finish).
"""

from __future__ import annotations

import asyncio
import logging
import signal

from app.config import get_settings
from app.core import db
from app.core import redis as redis_core
from app.core.buffer import RedisStreamBuffer

from worker.consumer import RollupConsumer


async def _run() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    log = logging.getLogger("worker")

    pool = await db.create_pool(settings)
    buffer_client = redis_core.create_buffer_client(settings)
    buffer = RedisStreamBuffer(buffer_client, settings)
    consumer = RollupConsumer(pool, buffer)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, consumer.request_stop)

    log.info("rollup worker started (group=%s)", settings.consumer_group)
    try:
        await consumer.run()
    finally:
        await db.close_pool(pool)
        await buffer_client.aclose()
        log.info("rollup worker stopped")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

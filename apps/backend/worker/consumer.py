"""Rollup worker consume loop.

XREADGROUP a batch -> persist in one transaction -> XACK only after commit. On
startup and between reads, reclaim stuck pending entries from crashed consumers
(XAUTOCLAIM). The XACK-after-COMMIT ordering is the critical correctness detail:
a crash before XACK leaves messages pending; redelivery + Postgres dedup makes
reprocessing a no-op (exactly-once effect over at-least-once delivery).
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg
from app.core.buffer import EventBuffer

from worker.rollup import persist_batch

log = logging.getLogger("worker")


class RollupConsumer:
    def __init__(self, pool: asyncpg.Pool, buffer: EventBuffer) -> None:
        self._pool = pool
        self._buffer = buffer
        self._stopping = asyncio.Event()

    def request_stop(self) -> None:
        self._stopping.set()

    async def run(self) -> None:
        await self._buffer.ensure_group()
        while not self._stopping.is_set():
            await self.run_once()

    async def run_once(self) -> int:
        """One consume iteration: reclaim idle pending entries, then read + process
        a new batch. Returns the number of messages processed.

        Reclaiming every iteration (not just at startup) re-drives entries stuck by
        a crashed peer *and* a batch this worker failed on previously: a failed
        batch is left pending (not acked), goes idle past ``claim_idle_ms``, and is
        picked back up here (review I2/I3). ``read_batch`` blocks up to
        ``block_ms``, so this loop does not busy-spin.
        """
        processed = 0
        reclaimed = await self._buffer.autoclaim()
        if reclaimed:
            await self._process(reclaimed)
            processed += len(reclaimed)
        messages = await self._buffer.read_batch()
        if messages:
            await self._process(messages)
            processed += len(messages)
        return processed

    async def _process(self, messages) -> None:
        if not messages:
            return
        try:
            await persist_batch(self._pool, messages)
        except Exception:
            # Do NOT ack: messages stay pending and will be redelivered / reclaimed.
            log.exception("batch failed; leaving %d messages pending", len(messages))
            return
        await self._buffer.ack([m.id for m in messages])
        log.debug("committed + acked %d messages", len(messages))

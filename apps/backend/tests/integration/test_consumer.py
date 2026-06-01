"""Consumer loop: periodic reclaim re-drives stuck/failed batches (review I2/I3).

A batch left pending by a crashed/failed consumer must be reclaimed and
reprocessed by the running loop — not only at startup. `run_once()` performs one
iteration (reclaim idle pending, then read+process a new batch) and `run()` loops
it; `request_stop()` makes the loop exit promptly (graceful shutdown).
"""

from __future__ import annotations

import asyncio

import pytest
from app.config import Settings
from app.core.buffer import RedisStreamBuffer
from worker.consumer import RollupConsumer

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


def _fields(event_id: str):
    return {
        "event_id": event_id,
        "tenant": "default",
        "type": "click",
        "user_id": "",
        "ts": "2026-01-01T10:00:00+00:00",
        "props": "",
    }


async def test_run_once_reclaims_stuck_pending_entry(pg_pool, buffer_redis):
    # claim idle = 0 so the periodic reclaim picks up the pending entry immediately.
    buf = RedisStreamBuffer(buffer_redis, Settings(worker_block_ms=50, worker_claim_idle_ms=0))
    consumer = RollupConsumer(pg_pool, buf)
    await buf.ensure_group()

    await buf.add(_fields("e_stuck"))
    delivered = await buf.read_batch()  # read but never acked == crashed before XACK
    assert len(delivered) == 1

    processed = await consumer.run_once()  # should reclaim + persist + ack
    assert processed >= 1

    pending = await buffer_redis.xpending(buf._stream, buf._group)
    assert pending["pending"] == 0
    async with pg_pool.acquire() as conn:
        assert await conn.fetchval("SELECT count(*) FROM events") == 1


async def test_request_stop_exits_run(pg_pool, buffer_redis):
    buf = RedisStreamBuffer(buffer_redis, Settings(worker_block_ms=50, worker_claim_idle_ms=0))
    consumer = RollupConsumer(pg_pool, buf)
    consumer.request_stop()
    # With stop already requested, run() must return promptly.
    await asyncio.wait_for(consumer.run(), timeout=2)

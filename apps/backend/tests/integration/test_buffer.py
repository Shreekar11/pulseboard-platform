"""Redis Streams buffer adapter: consumer-group glue + reclaim semantics.

Real-issue focus: the XREADGROUP/XACK/XAUTOCLAIM wiring (Redis API shapes) and the
crash-before-XACK guarantee — an un-acked message must remain reclaimable and,
combined with Postgres dedup, produce an exactly-once effect (Phase-1-Backend §8).
"""

from __future__ import annotations

import pytest
from app.config import Settings
from app.core.buffer import RedisStreamBuffer
from worker.rollup import persist_batch

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


def _buffer(client):
    # claim idle = 0 so XAUTOCLAIM reclaims immediately in the test.
    settings = Settings(worker_block_ms=200, worker_claim_idle_ms=0)
    return RedisStreamBuffer(client, settings)


def _fields(event_id: str):
    return {
        "event_id": event_id,
        "tenant": "default",
        "type": "click",
        "user_id": "",
        "ts": "2026-01-01T10:00:00+00:00",
        "props": "",
    }


async def test_add_read_ack_roundtrip(buffer_redis):
    buf = _buffer(buffer_redis)
    await buf.ensure_group()
    await buf.add(_fields("e1"))
    await buf.add(_fields("e2"))

    batch = await buf.read_batch()
    assert {m.fields["event_id"] for m in batch} == {"e1", "e2"}

    await buf.ack([m.id for m in batch])
    pending = await buffer_redis.xpending(buf._stream, buf._group)
    assert pending["pending"] == 0


async def test_unacked_message_is_reclaimable_and_dedupes(pg_pool, buffer_redis):
    buf = _buffer(buffer_redis)
    await buf.ensure_group()
    await buf.add(_fields("e_crash"))

    # First delivery: persist but "crash" before ack (no ack call).
    first = await buf.read_batch()
    await persist_batch(pg_pool, first)
    assert len(first) == 1  # delivered, still pending (un-acked)

    # Recovery: reclaim the pending entry and reprocess.
    reclaimed = await buf.autoclaim()
    assert {m.fields["event_id"] for m in reclaimed} == {"e_crash"}
    await persist_batch(pg_pool, reclaimed)
    await buf.ack([m.id for m in reclaimed])

    # Exactly-once effect: reprocessing did not double-count.
    async with pg_pool.acquire() as conn:
        events = await conn.fetchval("SELECT count(*) FROM events")
        rollup_total = await conn.fetchval("SELECT COALESCE(SUM(count), 0) FROM rollups")
    assert events == 1
    assert rollup_total == 1

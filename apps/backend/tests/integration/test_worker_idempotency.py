"""Worker correctness: dedup on event_id + replay safety (exactly-once effect).

These are the crown-jewel correctness properties (Phase-1-Backend §5): a retried
or redelivered event must never be double-counted, and reprocessing a batch
(crash-before-XACK replay) must leave rollups unchanged.
"""

from __future__ import annotations

import pytest
from app.core.buffer import BufferMessage
from worker.rollup import persist_batch

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


def _msg(mid: str, event_id: str, *, type_: str = "signup", ts: str = "2026-01-01T10:30:00+00:00"):
    return BufferMessage(
        id=mid,
        fields={
            "event_id": event_id,
            "tenant": "default",
            "type": type_,
            "user_id": "u1",
            "ts": ts,
            "props": "",
        },
    )


async def _counts(pool):
    async with pool.acquire() as conn:
        events = await conn.fetchval("SELECT count(*) FROM events")
        rollup_total = await conn.fetchval("SELECT COALESCE(SUM(count), 0) FROM rollups")
    return events, rollup_total


async def test_duplicate_event_id_across_batches_counted_once(pg_pool):
    await persist_batch(pg_pool, [_msg("1-0", "evt_dup")])
    await persist_batch(pg_pool, [_msg("2-0", "evt_dup")])  # redelivery / retry

    events, rollup_total = await _counts(pg_pool)
    assert events == 1
    assert rollup_total == 1


async def test_replay_same_batch_leaves_rollups_unchanged(pg_pool):
    batch = [_msg("1-0", "evt_a"), _msg("1-1", "evt_b")]
    await persist_batch(pg_pool, batch)
    await persist_batch(pg_pool, batch)  # crash-before-XACK replay

    events, rollup_total = await _counts(pg_pool)
    assert events == 2
    assert rollup_total == 2


async def test_intra_batch_duplicate_counted_once(pg_pool):
    # Same event_id twice within one XREADGROUP batch.
    await persist_batch(pg_pool, [_msg("1-0", "evt_x"), _msg("1-1", "evt_x")])

    events, rollup_total = await _counts(pg_pool)
    assert events == 1
    assert rollup_total == 1


async def test_same_hour_different_events_accumulate(pg_pool):
    await persist_batch(
        pg_pool,
        [
            _msg("1-0", "e1", ts="2026-01-01T10:05:00+00:00"),
            _msg("1-1", "e2", ts="2026-01-01T10:55:00+00:00"),
        ],
    )
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT bucket, count FROM rollups WHERE type='signup'")
    assert len(rows) == 1  # both fall in the 10:00 hour bucket
    assert rows[0]["count"] == 2

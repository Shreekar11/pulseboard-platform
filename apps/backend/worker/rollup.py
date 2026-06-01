"""Batch persistence: the worker's single Postgres transaction.

Idempotency (Phase-1-Backend §5): PRIMARY KEY(event_id) + ON CONFLICT DO NOTHING
absorbs client retries and stream redelivery; rollups increment only from
RETURNING (newly-inserted) rows, so a duplicate adds 0.
"""

from __future__ import annotations

from datetime import datetime

import asyncpg
from app.core.buffer import BufferMessage

from worker.sql import PERSIST_BATCH


def _dedup_in_batch(messages: list[BufferMessage]) -> list[BufferMessage]:
    """Drop intra-batch duplicate event_ids (cheap safeguard; DB enforces too)."""
    seen: dict[str, BufferMessage] = {}
    for m in messages:
        eid = m.fields.get("event_id")
        if eid and eid not in seen:
            seen[eid] = m
    return list(seen.values())


async def persist_batch(pool: asyncpg.Pool, messages: list[BufferMessage]) -> None:
    """Insert raw events + upsert rollups for one batch, in a single transaction.

    Raises on failure (caller must NOT ack — messages stay pending and redeliver).
    """
    rows = _dedup_in_batch(messages)
    if not rows:
        return

    event_ids: list[str] = []
    tenants: list[str] = []
    types: list[str] = []
    user_ids: list[str] = []
    timestamps: list[datetime] = []
    props: list[str] = []
    for m in rows:
        f = m.fields
        event_ids.append(f["event_id"])
        tenants.append(f.get("tenant") or "default")
        types.append(f["type"])
        user_ids.append(f.get("user_id") or "")
        timestamps.append(datetime.fromisoformat(f["ts"]))
        props.append(f.get("props") or "")

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                PERSIST_BATCH, event_ids, tenants, types, user_ids, timestamps, props
            )

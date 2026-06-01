"""Metrics read queries — rollups table only, never raw events.

`[from, to)` half-open ranges, UTC, gap-filled via generate_series so charts have
no holes (Phase-1-Backend §7, §11).
"""

from __future__ import annotations

from datetime import datetime

import asyncpg

from app.core.timeutil import step_for
from app.models.metrics import MetricPoint, TopItem

# generate_series gap-fill; $4 is '1 hour'|'1 day'|'1 week'; range is [from, to).
# $4 is hinted as text (::text::interval) so asyncpg sends the string rather than
# trying to encode it with the interval (timedelta) codec.
_SERIES_SQL = """
SELECT g.b AS bucket, COALESCE(SUM(r.count), 0)::bigint AS count
FROM generate_series(
        $2::timestamptz, $3::timestamptz - $4::text::interval, $4::text::interval
     ) AS g(b)
LEFT JOIN rollups r
  ON r.tenant = $1 AND r.type = $5
 AND r.bucket >= g.b AND r.bucket < g.b + $4::text::interval
WHERE g.b >= $2::timestamptz AND g.b < $3::timestamptz
GROUP BY g.b
ORDER BY g.b;
"""

_TOP_SQL = """
SELECT type, SUM(count)::bigint AS count
FROM rollups
WHERE tenant = $1 AND bucket >= $2::timestamptz AND bucket < $3::timestamptz
GROUP BY type
ORDER BY count DESC, type
LIMIT $4;
"""


async def get_series(
    pool: asyncpg.Pool,
    *,
    tenant: str,
    type_: str,
    from_: datetime,
    to: datetime,
    interval: str,
) -> list[MetricPoint]:
    step = step_for(interval)
    async with pool.acquire() as conn:
        rows = await conn.fetch(_SERIES_SQL, tenant, from_, to, step, type_)
    return [MetricPoint(bucket=r["bucket"], count=r["count"]) for r in rows]


async def get_top(
    pool: asyncpg.Pool,
    *,
    tenant: str,
    from_: datetime,
    to: datetime,
    limit: int,
) -> list[TopItem]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(_TOP_SQL, tenant, from_, to, limit)
    return [TopItem(type=r["type"], count=r["count"]) for r in rows]

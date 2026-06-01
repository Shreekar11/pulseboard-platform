"""Metrics API bucket-alignment (review C1), end-to-end through the HTTP layer.

Non-aligned `from`/`to` must not bleed across calendar buckets, and a sub-step
range must still return one bucket instead of an empty series.
"""

from __future__ import annotations

from datetime import UTC

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


@pytest_asyncio.fixture
async def client(settings, pg_pool, buffer_redis, ratelimit_redis):
    from app.main import create_app

    app = create_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c


async def _insert(pool, rows):
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO rollups (tenant, type, bucket, count) VALUES ('default', $1, $2, $3)",
            rows,
        )


async def test_sub_step_range_returns_one_bucket(client, pg_pool):
    from datetime import datetime

    await _insert(pg_pool, [("signup", datetime(2026, 3, 1, 10, tzinfo=UTC), 5)])
    # interval=day over a 12h span -> previously an empty series; must be one bucket.
    resp = await client.get(
        "/api/metrics",
        params={
            "type": "signup",
            "from": "2026-03-01T00:00:00Z",
            "to": "2026-03-01T12:00:00Z",
            "interval": "day",
        },
    )
    assert resp.status_code == 200
    series = resp.json()["series"]
    assert len(series) == 1
    assert series[0]["count"] == 5


async def test_misaligned_day_input_does_not_bleed(client, pg_pool):
    from datetime import datetime

    await _insert(
        pg_pool,
        [
            ("signup", datetime(2026, 3, 1, 23, tzinfo=UTC), 3),  # day 1
            ("signup", datetime(2026, 3, 2, 1, tzinfo=UTC), 7),  # day 2
        ],
    )
    # Misaligned 05:00 bounds: must produce two correct per-calendar-day buckets,
    # not one window that merges 23:00(day1) with 01:00(day2).
    resp = await client.get(
        "/api/metrics",
        params={
            "type": "signup",
            "from": "2026-03-01T05:00:00Z",
            "to": "2026-03-02T05:00:00Z",
            "interval": "day",
        },
    )
    assert resp.status_code == 200
    counts = [p["count"] for p in resp.json()["series"]]
    assert counts == [3, 7]

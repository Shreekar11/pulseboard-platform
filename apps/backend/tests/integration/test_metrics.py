"""Metrics read correctness: gap-fill, half-open [from, to), and day/week roll-up.

Where the generate_series SQL subtlety lives (Phase-1-Backend §7, §11): empty
buckets must be 0 (no holes), the range is half-open so a bucket exactly at `to`
is excluded, and day/week intervals aggregate hourly rollups correctly.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services import metrics_service

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


async def _insert_rollups(pool, rows):
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO rollups (tenant, type, bucket, count) VALUES ('default', $1, $2, $3)",
            rows,
        )


async def test_gap_fill_zeros_no_holes(pg_pool):
    # Only the 10:00 hour has data; 08,09,11 must come back as 0.
    await _insert_rollups(pg_pool, [("signup", _utc("2026-01-01T10:00:00"), 5)])

    series = await metrics_service.get_series(
        pg_pool,
        tenant="default",
        type_="signup",
        from_=_utc("2026-01-01T08:00:00"),
        to=_utc("2026-01-01T12:00:00"),
        interval="hour",
    )
    assert [p.count for p in series] == [0, 0, 5, 0]
    assert len(series) == 4


async def test_half_open_excludes_to_includes_from(pg_pool):
    await _insert_rollups(
        pg_pool,
        [
            ("signup", _utc("2026-01-01T10:00:00"), 3),  # == from -> included
            ("signup", _utc("2026-01-01T12:00:00"), 9),  # == to   -> excluded
        ],
    )
    series = await metrics_service.get_series(
        pg_pool,
        tenant="default",
        type_="signup",
        from_=_utc("2026-01-01T10:00:00"),
        to=_utc("2026-01-01T12:00:00"),
        interval="hour",
    )
    buckets = {p.bucket.hour: p.count for p in series}
    assert buckets == {10: 3, 11: 0}
    assert 12 not in buckets


async def test_day_interval_aggregates_hourly(pg_pool):
    await _insert_rollups(
        pg_pool,
        [
            ("signup", _utc("2026-01-01T01:00:00"), 2),
            ("signup", _utc("2026-01-01T23:00:00"), 3),
            ("signup", _utc("2026-01-02T05:00:00"), 7),
        ],
    )
    series = await metrics_service.get_series(
        pg_pool,
        tenant="default",
        type_="signup",
        from_=_utc("2026-01-01T00:00:00"),
        to=_utc("2026-01-03T00:00:00"),
        interval="day",
    )
    assert [p.count for p in series] == [5, 7]  # day1: 2+3, day2: 7


async def test_top_n_ordering_and_limit(pg_pool):
    await _insert_rollups(
        pg_pool,
        [
            ("click", _utc("2026-01-01T10:00:00"), 50),
            ("signup", _utc("2026-01-01T10:00:00"), 30),
            ("purchase", _utc("2026-01-01T10:00:00"), 10),
        ],
    )
    items = await metrics_service.get_top(
        pg_pool,
        tenant="default",
        from_=_utc("2026-01-01T00:00:00"),
        to=_utc("2026-01-02T00:00:00"),
        limit=2,
    )
    assert [(i.type, i.count) for i in items] == [("click", 50), ("signup", 30)]

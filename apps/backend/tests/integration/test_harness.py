"""Sanity checks that the integration harness (containers + migration) works."""

from __future__ import annotations

import pytest

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


async def test_migration_created_tables(pg_pool):
    async with pg_pool.acquire() as conn:
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
    names = {r["tablename"] for r in tables}
    assert {"events", "rollups"}.issubset(names)


async def test_redis_reachable(buffer_redis):
    assert await buffer_redis.ping() is True

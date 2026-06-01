"""Postgres access via an asyncpg connection pool.

The pool is created at startup (API lifespan / worker bootstrap) and closed on
shutdown. The metrics API reads through this pool (rollups only); the worker is
the *sole writer*. The ingest path must never use this module.
"""

from __future__ import annotations

import asyncpg

from app.config import Settings


async def create_pool(settings: Settings) -> asyncpg.Pool:
    """Create an asyncpg pool sized from settings."""
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        # Pin the session to UTC so date_trunc / generate_series bucket in UTC.
        server_settings={"timezone": "UTC"},
    )


async def close_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()


async def ping(pool: asyncpg.Pool) -> bool:
    """Readiness check: confirm Postgres answers a trivial query."""
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT 1") == 1

"""Shared test fixtures.

Integration tests run against real Postgres + Redis (testcontainers). Containers
are session-scoped (sync); connections are per-test (function-scoped) to avoid
event-loop-scope issues, with table truncation / FLUSHDB between tests.

The Alembic migration is applied to the test database, so the migration itself is
exercised as part of the suite.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from redis.asyncio import Redis

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _docker_available() -> bool:
    try:
        import docker  # noqa: F401

        client = __import__("docker").from_env()
        client.ping()
        return True
    except Exception:
        return False


requires_docker = pytest.mark.skipif(
    not _docker_available(), reason="Docker not available for testcontainers"
)


@pytest.fixture(scope="session")
def postgres_dsn() -> Iterator[str]:
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        dsn = (
            f"postgresql://{pg.username}:{pg.password}"
            f"@{pg.get_container_host_ip()}:{pg.get_exposed_port(5432)}/{pg.dbname}"
        )
        yield dsn


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as rc:
        host = rc.get_container_host_ip()
        port = rc.get_exposed_port(6379)
        yield f"redis://{host}:{port}"


@pytest.fixture(scope="session", autouse=True)
def _configure_env(postgres_dsn: str, redis_url: str) -> Iterator[None]:
    """Point Settings + Alembic at the containers and apply migrations once."""
    os.environ["DATABASE_URL"] = postgres_dsn
    os.environ["ALEMBIC_DATABASE_URL"] = postgres_dsn
    os.environ["REDIS_BUFFER_URL"] = f"{redis_url}/0"
    os.environ["REDIS_RATELIMIT_URL"] = f"{redis_url}/1"

    from app.config import get_settings

    get_settings.cache_clear()

    from alembic import command
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    command.upgrade(cfg, "head")

    yield
    get_settings.cache_clear()


@pytest.fixture
def settings():
    from app.config import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture
async def pg_pool(settings) -> AsyncIterator[asyncpg.Pool]:
    from app.core import db

    pool = await db.create_pool(settings)
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE events, rollups;")
    try:
        yield pool
    finally:
        await db.close_pool(pool)


@pytest_asyncio.fixture
async def buffer_redis(settings) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.redis_buffer_url, decode_responses=True)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def ratelimit_redis(settings) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.redis_ratelimit_url, decode_responses=True)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.aclose()

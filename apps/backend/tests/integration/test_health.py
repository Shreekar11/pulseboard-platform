"""Liveness/readiness behavior (plan §8, §13, §16).

/healthz is always 200 (no dependency checks). /readyz is 200 only when both Redis
and Postgres answer, and 503 if either is down.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


@pytest_asyncio.fixture
async def app_client(settings, pg_pool, buffer_redis, ratelimit_redis):
    from app.main import create_app

    app = create_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield app, c


async def test_healthz_always_ok(app_client):
    _app, c = app_client
    resp = await c.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_readyz_ok_when_both_up(app_client):
    _app, c = app_client
    resp = await c.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["checks"] == {"redis": True, "postgres": True}


async def test_readyz_503_when_redis_down(app_client):
    app, c = app_client
    # Point the readiness Redis check at an unused port → fails fast.
    app.state.buffer_client = Redis.from_url("redis://127.0.0.1:6390/0", socket_connect_timeout=0.2)
    resp = await c.get("/readyz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["checks"]["redis"] is False
    assert body["checks"]["postgres"] is True

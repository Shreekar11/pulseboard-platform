"""Ingest endpoint wiring: hot path returns 202, lands in the stream, and does
NOT write Postgres; malformed input is rejected; over-limit yields 429.

Real-issue focus (Phase-1-Backend §3, §4, §9): the hot path must be Postgres-free
and the rate-limit result must translate into a 429 + Retry-After.
"""

from __future__ import annotations

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


async def test_ingest_accepts_and_lands_in_stream_without_postgres(
    client, settings, pg_pool, buffer_redis
):
    resp = await client.post(
        "/api/events",
        json={"event_id": "evt_1", "type": "signup", "ts": "2026-01-01T10:00:00Z"},
    )
    assert resp.status_code == 202
    assert resp.json() == {"status": "accepted", "event_id": "evt_1"}

    # Landed in the stream...
    assert await buffer_redis.xlen(settings.events_stream) == 1
    # ...and the hot path wrote nothing to Postgres.
    async with pg_pool.acquire() as conn:
        assert await conn.fetchval("SELECT count(*) FROM events") == 0


async def test_malformed_event_rejected_422(client):
    resp = await client.post("/api/events", json={"event_id": "evt_1"})  # missing type
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_over_limit_returns_429_with_retry_after(
    monkeypatch, pg_pool, buffer_redis, ratelimit_redis
):
    monkeypatch.setenv("RATELIMIT_REQUESTS", "1")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            body = {"event_id": "e", "type": "signup"}
            first = await c.post("/api/events", json=body)
            second = await c.post("/api/events", json={**body, "event_id": "e2"})

    assert first.status_code == 202
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"
    assert int(second.headers["retry-after"]) >= 1
    get_settings.cache_clear()

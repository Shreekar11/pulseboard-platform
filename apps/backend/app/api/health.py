"""Liveness and readiness endpoints.

`/healthz` — liveness: process is up (no dependency checks, so a transient blip
does not get the pod killed).
`/readyz` — readiness: Redis buffer AND Postgres must answer, since the ingest
path depends on Redis and the metrics path depends on Postgres
(Phase-1-Backend §8, §12). Readiness reflects ability to serve, not freshness.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request, Response, status

from app.core import db, redis

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict[str, object]:
    pool = request.app.state.pool
    buffer_client = request.app.state.buffer_client

    redis_ok, pg_ok = await asyncio.gather(
        _safe(redis.ping(buffer_client)),
        _safe(db.ping(pool)),
    )

    ready = redis_ok and pg_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if ready else "not_ready",
        "checks": {"redis": redis_ok, "postgres": pg_ok},
    }


async def _safe(coro) -> bool:
    try:
        return bool(await coro)
    except Exception:
        return False

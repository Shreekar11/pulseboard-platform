"""Ingest hot path: POST /api/events.

Validate (Pydantic) -> rate-limit (per IP) -> XADD to the Redis stream -> 202.
This handler performs NO Postgres work (Phase-1-Backend §3, §4). The expensive,
batched persistence happens asynchronously in the worker.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.deps import BufferDep, RateLimiterDep
from app.models.errors import ErrorBody, ErrorResponse
from app.models.event import EventAccepted, EventIn

log = logging.getLogger("ingest")

router = APIRouter(prefix="/api", tags=["ingest"])


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventAccepted,
    responses={
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def ingest_event(
    event: EventIn,
    request: Request,
    buffer: BufferDep,
    rate_limiter: RateLimiterDep,
):
    # Rate limiting is best-effort abuse protection. If its Redis is unavailable we
    # fail OPEN: the hot path stays available (the *buffer* Redis is the critical,
    # separate dependency; /readyz does not gate on rate-limit Redis). (Review I5.)
    try:
        rl = await rate_limiter.check(_client_ip(request))
    except RedisError:
        log.warning("rate-limit check failed; failing open", exc_info=True)
    else:
        if not rl.allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(rl.retry_after_seconds)},
                content=ErrorResponse(
                    error=ErrorBody(code="rate_limited", message="rate limit exceeded")
                ).model_dump(),
            )

    try:
        await buffer.add(event.to_stream_fields())
    except RedisError:
        # Never silently drop: tell the client we could not accept the event.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error=ErrorBody(code="buffer_unavailable", message="ingest buffer unavailable")
            ).model_dump(),
        )

    return EventAccepted(event_id=event.event_id)

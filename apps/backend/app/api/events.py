"""Ingest hot path: POST /api/events.

Validate (Pydantic) -> rate-limit (per IP) -> XADD to the Redis stream -> 202.
This handler performs NO Postgres work (Phase-1-Backend §3, §4). The expensive,
batched persistence happens asynchronously in the worker.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.deps import BufferDep, RateLimiterDep
from app.models.errors import ErrorBody, ErrorResponse
from app.models.event import EventAccepted, EventIn

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
    rl = await rate_limiter.check(_client_ip(request))
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

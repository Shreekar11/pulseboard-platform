"""FastAPI dependency providers.

Shared resources live on ``app.state`` (created in the lifespan) so the app holds
no per-request in-memory state — counters and the buffer live in Redis, reads in
Postgres. This keeps the API stateless and horizontally scalable.
"""

from __future__ import annotations

from typing import Annotated

import asyncpg
from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.buffer import EventBuffer
from app.core.ratelimit import RateLimiter


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_buffer(request: Request) -> EventBuffer:
    return request.app.state.buffer


def get_buffer_client(request: Request) -> Redis:
    return request.app.state.buffer_client


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


PoolDep = Annotated[asyncpg.Pool, Depends(get_pool)]
BufferDep = Annotated[EventBuffer, Depends(get_buffer)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]

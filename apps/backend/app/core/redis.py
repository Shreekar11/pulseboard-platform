"""Async Redis client factories.

Two logically-separate clients: the ingest *stream buffer* and the *rate
limiter*. They use separate URLs (separate logical DB locally, separate instances
in production) so rate-limit churn or memory pressure can never threaten accepted
events (Phase-1-Backend §3, §9).
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.config import Settings


def create_buffer_client(settings: Settings) -> Redis:
    """Client for the Redis Streams ingest buffer."""
    return Redis.from_url(settings.redis_buffer_url, decode_responses=True)


def create_ratelimit_client(settings: Settings) -> Redis:
    """Client for the per-IP rate limiter (separate from the buffer)."""
    return Redis.from_url(settings.redis_ratelimit_url, decode_responses=True)


async def ping(client: Redis) -> bool:
    """Readiness check: confirm Redis answers PING."""
    return bool(await client.ping())

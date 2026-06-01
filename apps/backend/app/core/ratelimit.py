"""Per-IP sliding-window rate limiter backed by Redis.

Implemented as an atomic Lua script (sliding-window log over a sorted set) on the
*rate-limit* Redis, so all stateless API replicas share one counter
(Phase-1-Backend §9). Applied to the ingest hot path only.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis

from app.config import Settings

# KEYS[1]=key  ARGV: now_ms, window_ms, limit, unique_member
# Returns {allowed(0|1), retry_after_ms}
_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count < limit then
  redis.call('ZADD', key, now, member)
  redis.call('PEXPIRE', key, window)
  return {1, 0}
end
local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local retry = window
if oldest[2] then
  retry = (tonumber(oldest[2]) + window) - now
end
return {0, retry}
"""


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimiter:
    def __init__(self, client: Redis, settings: Settings) -> None:
        self._r = client
        self._limit = settings.ratelimit_requests
        self._window_ms = settings.ratelimit_window_seconds * 1000
        self._script = client.register_script(_SLIDING_WINDOW_LUA)

    async def check(self, client_ip: str) -> RateLimitResult:
        now_ms = int(time.time() * 1000)
        allowed, retry_after_ms = await self._script(
            keys=[f"rl:{client_ip}"],
            args=[now_ms, self._window_ms, self._limit, f"{now_ms}-{uuid.uuid4().hex}"],
        )
        return RateLimitResult(
            allowed=bool(int(allowed)),
            retry_after_seconds=max(1, (int(retry_after_ms) + 999) // 1000),
        )

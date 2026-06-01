"""Rate limiter correctness: the custom sliding-window Lua script.

Real-issue focus (Phase-1-Backend §9): the window must allow exactly N requests,
deny the next with a sane Retry-After, slide so the IP is allowed again after the
window passes, and isolate different IPs.
"""

from __future__ import annotations

import asyncio

import pytest
from app.config import Settings
from app.core.ratelimit import RateLimiter

from tests.conftest import requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


@pytest.fixture
def limiter(ratelimit_redis):
    settings = Settings(ratelimit_requests=3, ratelimit_window_seconds=1)
    return RateLimiter(ratelimit_redis, settings)


async def test_allows_up_to_limit_then_denies(limiter):
    results = [await limiter.check("1.1.1.1") for _ in range(4)]
    assert [r.allowed for r in results] == [True, True, True, False]
    assert results[-1].retry_after_seconds >= 1


async def test_window_slides_after_expiry(limiter):
    for _ in range(3):
        await limiter.check("2.2.2.2")
    assert (await limiter.check("2.2.2.2")).allowed is False

    await asyncio.sleep(1.05)  # let the 1s window pass
    assert (await limiter.check("2.2.2.2")).allowed is True


async def test_limits_are_per_ip(limiter):
    for _ in range(3):
        await limiter.check("3.3.3.3")
    # A different IP is unaffected by 3.3.3.3 exhausting its window.
    assert (await limiter.check("4.4.4.4")).allowed is True

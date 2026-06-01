"""Bucket-boundary alignment for metric ranges (Phase-1-Backend §7, §11).

`from` floors to its bucket boundary; `to` ceils. This prevents adjacent-bucket
bleed for non-aligned day/week inputs and guarantees a non-empty series for
sub-step ranges. (Review finding C1.)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.timeutil import align_ceil, align_floor


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_floor_hour():
    assert align_floor(_utc("2026-01-01T10:37:12"), "hour") == _utc("2026-01-01T10:00:00")


def test_floor_day():
    assert align_floor(_utc("2026-01-01T10:37:12"), "day") == _utc("2026-01-01T00:00:00")


def test_floor_week_to_monday():
    # 2026-01-01 is a Thursday; the week floors back to Monday 2025-12-29.
    assert align_floor(_utc("2026-01-01T10:00:00"), "week") == _utc("2025-12-29T00:00:00")


def test_ceil_returns_same_when_already_aligned():
    aligned = _utc("2026-01-03T00:00:00")
    assert align_ceil(aligned, "day") == aligned


def test_ceil_rounds_up_when_not_aligned():
    assert align_ceil(_utc("2026-01-01T10:37:12"), "day") == _utc("2026-01-02T00:00:00")
    assert align_ceil(_utc("2026-01-01T10:37:12"), "hour") == _utc("2026-01-01T11:00:00")


def test_naive_input_assumed_utc():
    assert align_floor(datetime(2026, 1, 1, 10, 0, 0), "hour") == _utc("2026-01-01T10:00:00")


def test_unsupported_interval_raises():
    with pytest.raises(ValueError):
        align_floor(_utc("2026-01-01T00:00:00"), "month")

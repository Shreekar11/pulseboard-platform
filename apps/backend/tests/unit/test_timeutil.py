"""Unit tests for time/interval helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timezone

import pytest
from app.core.timeutil import step_for, to_utc


def test_naive_assumed_utc():
    dt = to_utc(datetime(2026, 1, 1, 10, 0, 0))
    assert dt.tzinfo == UTC
    assert dt.hour == 10


def test_aware_converted_to_utc():
    from datetime import timedelta

    tz = timezone(timedelta(hours=2))
    dt = to_utc(datetime(2026, 1, 1, 10, 0, 0, tzinfo=tz))
    assert dt.tzinfo == UTC
    assert dt.hour == 8


@pytest.mark.parametrize(
    ("interval", "expected"),
    [("hour", "1 hour"), ("day", "1 day"), ("week", "1 week")],
)
def test_step_for_supported(interval, expected):
    assert step_for(interval) == expected


def test_step_for_unsupported():
    with pytest.raises(ValueError):
        step_for("month")

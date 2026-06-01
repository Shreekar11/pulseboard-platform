"""UTC normalization and interval/bucket helpers.

Contract (Phase-1-Backend §7): all timestamps are UTC; metric ranges are
half-open ``[from, to)``; ``from``/``to`` are aligned to bucket boundaries so
non-aligned inputs cannot bleed adjacent-bucket data. Hourly is the base grain;
day/week aggregate up on read.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

# interval -> Postgres step interval literal used by generate_series gap-fill.
INTERVAL_STEPS: dict[str, str] = {
    "hour": "1 hour",
    "day": "1 day",
    "week": "1 week",
}

# interval -> Python timedelta, used for ceil rounding (week == 7 days, matching
# Postgres '1 week' and date_trunc('week') Monday-based weeks).
_STEP_DELTAS: dict[str, timedelta] = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
}


def to_utc(dt: datetime) -> datetime:
    """Normalize an aware/naive datetime to UTC. Naive is assumed to be UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def now_utc() -> datetime:
    return datetime.now(UTC)


def step_for(interval: str) -> str:
    """Return the Postgres interval literal for a supported interval, else raise."""
    try:
        return INTERVAL_STEPS[interval]
    except KeyError as exc:
        raise ValueError(f"unsupported interval: {interval!r}") from exc


def align_floor(dt: datetime, interval: str) -> datetime:
    """Floor a UTC datetime down to its interval bucket boundary."""
    dt = to_utc(dt)
    if interval == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if interval == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if interval == "week":
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight - timedelta(days=midnight.weekday())  # back to Monday
    raise ValueError(f"unsupported interval: {interval!r}")


def align_ceil(dt: datetime, interval: str) -> datetime:
    """Ceil a UTC datetime up to its interval bucket boundary.

    Already-aligned inputs are returned unchanged (so a half-open ``[from, to)``
    with an aligned ``to`` is not extended). A non-aligned ``to`` rounds up to the
    next boundary, which also guarantees a non-empty series for sub-step ranges.
    """
    dt = to_utc(dt)
    floored = align_floor(dt, interval)
    if floored == dt:
        return floored
    return floored + _STEP_DELTAS[interval]

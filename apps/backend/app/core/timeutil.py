"""UTC normalization and interval/bucket helpers.

Contract (Phase-1-Backend §7): all timestamps are UTC; metric ranges are
half-open ``[from, to)``; ``from``/``to`` are aligned to bucket boundaries so
non-aligned inputs cannot bleed adjacent-bucket data. Hourly is the base grain;
day/week aggregate up on read.
"""

from __future__ import annotations

from datetime import UTC, datetime

# interval -> Postgres step interval literal used by generate_series gap-fill.
INTERVAL_STEPS: dict[str, str] = {
    "hour": "1 hour",
    "day": "1 day",
    "week": "1 week",
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

# PulseBoard Backend

Event-analytics backend (Part 1 of the case study). Three responsibilities, one codebase:

- **Ingest API** (`POST /api/events`) — validate → rate-limit → `XADD` to a Redis stream → `202`. No Postgres on the hot path.
- **Rollup worker** — sole Postgres writer. Batch-consumes the stream, persists raw events idempotently (`PK(event_id)`), upserts hourly rollups in one transaction, `XACK`s only after commit.
- **Metrics API** (`GET /api/metrics`, `/api/metrics/top`) — reads pre-aggregated `rollups` only, never raw events.

Design source of truth: `docs/` + the locked `Phase-1-Backend` design. Implementation plan tracks build milestones.

## Stack

Python 3.12 · FastAPI · Pydantic v2 · asyncpg · redis (async) · SQLAlchemy Core + Alembic (migrations only). Managed with **uv**.

## Layout

```
app/        FastAPI app: config, api/ (events, metrics, health), models/, core/ (db, redis, buffer, ratelimit, time), services/
worker/     standalone rollup worker (consumer loop + one-transaction rollup)
migrations/ Alembic env + versioned migrations (events, rollups)
tests/      unit/ + integration/
```

## Local commands

```bash
uv sync                                    # create venv (Python 3.12) + install deps
uv run alembic upgrade head                # apply migrations
uv run python -m uvicorn app.main:app --reload --port 8000   # API
uv run python -m worker.main               # rollup worker
uv run pytest                              # tests
uv run ruff check . && uv run ruff format  # lint/format
```

> Modules are run with `python -m` so the project root is importable (the project is a
> non-packaged uv application; see `pyproject.toml`).

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

## Run the stack with Docker Compose

From the repo root (`docker-compose.yml` provisions postgres, redis, a one-shot
migration, the API, and the worker):

```bash
docker compose up -d --build          # build + start the backend stack
curl localhost:8000/readyz            # {"status":"ready","checks":{"redis":true,"postgres":true}}

# ingest (returns 202; does no Postgres work)
curl -X POST localhost:8000/api/events -H 'content-type: application/json' \
  -d '{"event_id":"evt_1","type":"signup","ts":"2026-01-01T10:00:00Z"}'

# read (served from rollups; gap-filled, half-open [from, to))
curl "localhost:8000/api/metrics?type=signup&from=2026-01-01T09:00:00Z&to=2026-01-01T12:00:00Z&interval=hour"
curl "localhost:8000/api/metrics/top?dimension=type&from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z"

docker compose down
```

## Testing

```bash
uv run pytest -m "not integration"    # unit tests only (no Docker)
uv run pytest                         # full suite (integration spins Postgres + Redis via testcontainers)
```

Integration tests apply the real Alembic migration to a throwaway Postgres and run
against a real Redis, so the migration and the consumer-group wiring are exercised.
They self-skip if Docker is unavailable.

## Backend design

**Read/write split & pre-aggregation.** `POST /api/events` never touches Postgres:
it validates, rate-limits, and `XADD`s to a Redis stream, returning `202`. Reads
(`GET /api/metrics*`) are served *exclusively* from the pre-aggregated `rollups`
table — never a raw-event scan. This is the whole point: dashboard load cost is
independent of event volume.

**How rollups stay fresh.** A separate rollup worker consumes the stream in batches
(`XREADGROUP`, ~500 messages or ~500 ms, whichever first) and is the *sole* Postgres
writer. Each batch is one transaction: insert raw events, then increment hourly
rollups for the newly-inserted rows. Freshness lags ingest by a few seconds; the
batch size/interval is the freshness ↔ write-amplification knob. Hourly is the base
grain; `day`/`week` reads aggregate up from hourly rows, gap-filled with
`generate_series` so charts have no holes.

**Idempotency (no double counting).** `events` has `PRIMARY KEY (event_id)`. The
batch does `INSERT … ON CONFLICT (event_id) DO NOTHING RETURNING …` and increments
rollups **only from the returned (newly-inserted) rows** — a duplicate inserts 0 rows
and adds 0 to the count. The worker `XACK`s **only after** the Postgres commit, so a
crash between commit and ack leaves messages pending; Redis redelivers them and the
dedup makes reprocessing a no-op. Result: **exactly-once effect** over at-least-once
delivery (verified end-to-end and in `tests/integration`).

**Horizontal scaling.** The API holds no per-request state — rate-limit counters and
the event buffer both live in Redis — so it scales by adding replicas. The worker
scales by adding consumers to the `rollup-workers` group; stuck entries from a
crashed consumer are reclaimed via `XAUTOCLAIM`.

**Durability trade-off (honest).** PulseBoard uses **Redis Streams by default** to
keep the ingest API fast and decoupled from Postgres writes while avoiding Kafka's
operational cost for this assignment. Redis AOF persistence (`appendfsync everysec`)
gives acceptable durability for analytics, with a small hard-crash loss window (~1s).
The buffer is abstracted behind an **`EventBuffer` port** so Kafka can replace Redis
Streams when stronger replicated-log durability or higher sustained throughput is
required.

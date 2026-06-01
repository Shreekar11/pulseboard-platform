"""Worker-scaling drain benchmark.

Measures how fast the `rollup-workers` consumer group drains a fixed backlog of N
events as the number of worker replicas grows — demonstrating horizontal scaling.

For each worker count K (``--scales``):
  1. quiesce workers (`--scale worker=0`)
  2. clean state: FLUSHDB (buffer), TRUNCATE events+rollups, recreate the group at
     id 0 so it sees the backlog we are about to add
  3. pipelined XADD of N events (unique ids)
  4. scale workers to K, then time until all N events are rolled up
     (`SUM(rollups.count) == N`)
  5. record events/s + verify exactly-once correctness (events row count == N,
     rollup sum == N) under concurrent workers

Run from apps/backend (Docker must be running, images built):

    uv run python -m loadtest.drain_benchmark --events 100000 --scales 1,3

Reuses app.config.Settings + the same Redis/Postgres connection helpers as the app.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import asyncpg
from app.config import get_settings
from redis.asyncio import Redis
from redis.exceptions import ResponseError

# Spread synthetic events across many (type, hour) rollup buckets so workers don't
# all contend on a single hot row — otherwise the scaling measurement would be
# dominated by lock contention on one rollup row rather than throughput.
SEED_TYPES = 50
SEED_HOURS = 1000

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = Path(__file__).resolve().parent / "results"
COMPOSE = ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.loadtest.yml"]


def _compose(*args: str) -> None:
    subprocess.run([*COMPOSE, *args], cwd=REPO_ROOT, check=True, capture_output=True)


def _scale_workers(k: int, build: bool = False) -> None:
    args = ["up", "-d"]
    if build:
        args.append("--build")
    args += ["--scale", f"worker={k}"]
    _compose(*args)


async def _wait_ready(settings, timeout: float = 60.0) -> None:  # noqa: ASYNC109 (caller-configurable)
    """Wait until host can reach Postgres + Redis (compose ports)."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            conn = await asyncpg.connect(settings.database_url)
            await conn.execute("SELECT 1")
            await conn.close()
            r = Redis.from_url(settings.redis_buffer_url, decode_responses=True)
            await r.ping()
            await r.aclose()
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            await asyncio.sleep(1.0)


async def _seed_backlog(r: Redis, stream: str, group: str, n: int) -> None:
    """Clean stream/tables state and XADD N unique events (pipelined)."""
    await r.flushdb()
    try:
        await r.xgroup_create(stream, group, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
    base = datetime.now(UTC)
    batch = 5000
    for start in range(0, n, batch):
        pipe = r.pipeline(transaction=False)
        for i in range(start, min(start + batch, n)):
            pipe.xadd(
                stream,
                {
                    "event_id": f"evt_{uuid.uuid4().hex}",
                    "tenant": "default",
                    "type": f"t{i % SEED_TYPES}",
                    "user_id": "u1",
                    "ts": (base - timedelta(hours=i % SEED_HOURS)).isoformat(),
                    "props": "",
                },
            )
        await pipe.execute()


async def _rollup_sum(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        return int(await conn.fetchval("SELECT COALESCE(SUM(count), 0) FROM rollups"))


async def _truncate(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE events, rollups;")


async def _run_scale(settings, pool: asyncpg.Pool, n: int, k: int, timeout: float) -> dict:  # noqa: ASYNC109 (caller-configurable)
    stream, group = settings.events_stream, settings.consumer_group

    _scale_workers(0)  # quiesce so nothing drains while we seed
    await _truncate(pool)
    r = Redis.from_url(settings.redis_buffer_url, decode_responses=True)
    await _seed_backlog(r, stream, group, n)

    t0 = time.monotonic()
    _scale_workers(k)
    deadline = t0 + timeout
    while True:
        if await _rollup_sum(pool) >= n:
            break
        if time.monotonic() > deadline:
            raise TimeoutError(f"drain did not complete for workers={k} within {timeout}s")
        await asyncio.sleep(0.1)
    elapsed = time.monotonic() - t0

    async with pool.acquire() as conn:
        events = int(await conn.fetchval("SELECT count(*) FROM events"))
        rollup_sum = int(await conn.fetchval("SELECT COALESCE(SUM(count), 0) FROM rollups"))
    await r.aclose()

    return {
        "workers": k,
        "events": n,
        "drain_seconds": round(elapsed, 3),
        "events_per_sec": round(n / elapsed, 1),
        "correct": events == n and rollup_sum == n,
        "events_rows": events,
        "rollup_sum": rollup_sum,
    }


async def main() -> None:
    ap = argparse.ArgumentParser(description="Worker-scaling drain benchmark")
    ap.add_argument("--events", type=int, default=100_000)
    ap.add_argument("--scales", default="1,3", help="comma-separated worker counts")
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args()
    scales = [int(s) for s in args.scales.split(",")]

    settings = get_settings()
    print(f"Bringing up stack (build) with 0 workers… (repo={REPO_ROOT})")
    _scale_workers(0, build=True)
    await _wait_ready(settings)

    pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=4)
    results = []
    try:
        for k in scales:
            print(f"\n=== workers={k}: draining {args.events} events ===")
            res = await _run_scale(settings, pool, args.events, k, args.timeout)
            print(json.dumps(res, indent=2))
            results.append(res)
    finally:
        await pool.close()
        _scale_workers(0)  # quiesce at the end

    baseline = next((r for r in results if r["workers"] == scales[0]), results[0])
    for r in results:
        r["speedup_vs_baseline"] = round(r["events_per_sec"] / baseline["events_per_sec"], 2)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "drain_results.json"
    out.write_text(json.dumps({"events": args.events, "runs": results}, indent=2))
    print(f"\nWrote {out}")
    print("\nworkers | events/s | drain_s | speedup | correct")
    for r in results:
        print(
            f"  {r['workers']:>5} | {r['events_per_sec']:>8.0f} | "
            f"{r['drain_seconds']:>7.1f} | {r['speedup_vs_baseline']:>6.2f}x | {r['correct']}"
        )


if __name__ == "__main__":
    asyncio.run(main())

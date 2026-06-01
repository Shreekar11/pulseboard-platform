# PulseBoard Backend — Load Test & Worker-Scaling Benchmark

Reproducible benchmark of the ingest hot path (`POST /api/events`) and of horizontal
worker scaling in the `rollup-workers` consumer group. Raw artifacts alongside this
file: `ingest_stats.csv`, `ingest_stats_history.csv`, `ingest.html`, `drain_results.json`.

## Environment

| | |
|---|---|
| Machine | Apple M4, 10 cores, 16 GB RAM |
| OS | macOS 26.2 |
| Docker | 28.5.2 |
| Topology | **single host** — load generator + full stack (api, worker(s), postgres, redis) all co-located |
| Stack | `docker-compose.yml` + `docker-compose.loadtest.yml` (per-IP rate limit raised so we measure the hot path, not the limiter) |
| Date | 2026-06-02 |

> ⚠️ **Numbers are illustrative, not production SLO proof.** The load client and the
> entire stack share the same 10 cores, so they compete for CPU. Absolute latency is
> inflated by co-location and by zero client think-time; treat these as *trends and
> relative comparisons*, not capacity planning figures. A real measurement would put
> the client on a separate host and the DB/Redis on dedicated nodes.

## 1. Ingest hot path (Locust)

`POST /api/events` — 200 virtual users, no think time, 60s, unique `event_id` per request.

```
uv run locust -f loadtest/locustfile.py --headless -u 200 -r 50 -t 60s \
    --host http://localhost:8000 --csv loadtest/results/ingest --html loadtest/results/ingest.html
```

| Metric | Result |
|---|---|
| Requests | 170,143 |
| **Failures** | **0 (0.00%)** |
| Throughput | **~2,881 req/s** |
| p50 | 68 ms |
| p90 / p95 | 78 / 82 ms |
| p99 | 88 ms |
| p99.9 / max | 97 / 206 ms |

**Read vs the `<50ms` p99 design SLO:** not met *at this concurrency on a single host* —
with 200 zero-think-time users hammering a stack that shares the same CPU, requests
queue and latency rises. The meaningful results here are **0% errors at ~2.9k rps** and
a tight, stable distribution (p50 68 → p99 88 ms, no long tail until p99.99). The hot
path stays fast and lossless under sustained load; the absolute p99 reflects laptop
co-location, not the design ceiling.

## 2. Horizontal worker scaling (drain benchmark)

Seed a fixed backlog of **100,000** events (spread across 50 types × up to 1000 hourly
buckets to avoid single-row lock contention), then time the `rollup-workers` group to
fully roll them up, at 1 vs 3 worker replicas.

```
uv run python -m loadtest.drain_benchmark --events 100000 --scales 1,3
```

| Workers | Drain time | Throughput | Speedup | Correctness (`events==rollup_sum==100k`) |
|---:|---:|---:|---:|:--:|
| 1 | 5.41 s | 18,474 events/s | 1.00× | ✅ |
| 3 | 3.15 s | 31,722 events/s | **1.72×** | ✅ |

**Correctness under concurrency:** with 3 workers consuming the same group in parallel,
the final state is exactly `events=100,000` and `SUM(rollups.count)=100,000` — no
double-counting and no loss. This validates the exactly-once *effect* (PK dedup +
`XACK`-after-commit) holds when Redis distributes entries across multiple consumers.

## Analysis

- **Workers scale horizontally.** Adding replicas to the consumer group increases drain
  throughput (1.72× at 3 workers) with zero code changes — Redis Streams distributes
  pending entries across consumers, and each replica self-names by hostname so they are
  distinct consumers (no shared-id collision).
- **Why sub-linear (1.72×, not 3×):**
  1. The timer includes **worker container start** (scale 0→K, ~1–2 s fixed) — a larger
     share of the short 3-worker run, so the measured speedup is *conservative* vs
     steady-state per-worker throughput.
  2. **Postgres is the shared write ceiling** — all workers write through one Postgres
     on the same host; beyond a few workers, DB write IO / connection capacity, not the
     consumer group, bounds throughput. This matches the design note that the worker is
     the sole writer and Postgres is the eventual scaling limit (mitigated by batched
     multi-row insert + grouped upsert).
- **Implication:** ingest (Redis `XADD`) absorbs bursts cheaply; rollup throughput scales
  by adding workers until Postgres saturates, after which the documented next steps apply
  (PgBouncer, read replicas for metrics, partitioning, or sharding the buffer / Kafka swap).

## Reproduce

```bash
cd apps/backend
uv sync --group loadtest
docker compose -f ../../docker-compose.yml -f ../../docker-compose.loadtest.yml up -d --build --scale worker=1
# wait for: curl -s localhost:8000/readyz
uv run locust -f loadtest/locustfile.py --headless -u 200 -r 50 -t 60s --host http://localhost:8000 \
    --csv loadtest/results/ingest --html loadtest/results/ingest.html
uv run python -m loadtest.drain_benchmark --events 100000 --scales 1,3
docker compose -f ../../docker-compose.yml -f ../../docker-compose.loadtest.yml down
```

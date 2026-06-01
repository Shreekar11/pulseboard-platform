# Load tests & benchmarks

Two complementary measurements (see `results/RESULTS.md` for a captured run):

1. **Ingest hot path** — Locust drives `POST /api/events` and reports throughput +
   latency percentiles + error rate.
2. **Worker scaling** — `drain_benchmark.py` times the consumer group draining a fixed
   backlog at different worker-replica counts, and verifies exactly-once correctness.

## Setup

```bash
cd apps/backend
uv sync --group loadtest    # installs Locust (kept out of the runtime image)
```

Bring up the stack with the load-test override (raises the per-IP rate limit so the
throughput run measures the hot path, not the limiter):

```bash
# from repo root
docker compose -f docker-compose.yml -f docker-compose.loadtest.yml up -d --build --scale worker=1
curl -s localhost:8000/readyz     # {"status":"ready",...}
```

## 1. Ingest load test (Locust)

```bash
uv run locust -f loadtest/locustfile.py --headless \
    -u 200 -r 50 -t 60s --host http://localhost:8000 \
    --csv loadtest/results/ingest --html loadtest/results/ingest.html
```

Outputs `results/ingest_stats.csv`, `ingest_stats_history.csv`, and `ingest.html`.

## 2. Worker-scaling drain benchmark

```bash
uv run python -m loadtest.drain_benchmark --events 100000 --scales 1,3
```

It orchestrates Docker Compose itself (scales workers, seeds the backlog, times the
drain, verifies `events == rollup_sum == N`) and writes `results/drain_results.json`.
Requires Docker running and the compose files at the repo root.

## Scaling workers manually

```bash
docker compose -f docker-compose.yml -f docker-compose.loadtest.yml up -d --scale worker=3
```

Each replica self-names via the hostname default (`CONSUMER_NAME` is intentionally
unset), so all replicas are distinct consumers in the `rollup-workers` group and Redis
fans entries across them. **Do not pin `CONSUMER_NAME` in the environment** — all
replicas would then share one consumer id and the fan-out collapses.

## Teardown

```bash
docker compose -f docker-compose.yml -f docker-compose.loadtest.yml down
```

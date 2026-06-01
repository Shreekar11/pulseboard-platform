"""Locust load test for the ingest hot path (POST /api/events).

Drives maximum throughput from a pool of virtual users, each firing events with a
unique event_id (so nothing is deduped away on the producer side). Locust reports
RPS, p50/p95/p99 latency, and failure rate (any 4xx/5xx counts as a failure).

Run headless against the compose stack:

    uv run locust -f loadtest/locustfile.py --headless \
        -u 200 -r 50 -t 60s --host http://localhost:8000 \
        --csv loadtest/results/ingest --html loadtest/results/ingest.html

Note: run the API with a raised rate limit (docker-compose.loadtest.yml) so this
measures the hot path, not the per-IP limiter.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime

from locust import HttpUser, constant, task

EVENT_TYPES = ["signup", "click", "purchase", "view", "logout"]


class IngestUser(HttpUser):
    wait_time = constant(0)  # no think time — push the hot path

    @task
    def post_event(self) -> None:
        self.client.post(
            "/api/events",
            json={
                "event_id": f"evt_{uuid.uuid4().hex}",
                "type": random.choice(EVENT_TYPES),
                "user_id": f"u{random.randint(1, 10_000)}",
                "ts": datetime.now(UTC).isoformat(),
            },
            name="POST /api/events",
        )

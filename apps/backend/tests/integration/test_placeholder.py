"""Integration tests run against real Postgres + Redis via testcontainers.

Implemented in the testing milestone of the implementation plan. Cases to cover
(Phase-1-Backend §13):
- ingest -> stream (no Postgres on the hot path)
- duplicate event_id counted exactly once
- worker replay / crash-before-XACK idempotency
- metrics gap-fill (hour/day/week) and half-open [from, to) boundaries
- top-N ordering + limit
- rate-limit 429 shared across replicas
- /readyz reflects Redis + Postgres
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="implemented in the testing milestone (needs Docker/testcontainers)")
def test_ingest_to_metrics_roundtrip(): ...

"""SQL for the rollup worker — one atomic statement per batch.

Persist raw events (dedup on event_id) and increment hourly rollups for
*newly-inserted* rows only, via a single CTE so the whole thing is one statement
inside one transaction (Phase-1-Backend §5, §10). The session timezone is UTC
(see app.core.db.create_pool), so date_trunc('hour', ts) buckets in UTC.
"""

PERSIST_BATCH = """
WITH input AS (
    SELECT * FROM unnest(
        $1::text[], $2::text[], $3::text[], $4::text[], $5::timestamptz[], $6::text[]
    ) AS t(event_id, tenant, type, user_id, ts, props)
),
ins AS (
    INSERT INTO events (event_id, tenant, type, user_id, ts, props)
    SELECT event_id, tenant, type, NULLIF(user_id, ''), ts, NULLIF(props, '')::jsonb
    FROM input
    ON CONFLICT (event_id) DO NOTHING
    RETURNING tenant, type, ts
)
INSERT INTO rollups (tenant, type, bucket, count)
SELECT tenant, type, date_trunc('hour', ts), count(*)
FROM ins
GROUP BY tenant, type, date_trunc('hour', ts)
ON CONFLICT (tenant, type, bucket)
DO UPDATE SET count = rollups.count + EXCLUDED.count;
"""

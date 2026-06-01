"""init: events + rollups

Locked Phase-1-Backend schema (§6):
- events:  raw, write-optimized, PRIMARY KEY(event_id) for free dedup.
- rollups: read-optimized, permanent, PK(tenant, type, bucket) for range scans,
           plus (tenant, bucket) index for /metrics/top.

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE events (
            event_id   TEXT PRIMARY KEY,
            tenant     TEXT NOT NULL DEFAULT 'default',
            type       TEXT NOT NULL,
            user_id    TEXT,
            ts         TIMESTAMPTZ NOT NULL,
            props      JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE rollups (
            tenant TEXT NOT NULL,
            type   TEXT NOT NULL,
            bucket TIMESTAMPTZ NOT NULL,
            count  BIGINT NOT NULL,
            PRIMARY KEY (tenant, type, bucket)
        );
        """
    )
    op.execute("CREATE INDEX rollups_tenant_bucket_idx ON rollups (tenant, bucket);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rollups;")
    op.execute("DROP TABLE IF EXISTS events;")

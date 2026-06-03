"""Application configuration (12-factor, env-driven).

Single source of settings for both the API and the worker. Buffer Redis and
rate-limit Redis are kept as separate URLs so they can be split into distinct
instances in production (see Phase-1-Backend §3, §9).
"""

from __future__ import annotations

import socket
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Postgres ---
    database_url: str = "postgresql://pulse:pulse@localhost:5432/pulseboard"
    db_pool_min: int = 2
    db_pool_max: int = 10

    # --- Redis: ingest stream buffer ---
    redis_buffer_url: str = "redis://localhost:6379/0"

    # --- Redis: rate limiter (separate logical DB locally, separate instance in prod) ---
    redis_ratelimit_url: str = "redis://localhost:6379/1"

    # --- Stream / consumer group ---
    events_stream: str = "events"
    consumer_group: str = "rollup-workers"
    # Unique per replica so multiple workers don't share one consumer id. Defaults
    # to the hostname (pod name in K8s); override with CONSUMER_NAME.
    consumer_name: str = Field(default_factory=socket.gethostname)
    stream_maxlen: int = 1_000_000  # backstop trim bound (approximate, '~')

    # --- Worker batching (freshness vs write-amplification knob) ---
    worker_batch_size: int = 500
    worker_block_ms: int = 500
    worker_claim_idle_ms: int = 30_000

    # --- Rate limiting (per-IP sliding window) ---
    ratelimit_requests: int = 100
    ratelimit_window_seconds: int = 1

    # --- Validation ---
    props_max_bytes: int = 8192

    # --- Misc ---
    default_tenant: str = "default"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    cloud_provider: str = "local"
    region: str = "local"
    app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (read env once per process)."""
    return Settings()

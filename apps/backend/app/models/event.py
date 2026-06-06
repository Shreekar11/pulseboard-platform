"""Ingest request/response models (Pydantic v2).

`EventIn` is the spec-derived DTO (`app.models.generated.EventIn`) extended with
domain behavior: required ids, UTC timestamp normalization, props size cap, and
flattening to Redis stream fields. `tenant` is server-assigned ('default') in
Phase 1 — not accepted from clients (no auth).

See openapi/openapi.json for the contract.
"""

from __future__ import annotations

import json
from datetime import datetime

from pydantic import field_validator, model_validator

from app.config import get_settings
from app.core.timeutil import now_utc, to_utc
from app.models.generated import EventAccepted
from app.models.generated import EventIn as EventInBase

__all__ = ["EventIn", "EventAccepted"]


class EventIn(EventInBase):
    # Override the generated `AwareDatetime` field so naive timestamps are
    # accepted and normalized to UTC by the validator below (assumed UTC).
    ts: datetime | None = None

    @field_validator("ts")
    @classmethod
    def _normalize_ts(cls, v: datetime | None) -> datetime | None:
        return to_utc(v) if v is not None else None

    @model_validator(mode="after")
    def _check_props_size(self) -> EventIn:
        if self.props is not None:
            size = len(json.dumps(self.props, separators=(",", ":")).encode("utf-8"))
            limit = get_settings().props_max_bytes
            if size > limit:
                raise ValueError(f"props exceeds {limit} bytes (got {size})")
        return self

    def to_stream_fields(self) -> dict[str, str]:
        """Flatten to the string field map XADD'd to the Redis stream."""
        settings = get_settings()
        ts = self.ts or now_utc()
        return {
            "event_id": self.event_id,
            "tenant": settings.default_tenant,
            "type": self.type,
            "user_id": str(self.user_id.root) if self.user_id is not None else "",
            "ts": ts.isoformat(),
            "props": json.dumps(self.props, separators=(",", ":"))
            if self.props is not None
            else "",
        }

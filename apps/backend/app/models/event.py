"""Ingest request/response models (Pydantic v2).

Validation + normalization for `POST /api/events`: required ids, UTC timestamp
normalization, props size cap. `tenant` is server-assigned ('default') in Phase 1
— not accepted from clients (no auth).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings
from app.core.timeutil import now_utc, to_utc


class EventIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=255)
    user_id: str | None = Field(default=None, max_length=255)
    ts: datetime | None = None
    props: dict[str, Any] | None = None

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
            "user_id": self.user_id or "",
            "ts": ts.isoformat(),
            "props": json.dumps(self.props) if self.props is not None else "",
        }


class EventAccepted(BaseModel):
    status: str = "accepted"
    event_id: str

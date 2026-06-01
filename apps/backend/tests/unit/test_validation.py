"""Unit tests for ingest validation + normalization (no external services)."""

from __future__ import annotations

from datetime import UTC

import pytest
from app.models.event import EventIn
from pydantic import ValidationError


def test_minimal_event_is_valid():
    e = EventIn(event_id="evt_1", type="signup")
    assert e.event_id == "evt_1"
    assert e.ts is None  # filled at stream-fields time


def test_missing_event_id_rejected():
    with pytest.raises(ValidationError):
        EventIn(type="signup")


def test_blank_type_rejected():
    with pytest.raises(ValidationError):
        EventIn(event_id="evt_1", type="")


def test_ts_normalized_to_utc():
    e = EventIn(event_id="evt_1", type="click", ts="2026-01-01T12:00:00+05:00")
    assert e.ts.tzinfo == UTC
    assert e.ts.hour == 7  # 12:00+05:00 -> 07:00Z


def test_oversized_props_rejected(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("PROPS_MAX_BYTES", "32")
    with pytest.raises(ValidationError):
        EventIn(event_id="evt_1", type="click", props={"k": "x" * 100})
    get_settings.cache_clear()


def test_to_stream_fields_defaults_tenant_and_ts():
    fields = EventIn(event_id="evt_1", type="signup").to_stream_fields()
    assert fields["tenant"] == "default"
    assert fields["event_id"] == "evt_1"
    assert fields["ts"]  # defaulted to now()

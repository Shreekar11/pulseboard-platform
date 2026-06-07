"""Unit tests for GET /api/info — no infrastructure required."""

from __future__ import annotations

from unittest.mock import patch

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def _client():
    return TestClient(create_app(), raise_server_exceptions=True)


def test_info_returns_defaults():
    client = _client()
    resp = client.get("/api/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cloud_provider"] == "local"
    assert body["region"] == "local"
    assert body["version"] == "0.1.0"
    assert body["buffer"] == "redis-streams"


def test_info_reflects_env_overrides():
    custom = Settings(cloud_provider="aws", region="eu-west-1", app_version="1.2.3")
    with patch("app.api.info.get_settings", return_value=custom):
        client = _client()
        resp = client.get("/api/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cloud_provider"] == "aws"
    assert body["region"] == "eu-west-1"
    assert body["version"] == "1.2.3"

"""Deployment metadata: GET /api/info.

Read-only, no dependencies — returns env-configured deployment metadata
(cloud provider, region, version, buffer type).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.info import InfoResponse

router = APIRouter(prefix="/api", tags=["info"])


@router.get("/info", response_model=InfoResponse)
async def get_info() -> InfoResponse:
    s = get_settings()
    return InfoResponse(
        cloud_provider=s.cloud_provider,
        region=s.region,
        version=s.app_version,
        buffer=s.buffer_type,
    )

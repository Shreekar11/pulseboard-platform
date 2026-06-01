"""Metrics read API: GET /api/metrics and GET /api/metrics/top.

Reads pre-aggregated rollups only (never raw events). Half-open `[from, to)`,
UTC, gap-filled. Validates params; raises 422 on bad input.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.config import get_settings
from app.core.timeutil import INTERVAL_STEPS, to_utc
from app.deps import PoolDep
from app.models.metrics import MetricsResponse, TopResponse
from app.services import metrics_service

router = APIRouter(prefix="/api", tags=["metrics"])


def _validate_range(from_: datetime, to: datetime) -> tuple[datetime, datetime]:
    f, t = to_utc(from_), to_utc(to)
    if f >= t:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`from` must be strictly before `to`",
        )
    return f, t


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    pool: PoolDep,
    type: str = Query(min_length=1),
    from_: datetime = Query(alias="from"),
    to: datetime = Query(),
    interval: str = Query(default="day"),
):
    if interval not in INTERVAL_STEPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"interval must be one of {sorted(INTERVAL_STEPS)}",
        )
    f, t = _validate_range(from_, to)
    series = await metrics_service.get_series(
        pool,
        tenant=get_settings().default_tenant,
        type_=type,
        from_=f,
        to=t,
        interval=interval,
    )
    return MetricsResponse(type=type, interval=interval, from_=f, to=t, series=series)


@router.get("/metrics/top", response_model=TopResponse)
async def get_top(
    pool: PoolDep,
    dimension: str = Query(default="type"),
    from_: datetime = Query(alias="from"),
    to: datetime = Query(),
    limit: int = Query(default=10, ge=1, le=100),
):
    if dimension != "type":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="only dimension=type is supported in Phase 1",
        )
    f, t = _validate_range(from_, to)
    items = await metrics_service.get_top(
        pool, tenant=get_settings().default_tenant, from_=f, to=t, limit=limit
    )
    return TopResponse(dimension=dimension, from_=f, to=t, items=items)

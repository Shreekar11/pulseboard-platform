"""Metrics query/response models (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricPoint(BaseModel):
    bucket: datetime
    count: int


class MetricsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    interval: str
    from_: datetime = Field(alias="from")
    to: datetime
    series: list[MetricPoint]


class TopItem(BaseModel):
    type: str
    count: int


class TopResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dimension: str
    from_: datetime = Field(alias="from")
    to: datetime
    items: list[TopItem]

"""Unified error envelope returned by all endpoints.

Shape: ``{"error": {"code": ..., "message": ..., "details": ...}}``.
Applied via exception handlers registered in app.main.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody

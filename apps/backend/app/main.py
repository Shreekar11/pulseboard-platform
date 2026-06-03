"""FastAPI application factory.

Wires shared resources (Postgres pool, Redis buffer + rate-limit clients, the
EventBuffer adapter, the rate limiter) into ``app.state`` during the lifespan, and
registers routers + a unified error envelope.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import events, health, metrics
from app.config import Settings, get_settings
from app.core import db
from app.core import redis as redis_core
from app.core.buffer import RedisStreamBuffer
from app.core.ratelimit import RateLimiter
from app.models.errors import ErrorBody, ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app.state.settings = settings
    app.state.pool = await db.create_pool(settings)
    app.state.buffer_client = redis_core.create_buffer_client(settings)
    app.state.ratelimit_client = redis_core.create_ratelimit_client(settings)
    app.state.buffer = RedisStreamBuffer(app.state.buffer_client, settings)
    app.state.rate_limiter = RateLimiter(app.state.ratelimit_client, settings)
    try:
        yield
    finally:
        await db.close_pool(app.state.pool)
        await app.state.buffer_client.aclose()
        await app.state.ratelimit_client.aclose()


def _error(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorBody(code=code, message=message, details=details)
        ).model_dump(),
    )


def create_app() -> FastAPI:
    app = FastAPI(title="PulseBoard Backend", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request, exc: RequestValidationError):
        return _error(422, "validation_error", "request validation failed", exc.errors())

    @app.exception_handler(HTTPException)
    async def _http_handler(_request, exc: HTTPException):
        code = "rate_limited" if exc.status_code == 429 else f"http_{exc.status_code}"
        return _error(exc.status_code, code, str(exc.detail))

    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(metrics.router)
    return app


app = create_app()

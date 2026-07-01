"""FastAPI application entrypoint for Trip Weather Planner."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.cache import TTLCache
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
)
from app.routers import forecast

settings = get_settings()

app = FastAPI(
    title="Trip Weather Planner API",
    version=__version__,
    description=(
        "Weather-first travel planning backend. Ingests CWA township forecasts "
        "(falls back to mock data without a key), normalizes to daily summaries, "
        "and adds an AI trip summary. Third-party APIs are proxied server-side; "
        "keys never reach the frontend."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.state.cache = TTLCache(default_ttl=settings.cache_ttl_seconds)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


app.include_router(forecast.router)


@app.get("/")
async def root() -> dict:
    return {
        "name": "Trip Weather Planner API",
        "version": __version__,
        "mock_mode": settings.use_mock,
        "docs": "/docs",
    }

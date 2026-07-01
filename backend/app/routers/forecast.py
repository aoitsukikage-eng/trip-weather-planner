"""Forecast API routes."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Query, Request

from app.adapters.cwa import CWAAdapter
from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.data.towns import all_towns, get_town
from app.schemas.common import ApiResponse, Meta
from app.schemas.weather import (
    AiSummary,
    ForecastData,
    ForecastResult,
    Town,
)
from app.services.ai_summary import AiSummaryService
from app.services.weather import normalize_to_daily, pick_target_day

router = APIRouter(prefix="/api", tags=["forecast"])


def _meta(request: Request, *, cached: bool = False, source: str | None = None) -> Meta:
    return Meta(
        request_id=getattr(request.state, "request_id", "unknown"),
        cached=cached,
        source=source,
    )


@router.get("/health")
async def health(request: Request) -> ApiResponse[dict]:
    settings = get_settings()
    return ApiResponse[dict](
        data={"status": "ok", "mock_mode": settings.use_mock},
        meta=_meta(request),
    )


@router.get("/towns")
async def towns(request: Request) -> ApiResponse[list[Town]]:
    return ApiResponse[list[Town]](data=all_towns(), meta=_meta(request))


@router.get("/forecast")
async def forecast(
    request: Request,
    town: str = Query(..., description="Town code, e.g. 'taipei-zhongzheng'"),
    target_date: str = Query(
        ..., alias="date", description="Target date, YYYY-MM-DD"
    ),
) -> ApiResponse[ForecastResult]:
    settings = get_settings()
    cache = request.app.state.cache

    town_obj = get_town(town)
    if town_obj is None:
        raise NotFoundError(f"Unknown town code: {town}", error_code="unknown_town")

    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError as exc:
        raise AppError(
            "Invalid date; expected YYYY-MM-DD.", error_code="invalid_date"
        ) from exc

    cache_key = f"forecast:{town}:{target_date}"
    cached = cache.get(cache_key)
    if cached is not None:
        return ApiResponse[ForecastResult](
            data=cached, meta=_meta(request, cached=True, source="cache")
        )

    adapter = CWAAdapter(settings)
    slices, source = await adapter.fetch_time_slices(town_obj, parsed_date)
    all_days = normalize_to_daily(slices)
    days = pick_target_day(all_days, target_date)

    forecast_data = ForecastData(
        town=town_obj,
        target_date=target_date,
        source_dataset=source,
        days=days,
        generated_at=datetime.now(UTC).isoformat(),
    )

    ai = AiSummaryService(settings)
    summary_text, mode = ai.summarize(town_obj, days)
    result = ForecastResult(
        forecast=forecast_data,
        ai_summary=AiSummary(text=summary_text, mode=mode),
    )

    cache.set(cache_key, result, ttl=settings.cache_ttl_seconds)
    return ApiResponse[ForecastResult](
        data=result, meta=_meta(request, cached=False, source=source)
    )

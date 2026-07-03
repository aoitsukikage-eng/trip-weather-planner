"""Forecast API routes."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Query, Request

from app.adapters.cwa import CWAAdapter
from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError, UpstreamError
from app.data.towns import all_towns, get_town
from app.schemas.common import ApiResponse, Meta
from app.schemas.weather import (
    AiSummary,
    ForecastData,
    ForecastResult,
    Town,
)
from app.services.ai_summary import AiSummaryService
from app.services.weather import normalize_to_daily

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
    settings = get_settings()
    cache = request.app.state.cache
    if settings.use_mock:
        return ApiResponse[list[Town]](data=all_towns(), meta=_meta(request, source="mock"))

    adapter = CWAAdapter(settings, cache)
    try:
        town_list = await adapter.fetch_all_towns()
        return ApiResponse[list[Town]](data=town_list, meta=_meta(request, source="cwa-live"))
    except UpstreamError:
        return ApiResponse[list[Town]](
            data=all_towns(),
            meta=_meta(request, source="static-fallback"),
        )


@router.get("/forecast")
async def forecast(
    request: Request,
    town: str = Query(..., description="Town code, e.g. 'taipei-xinyi'"),
    target_date: str = Query(
        ..., alias="date", description="Target date, YYYY-MM-DD"
    ),
) -> ApiResponse[ForecastResult]:
    settings = get_settings()
    cache = request.app.state.cache

    town_obj = get_town(town)
    if town_obj is None and not settings.use_mock:
        adapter = CWAAdapter(settings, cache)
        try:
            live_towns = await adapter.fetch_all_towns()
            town_obj = next((item for item in live_towns if item.code == town), None)
        except UpstreamError:
            town_obj = None
    if town_obj is None:
        raise NotFoundError(f"Unknown town code: {town}", error_code="unknown_town")

    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError as exc:
        raise AppError(
            "Invalid date; expected YYYY-MM-DD.", error_code="invalid_date"
        ) from exc
    if not _is_date_in_window(parsed_date):
        raise AppError(
            "Date must be within today..today+6.",
            error_code="date_out_of_range",
        )

    cache_key = f"forecast:{town}:{target_date}"
    cached = cache.get(cache_key)
    if cached is not None:
        return ApiResponse[ForecastResult](
            data=cached, meta=_meta(request, cached=True, source="cache")
        )

    adapter = CWAAdapter(settings, cache)
    slices, source = await adapter.fetch_time_slices(town_obj, parsed_date)
    # Return the full forecast horizon (multi-day). The target date is carried in
    # ForecastData.target_date so the frontend can highlight it among the days.
    days = normalize_to_daily(slices)
    sunrise_sunset = None
    uv_info = None
    try:
        sunrise_sunset = await adapter.fetch_sunrise_sunset(town_obj, parsed_date)
    except UpstreamError:
        sunrise_sunset = None
    try:
        uv_info = await adapter.fetch_uv_info(town_obj)
    except UpstreamError:
        uv_info = None

    forecast_data = ForecastData(
        town=town_obj,
        target_date=target_date,
        source_dataset=source,
        days=days,
        sunrise_sunset=sunrise_sunset,
        uv=uv_info,
        generated_at=datetime.now(UTC).isoformat(),
    )

    ai = AiSummaryService(settings)
    summary_text, mode = ai.summarize(town_obj, days, target_date)
    result = ForecastResult(
        forecast=forecast_data,
        ai_summary=AiSummary(text=summary_text, mode=mode),
    )

    cache.set(cache_key, result, ttl=settings.cache_ttl_seconds)
    return ApiResponse[ForecastResult](
        data=result, meta=_meta(request, cached=False, source=source)
    )


def _is_date_in_window(target: date) -> bool:
    delta = (target - date.today()).days
    return 0 <= delta <= 6

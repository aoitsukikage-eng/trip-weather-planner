"""Forecast API routes."""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

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
from app.services.weather import (
    normalize_to_daily,
    normalize_to_hourly,
)

router = APIRouter(prefix="/api", tags=["forecast"])
TAIPEI_TZ = ZoneInfo("Asia/Taipei")


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
    if not _is_date_in_supported_range(parsed_date):
        raise AppError(
            "Date must be between today and today+10.",
            error_code="date_out_of_range",
        )

    cache_key = f"forecast:{town}:{target_date}"
    cached = cache.get(cache_key)
    if cached is not None:
        return ApiResponse[ForecastResult](
            data=cached, meta=_meta(request, cached=True, source="cache")
        )

    adapter = CWAAdapter(settings, cache)
    slices = await adapter.fetch_forecast_slices(town_obj)
    # Return the full week plus the near-term 72h chart data in one response.
    days = normalize_to_daily(slices.daily)
    if not _horizon_contains_date(days, target_date):
        raise AppError(
            "Date must be within the available forecast horizon.",
            error_code="date_out_of_range",
        )
    hourly_slots = normalize_to_hourly(slices.hourly)
    hourly = hourly_slots or None
    sunrise_sunset = None
    uv_info = None
    try:
        sunrise_sunset = await adapter.fetch_sunrise_sunset(town_obj, parsed_date)
    except UpstreamError:
        sunrise_sunset = None
    try:
        uv_info = await adapter.fetch_uv_info(town_obj, parsed_date)
    except UpstreamError:
        uv_info = None

    forecast_data = ForecastData(
        town=town_obj,
        target_date=target_date,
        source_dataset=slices.source_label,
        days=days,
        hourly=hourly,
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
        data=result, meta=_meta(request, cached=False, source=slices.source_label)
    )


def _taipei_today() -> date:
    return datetime.now(TAIPEI_TZ).date()


def _is_date_in_supported_range(target: date, today: date | None = None) -> bool:
    anchor = today or _taipei_today()
    delta = (target - anchor).days
    return 0 <= delta <= 10


def _horizon_contains_date(days: list, target_date: str) -> bool:
    return any(day.date == target_date for day in days)

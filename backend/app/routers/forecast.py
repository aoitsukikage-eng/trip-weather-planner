"""Forecast API routes."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Request

from app.adapters.cwa import CWAAdapter
from app.adapters.moenv import MOENVAdapter
from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError, UpstreamError
from app.data.towns import all_towns, canonical_code_for, get_canonical_town, get_town
from app.i18n.weather_text import LangType
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
    trim_daily_to_window,
)

logger = logging.getLogger("app.routers.forecast")

router = APIRouter(prefix="/api", tags=["forecast"])
TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def _meta(request: Request, *, cached: bool = False, source: str | None = None) -> Meta:
    return Meta(
        request_id=getattr(request.state, "request_id", "unknown"),
        cached=cached,
        source=source,
    )


def _log_forecast(
    *,
    request_id: str,
    canonical_town: str,
    cache_result: str,
    source: str | None,
    duration_ms: float,
    degraded_fields: list[str],
) -> None:
    extra = {
        "request_id": request_id,
        "canonical_town": canonical_town,
        "cache_result": cache_result,
        "source": source,
        "duration_ms": duration_ms,
        "degraded_fields": degraded_fields,
    }
    logger.info(
        "forecast completed: request_id=%s canonical_town=%s cache_result=%s "
        "source=%s duration_ms=%.2f degraded_fields=%s",
        request_id,
        canonical_town,
        cache_result,
        source,
        duration_ms,
        degraded_fields,
        extra=extra,
    )


@router.get("/health")
async def health(request: Request) -> ApiResponse[dict]:
    settings = get_settings()
    return ApiResponse[dict](
        data={"status": "ok", "mock_mode": settings.use_mock},
        meta=_meta(request),
    )


@router.get("/towns")
async def towns(
    request: Request,
    lang: LangType = Query("zh", description="Language ('zh', 'en', or 'ja')"),  # noqa: B008
) -> ApiResponse[list[Town]]:
    return ApiResponse[list[Town]](
        data=all_towns(), meta=_meta(request, source="local-catalog")
    )


@router.get("/forecast")
async def forecast(
    request: Request,
    town: str = Query(..., description="Town code, e.g. 'taipei-xinyi'"),  # noqa: B008
    target_date: str = Query(..., alias="date", description="Target date, YYYY-MM-DD"),  # noqa: B008
    lang: LangType = Query("zh", description="Language ('zh', 'en', or 'ja')"),  # noqa: B008
) -> ApiResponse[ForecastResult]:
    start_time = time.monotonic()
    settings = get_settings()
    cache = getattr(request.app.state, "cache", None)
    single_flight = getattr(request.app.state, "single_flight", None)
    http_client = getattr(request.app.state, "http_client", None)
    request_id = getattr(request.state, "request_id", "unknown")

    town_obj = get_town(town)
    canonical_code = canonical_code_for(town)
    canonical_town = get_canonical_town(town)
    if town_obj is None or canonical_code is None or canonical_town is None:
        raise NotFoundError(f"Unknown town code: {town}", error_code="unknown_town")

    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError as exc:
        raise AppError("Invalid date; expected YYYY-MM-DD.", error_code="invalid_date") from exc
    if not _is_date_in_supported_range(parsed_date):
        raise AppError(
            "Date must be between today and today+10.",
            error_code="date_out_of_range",
        )

    # Public identity cache key preserves caller's town representation
    public_cache_key = f"forecast:{town}:{target_date}:{lang}"
    if cache is not None:
        cached_entry = cache.get_entry(public_cache_key)
        if cached_entry.status == "fresh":
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            _log_forecast(
                request_id=request_id,
                canonical_town=canonical_code,
                cache_result="fresh",
                source="cache",
                duration_ms=duration_ms,
                degraded_fields=[],
            )
            return ApiResponse[ForecastResult](
                data=cached_entry.value,
                meta=_meta(request, cached=True, source="cache"),
            )

    semaphore = asyncio.Semaphore(settings.upstream_concurrency_limit)
    adapter = CWAAdapter(
        settings,
        cache,
        client=http_client,
        single_flight=single_flight,
        semaphore=semaphore,
    )
    moenv = MOENVAdapter(
        settings,
        cache,
        client=http_client,
        single_flight=single_flight,
        semaphore=semaphore,
    )

    flight_key = f"build:{town}:{target_date}:{lang}"

    async def _do_build() -> tuple[ForecastResult, str, list[str]]:
        degraded_fields: list[str] = []

        # Group 1: Core weekly & near-term slices (max 2 concurrent upstream operations)
        slices = await adapter.fetch_forecast_slices(canonical_town)
        days = trim_daily_to_window(
            normalize_to_daily(slices.daily, lang=lang), _taipei_today()
        )
        focused_date = target_date
        date_adjusted = False
        is_missing_today = (
            target_date == _taipei_today().isoformat()
            and days
            and not _horizon_contains_date(days, target_date)
        )
        if is_missing_today:
            focused_date = days[0].date
            date_adjusted = True
        elif not _horizon_contains_date(days, target_date):
            raise AppError(
                "Date must be within the available forecast horizon.",
                error_code="date_out_of_range",
            )

        if not slices.hourly:
            hourly = None
            degraded_fields.append("hourly")
        else:
            hourly_slots = normalize_to_hourly(slices.hourly, lang=lang)
            hourly = hourly_slots or None
            if hourly is None:
                degraded_fields.append("hourly")

        focused_day = date.fromisoformat(focused_date)

        # Group 2: Sunrise/sunset, UV, moon (bounded fan-out <= 3)
        async def _get_sunrise():
            try:
                return await adapter.fetch_sunrise_sunset(
                    town_obj, focused_day, lang=lang
                )
            except UpstreamError:
                degraded_fields.append("sunrise_sunset")
                return None

        async def _get_uv():
            try:
                return await adapter.fetch_uv_info(town_obj, focused_day, lang=lang)
            except UpstreamError:
                degraded_fields.append("uv")
                return None

        async def _get_moon():
            try:
                return await adapter.fetch_moon(town_obj, focused_day, lang=lang)
            except UpstreamError:
                degraded_fields.append("moon")
                return None

        sunrise_sunset, uv_info, moon = await asyncio.gather(
            _get_sunrise(), _get_uv(), _get_moon()
        )

        # Group 3: Warnings, AQI current, AQI forecast (bounded fan-out <= 3)
        async def _get_warnings():
            try:
                return await adapter.fetch_warnings(town_obj, lang=lang)
            except UpstreamError:
                degraded_fields.append("warnings")
                return []

        async def _get_aqi():
            try:
                return await moenv.fetch_current(town_obj, lang=lang)
            except UpstreamError:
                degraded_fields.append("aqi")
                return None

        async def _get_aqi_forecasts():
            try:
                return await moenv.fetch_forecast(town_obj.city, lang=lang)
            except UpstreamError:
                degraded_fields.append("aqi_forecast")
                return {}

        warnings, aqi, aqi_forecasts = await asyncio.gather(
            _get_warnings(), _get_aqi(), _get_aqi_forecasts()
        )

        for day in days:
            if day.date in aqi_forecasts:
                day.aqi_forecast = aqi_forecasts[day.date]

        forecast_data = ForecastData(
            town=town_obj,
            target_date=focused_date,
            requested_date=target_date if date_adjusted else None,
            date_adjusted=date_adjusted,
            source_dataset=slices.source_label,
            days=days,
            hourly=hourly,
            sunrise_sunset=sunrise_sunset,
            uv=uv_info,
            aqi=aqi,
            warnings=warnings,
            moon=moon,
            generated_at=datetime.now(UTC).isoformat(),
        )

        ai = AiSummaryService(settings)
        summary_text, mode = ai.summarize(days, focused_date, lang=lang)
        res = ForecastResult(
            forecast=forecast_data,
            ai_summary=AiSummary(text=summary_text, mode=mode),
        )
        return res, slices.source_label, degraded_fields

    try:
        if single_flight is not None:
            result, source_label, degraded_fields = await asyncio.wait_for(
                single_flight.run(flight_key, _do_build),
                timeout=settings.forecast_timeout_seconds,
            )
        else:
            result, source_label, degraded_fields = await asyncio.wait_for(
                _do_build(),
                timeout=settings.forecast_timeout_seconds,
            )

        if cache is not None:
            cache.set(
                public_cache_key,
                result,
                ttl=settings.cache_ttl_seconds,
                stale_retention=settings.stale_retention_seconds,
            )
            # If requested town was an alias, populate canonical key with canonical town identity
            if town != canonical_code:
                canonical_cache_key = (
                    f"forecast:{canonical_code}:{target_date}:{lang}"
                )
                canonical_result = result.model_copy(deep=True)
                canonical_result.forecast.town = canonical_town
                cache.set(
                    canonical_cache_key,
                    canonical_result,
                    ttl=settings.cache_ttl_seconds,
                    stale_retention=settings.stale_retention_seconds,
                )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        _log_forecast(
            request_id=request_id,
            canonical_town=canonical_code,
            cache_result="miss",
            source=source_label,
            duration_ms=duration_ms,
            degraded_fields=degraded_fields,
        )
        return ApiResponse[ForecastResult](
            data=result, meta=_meta(request, cached=False, source=source_label)
        )
    except (TimeoutError, AppError, Exception) as exc:
        if isinstance(exc, AppError) and not isinstance(exc, UpstreamError):
            # Client / input validation errors should not trigger stale fallback
            raise

        stale_result = None
        if cache is not None:
            stale_entry = cache.get_entry(public_cache_key)
            if (
                stale_entry.status in ("fresh", "stale")
                and stale_entry.value is not None
            ):
                stale_result = stale_entry.value
            else:
                canonical_cache_key = (
                    f"forecast:{canonical_code}:{target_date}:{lang}"
                )
                canon_entry = cache.get_entry(canonical_cache_key)
                if (
                    canon_entry.status in ("fresh", "stale")
                    and canon_entry.value is not None
                ):
                    stale_result = canon_entry.value.model_copy(deep=True)
                    stale_result.forecast.town = town_obj

        if stale_result is not None:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            _log_forecast(
                request_id=request_id,
                canonical_town=canonical_code,
                cache_result="stale",
                source="stale-cache",
                duration_ms=duration_ms,
                degraded_fields=["upstream_error"],
            )
            return ApiResponse[ForecastResult](
                data=stale_result,
                meta=_meta(request, cached=True, source="stale-cache"),
            )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        _log_forecast(
            request_id=request_id,
            canonical_town=canonical_code,
            cache_result="miss",
            source=None,
            duration_ms=duration_ms,
            degraded_fields=["all"],
        )
        if isinstance(exc, asyncio.TimeoutError):
            raise UpstreamError(
                "Forecast build timed out.", error_code="upstream_timeout"
            ) from exc
        raise


def _taipei_today() -> date:
    return datetime.now(TAIPEI_TZ).date()


def _is_date_in_supported_range(target: date, today: date | None = None) -> bool:
    anchor = today or _taipei_today()
    delta = (target - anchor).days
    return 0 <= delta <= 10


def _horizon_contains_date(days: list, target_date: str) -> bool:
    return any(day.date == target_date for day in days)

"""Deterministic mock weather slices, used when no CWA key is configured.

The values are stable for a given (town, date, dataset) so tests and demos are
reproducible. Cadence mirrors the real datasets: F-D0047-093 => 3h slices for
2 days; F-D0047-091 => 12h slices for 7 days.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

from app.schemas.weather import SunriseSunset, TimeSlice, Town, UVInfo


def _stable_unit(*parts: str) -> float:
    """Return a stable pseudo-random float in [0, 1) from the given parts."""
    digest = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _weather_text(pop: int) -> str:
    if pop >= 70:
        return "陰時多雲短暫雨"
    if pop >= 40:
        return "多雲時陰"
    if pop >= 20:
        return "多雲"
    return "晴時多雲"


def mock_time_slices(
    dataset_id: str, town: Town, horizon_start: date | None = None
) -> list[TimeSlice]:
    cadence_hours, days = (3, 2) if dataset_id.endswith("093") else (12, 7)
    start = horizon_start or date.today()
    # Warmer in the south (lower latitude), cooler in the north.
    base_temp = 30.0 - (town.lat - 22.0) * 1.1

    slices: list[TimeSlice] = []
    steps = int(days * 24 / cadence_hours)
    for i in range(steps):
        ts = datetime.combine(start, datetime.min.time()) + timedelta(hours=i * cadence_hours)
        hour = ts.hour
        # Diurnal swing: coldest ~05:00, warmest ~14:00.
        diurnal = -4.0 if 0 <= hour < 9 else (3.5 if 9 <= hour < 18 else -1.0)
        noise = (_stable_unit(town.code, ts.isoformat()) - 0.5) * 3.0
        temp = round(base_temp + diurnal + noise, 1)
        pop = int(_stable_unit("pop", town.code, ts.date().isoformat(), str(hour)) * 100)
        slices.append(
            TimeSlice(
                start=ts.isoformat(),
                end=(ts + timedelta(hours=cadence_hours)).isoformat(),
                temp_c=temp,
                pop_percent=pop,
                weather=_weather_text(pop),
            )
        )
    return slices


def mock_sunrise_sunset(town: Town, target_date: date) -> SunriseSunset:
    day_of_year = target_date.timetuple().tm_yday
    seasonal_shift = int(18 * (1 - abs(182 - day_of_year) / 182))
    latitude_shift = int((town.lat - 23.5) * 2)
    sunrise_minutes = 360 - seasonal_shift + latitude_shift
    sunset_minutes = 1080 + seasonal_shift - latitude_shift
    return SunriseSunset(
        county=town.city,
        target_date=target_date.isoformat(),
        source_date=target_date.isoformat(),
        sunrise_time=_format_minutes(sunrise_minutes),
        sunset_time=_format_minutes(sunset_minutes),
        is_approximate=False,
    )


def mock_uv_info(town: Town, target_date: date) -> UVInfo:
    base = 6 + int((24.5 - town.lat) * 0.7)
    seasonal = 1 if 4 <= target_date.month <= 9 else -1
    value = float(max(1, min(12, base + seasonal)))
    return UVInfo(
        value=value,
        level=_uv_level(value),
        source_label="目前紫外線",
        source_type="observation",
        observed_at=f"{target_date.isoformat()}T12:00:00+08:00",
        station_id=f"mock-{town.code}",
        station_name=f"{town.name} mock station",
    )


def _format_minutes(total_minutes: int) -> str:
    total_minutes %= 24 * 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _uv_level(value: float) -> str:
    if value <= 2:
        return "低"
    if value <= 5:
        return "中"
    if value <= 7:
        return "高"
    if value <= 10:
        return "過量"
    return "危險"

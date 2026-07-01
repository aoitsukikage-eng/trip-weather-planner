"""Deterministic mock weather slices, used when no CWA key is configured.

The values are stable for a given (town, date, dataset) so tests and demos are
reproducible. Cadence mirrors the real datasets: F-D0047-093 => 3h slices for
2 days; F-D0047-091 => 12h slices for 7 days.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

from app.schemas.weather import TimeSlice, Town


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

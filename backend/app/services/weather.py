"""Weather normalization service.

Turns raw upstream time slices into per-day summaries. This is the "daily
summary" contract advertised by GET /api/forecast: the API never exposes raw
per-slot data, so the two datasets (3-hourly vs 12-hourly) are hidden behind a
uniform shape.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from app.schemas.weather import DailyForecast, HourlyForecast, TimeSlice


def _advice_hint(temp_high: float | None, temp_low: float | None, max_pop: int | None) -> str:
    if max_pop is not None and max_pop >= 70:
        return "降雨機率高,建議攜傘或準備室內備案。"
    if temp_high is not None and temp_high >= 33:
        return "高溫炎熱,注意防曬與補充水分。"
    if temp_low is not None and temp_low <= 12:
        return "氣溫偏低,出門記得保暖。"
    return "天氣大致穩定,適合安排戶外行程。"


def normalize_to_daily(slices: list[TimeSlice]) -> list[DailyForecast]:
    """Group slices by calendar date and summarize each day."""
    buckets: dict[str, list[TimeSlice]] = defaultdict(list)
    for s in slices:
        day = s.start[:10]  # YYYY-MM-DD prefix of ISO datetime
        if day:
            buckets[day].append(s)

    daily: list[DailyForecast] = []
    for day in sorted(buckets):
        day_slices = buckets[day]
        highs = [s.temp_high_c for s in day_slices if s.temp_high_c is not None]
        lows = [s.temp_low_c for s in day_slices if s.temp_low_c is not None]
        temps = [s.temp_c for s in day_slices if s.temp_c is not None]
        pops = [s.pop_percent for s in day_slices if s.pop_percent is not None]
        weathers = [s.weather for s in day_slices if s.weather]

        temp_high = max(highs) if highs else (max(temps) if temps else None)
        temp_low = min(lows) if lows else (min(temps) if temps else None)
        max_pop = max(pops) if pops else None
        # Representative weather = most frequent phenomenon that day.
        weather = Counter(weathers).most_common(1)[0][0] if weathers else None

        daily.append(
            DailyForecast(
                date=day,
                temp_high_c=temp_high,
                temp_low_c=temp_low,
                max_pop_percent=max_pop,
                weather=weather,
                advice_hint=_advice_hint(temp_high, temp_low, max_pop),
            )
        )
    return daily


def normalize_to_hourly(slices: list[TimeSlice]) -> list[HourlyForecast]:
    """Project normalized time slices into the 72h chart contract."""
    hourly: list[HourlyForecast] = []
    for slot in slices:
        if (
            slot.temp_c is None
            and slot.apparent_temp_c is None
            and slot.pop_percent is None
            and slot.weather is None
            and slot.weather_code is None
        ):
            continue
        hourly.append(
            HourlyForecast(
                time=slot.start,
                temp_c=slot.temp_c,
                apparent_temp_c=slot.apparent_temp_c,
                pop_percent=slot.pop_percent,
                weather=slot.weather,
                weather_code=slot.weather_code,
            )
        )
    return hourly


def should_include_hourly_chart(target: date, today: date | None = None) -> bool:
    """Only the next 72h window is eligible for the 3-hour chart."""
    delta = (target - (today or date.today())).days
    return 0 <= delta <= 2


def pick_target_day(days: list[DailyForecast], target_date: str) -> list[DailyForecast]:
    """Prefer the exact target date; fall back to the full horizon if absent."""
    exact = [d for d in days if d.date == target_date]
    return exact if exact else days

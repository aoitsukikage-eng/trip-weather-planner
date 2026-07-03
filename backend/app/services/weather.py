"""Weather normalization service.

Turns raw upstream time slices into per-day summaries. This is the "daily
summary" contract advertised by GET /api/forecast: the API never exposes raw
per-slot data, so the two datasets (3-hourly vs 12-hourly) are hidden behind a
uniform shape.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

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
    """Project upstream near-term slices into a uniform 3-hour chart contract."""
    buckets: dict[str, list[tuple[datetime, TimeSlice]]] = defaultdict(list)
    for slot in slices:
        start_at = _parse_iso_datetime(slot.start)
        if start_at is None:
            continue
        bucket_start = start_at.replace(
            hour=(start_at.hour // 3) * 3,
            minute=0,
            second=0,
            microsecond=0,
        )
        buckets[bucket_start.isoformat()].append((start_at, slot))

    hourly: list[HourlyForecast] = []
    for bucket_key in sorted(buckets):
        entries = sorted(buckets[bucket_key], key=lambda item: item[0])
        merged = _merge_hourly_bucket(bucket_key, entries)
        if merged is not None:
            hourly.append(merged)
    return hourly


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _merge_hourly_bucket(
    bucket_key: str, entries: list[tuple[datetime, TimeSlice]]
) -> HourlyForecast | None:
    first_slot = entries[0][1]
    temps = [slot.temp_c for _, slot in entries if slot.temp_c is not None]
    apparent_temps = [
        slot.apparent_temp_c for _, slot in entries if slot.apparent_temp_c is not None
    ]
    pops = [slot.pop_percent for _, slot in entries if slot.pop_percent is not None]
    weather_pairs = [
        (slot.weather or "", slot.weather_code)
        for _, slot in entries
        if slot.weather or slot.weather_code
    ]

    merged = HourlyForecast(
        time=bucket_key,
        temp_c=round(sum(temps) / len(temps), 1) if temps else None,
        apparent_temp_c=round(sum(apparent_temps) / len(apparent_temps), 1)
        if apparent_temps
        else None,
        pop_percent=max(pops) if pops else None,
        weather=None,
        weather_code=None,
    )

    if weather_pairs:
        ranked_weather = sorted(
            Counter(weather_pairs).items(),
            key=lambda item: (-item[1], weather_pairs.index(item[0])),
        )
        merged.weather, merged.weather_code = ranked_weather[0][0]

    if (
        merged.temp_c is None
        and merged.apparent_temp_c is None
        and merged.pop_percent is None
        and merged.weather is None
        and merged.weather_code is None
    ):
        return None

    bucket_start = _parse_iso_datetime(bucket_key)
    first_start = entries[0][0]
    if bucket_start is not None:
        expected_end = (bucket_start + timedelta(hours=3)).isoformat()
        first_end = _parse_iso_datetime(first_slot.end)
        if len(entries) == 1 and first_start == bucket_start and first_slot.end == expected_end:
            return HourlyForecast(
                time=first_slot.start,
                temp_c=first_slot.temp_c,
                apparent_temp_c=first_slot.apparent_temp_c,
                pop_percent=first_slot.pop_percent,
                weather=first_slot.weather,
                weather_code=first_slot.weather_code,
            )
        if len(entries) == 1 and first_end == bucket_start + timedelta(hours=3):
            merged.time = first_slot.start

    return merged


def should_include_hourly_chart(target: date, today: date | None = None) -> bool:
    """Only the next 72h window is eligible for the 3-hour chart."""
    delta = (target - (today or date.today())).days
    return 0 <= delta <= 2


def pick_target_day(days: list[DailyForecast], target_date: str) -> list[DailyForecast]:
    """Prefer the exact target date; fall back to the full horizon if absent."""
    exact = [d for d in days if d.date == target_date]
    return exact if exact else days

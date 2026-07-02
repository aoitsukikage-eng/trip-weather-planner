"""Domain schemas for weather forecasts.

These are the *normalized* shapes the API exposes. They are deliberately
decoupled from CWA's raw payload: swapping the upstream provider only touches
the adapter, not these schemas nor the frontend contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Town(BaseModel):
    """A selectable township/district."""

    code: str = Field(..., description="Stable identifier, e.g. 'taipei-zhongzheng'")
    name: str = Field(..., description="Township name, e.g. '中正區'")
    city: str = Field(..., description="Parent city/county, e.g. '臺北市'")
    lat: float
    lon: float


class TimeSlice(BaseModel):
    """Intermediate parsed slice from the upstream dataset (pre-normalization)."""

    start: str  # ISO datetime string
    end: str
    temp_c: float | None = None
    temp_high_c: float | None = None
    temp_low_c: float | None = None
    pop_percent: int | None = None  # probability of precipitation
    weather: str | None = None  # Wx phenomenon text


class DailyForecast(BaseModel):
    """One calendar day, summarized from many upstream time slices."""

    date: str  # YYYY-MM-DD
    temp_high_c: float | None = None
    temp_low_c: float | None = None
    max_pop_percent: int | None = None
    weather: str | None = None  # representative phenomenon for the day
    advice_hint: str | None = None  # short rule-based hint (rain/heat/cold)


class ForecastData(BaseModel):
    """Weather portion of GET /api/forecast."""

    town: Town
    target_date: str
    source_dataset: str  # which CWA dataset produced this (F-D0047-091 / -093 / mock)
    days: list[DailyForecast]
    generated_at: str


class AiSummary(BaseModel):
    text: str
    mode: str  # 'gemini' | 'rule-based' | 'rule-based-fallback'


class ForecastResult(BaseModel):
    """Full payload for GET /api/forecast: weather + AI trip summary."""

    forecast: ForecastData
    ai_summary: AiSummary

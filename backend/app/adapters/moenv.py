"""MOENV v2 air-quality adapter for aqx_p_432 and aqf_p_01."""

from __future__ import annotations

from datetime import date
from math import cos, radians, sqrt
from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.schemas.weather import AQIForecast, AQIInfo, Town

DATASET_CURRENT = "aqx_p_432"
DATASET_FORECAST = "aqf_p_01"
COUNTY_ZONES = {
    "臺北市": "北部",
    "新北市": "北部",
    "基隆市": "北部",
    "桃園市": "北部",
    "新竹市": "竹苗",
    "新竹縣": "竹苗",
    "苗栗縣": "竹苗",
    "臺中市": "中部",
    "彰化縣": "中部",
    "南投縣": "中部",
    "雲林縣": "雲嘉南",
    "嘉義市": "雲嘉南",
    "嘉義縣": "雲嘉南",
    "臺南市": "雲嘉南",
    "高雄市": "高屏",
    "屏東縣": "高屏",
    "宜蘭縣": "宜蘭",
    "花蓮縣": "花東",
    "臺東縣": "花東",
    "連江縣": "馬祖",
    "金門縣": "金門",
    "澎湖縣": "澎湖",
}


def aqi_level(value: int | None) -> str | None:
    if value is None:
        return None
    if value <= 50:
        return "良好"
    if value <= 100:
        return "普通"
    if value <= 150:
        return "對敏感族群不健康"
    if value <= 200:
        return "對所有族群不健康"
    if value <= 300:
        return "非常不健康"
    return "危害"


class MOENVAdapter:
    def __init__(self, settings: Settings, cache: TTLCache | None = None) -> None:
        self._settings, self._cache = settings, cache

    async def fetch_current(self, town: Town) -> AQIInfo | None:
        if self._settings.use_moenv_mock:
            return AQIInfo(
                value=42, level="良好", station_name="示範測站", source_label="目前空氣品質（示範）"
            )
        rows = await self._request(DATASET_CURRENT)
        nearest: tuple[float, dict[str, Any]] | None = None
        for row in rows:
            lat, lon, value = (
                _float(row.get("latitude")),
                _float(row.get("longitude")),
                _int(row.get("aqi")),
            )
            if lat is None or lon is None or value is None:
                continue
            distance = _distance(town.lat, town.lon, lat, lon)
            if nearest is None or distance < nearest[0]:
                nearest = (distance, row)
        if nearest is None:
            return None
        row = nearest[1]
        value = _int(row.get("aqi"))
        return AQIInfo(
            value=value,
            level=str(row.get("status") or aqi_level(value) or "資料不足"),
            station_name=str(row.get("sitename") or ""),
            observed_at=str(row.get("publishtime") or "") or None,
        )

    async def fetch_forecast(self, county: str) -> dict[str, AQIForecast]:
        zone = COUNTY_ZONES.get(county)
        if not zone:
            return {}
        if self._settings.use_moenv_mock:
            return {}
        rows = await self._request(DATASET_FORECAST)
        result = {}
        for row in rows:
            if str(row.get("area") or "").strip() != zone:
                continue
            raw_date = str(row.get("forecastdate") or "")[:10]
            value = _int(row.get("aqi"))
            try:
                day = date.fromisoformat(raw_date).isoformat()
            except ValueError:
                continue
            result[day] = AQIForecast(date=day, value=value, level=aqi_level(value))
        return result

    async def _request(self, dataset: str) -> list[dict[str, Any]]:
        key = f"moenv:{dataset}"
        cached = self._cache.get(key) if self._cache else None
        if cached is not None:
            return cached
        try:
            async with httpx.AsyncClient(timeout=self._settings.upstream_timeout_seconds) as client:
                response = await client.get(
                    f"{self._settings.moenv_base_url}/{dataset}",
                    params={"api_key": self._settings.moenv_api_key, "format": "JSON"},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("MOENV request failed.", error_code="moenv_upstream_error") from exc
        rows = _rows_from_payload(payload)
        if self._cache:
            self._cache.set(key, rows, ttl=1800)
        return rows


def _rows_from_payload(payload: object) -> list[dict[str, Any]]:
    """Accept MOENV's documented list response and its records wrapper variant."""
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = payload.get("records", [])
    else:
        candidates = []
    if not isinstance(candidates, list):
        return []
    return [row for row in candidates if isinstance(row, dict)]


def _float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _distance(a: float, b: float, c: float, d: float) -> float:
    return sqrt(((a - c) * 111) ** 2 + ((b - d) * 111 * cos(radians((a + c) / 2))) ** 2)

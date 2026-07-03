"""CWA (Central Weather Administration) adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import cos, radians, sqrt
from typing import Any

import httpx

from app.adapters.mock_data import mock_sunrise_sunset, mock_time_slices, mock_uv_info
from app.core.cache import TTLCache
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.schemas.weather import SunriseSunset, TimeSlice, Town, UVInfo

DATASET_NEAR = "F-D0047-093"
DATASET_WEEK = "F-D0047-091"
DATASET_SUNRISE = "A-B0062-001"
DATASET_UV = "O-A0005-001"
DATASET_STATIONS = "O-A0001-001"

TOWNS_CACHE_KEY = "cwa:towns"
SUNRISE_CACHE_KEY = "cwa:sunrise"
UV_CACHE_KEY = "cwa:uv"
STATION_CACHE_KEY = "cwa:stations"
TOWNS_CACHE_TTL = 86400
AUXILIARY_CACHE_TTL = 3600

_NEAR_DATASETS_BY_CITY: dict[str, str] = {
    "宜蘭縣": "F-D0047-001",
    "桃園市": "F-D0047-005",
    "新竹縣": "F-D0047-009",
    "苗栗縣": "F-D0047-013",
    "彰化縣": "F-D0047-017",
    "南投縣": "F-D0047-021",
    "雲林縣": "F-D0047-025",
    "嘉義縣": "F-D0047-029",
    "屏東縣": "F-D0047-033",
    "臺東縣": "F-D0047-037",
    "花蓮縣": "F-D0047-041",
    "澎湖縣": "F-D0047-045",
    "基隆市": "F-D0047-049",
    "新竹市": "F-D0047-053",
    "嘉義市": "F-D0047-057",
    "臺北市": "F-D0047-061",
    "高雄市": "F-D0047-065",
    "新北市": "F-D0047-069",
    "臺中市": "F-D0047-073",
    "臺南市": "F-D0047-077",
    "連江縣": "F-D0047-081",
    "金門縣": "F-D0047-085",
}
_WEEK_DATASETS_BY_CITY: dict[str, str] = {
    "宜蘭縣": "F-D0047-003",
    "桃園市": "F-D0047-007",
    "新竹縣": "F-D0047-011",
    "苗栗縣": "F-D0047-015",
    "彰化縣": "F-D0047-019",
    "南投縣": "F-D0047-023",
    "雲林縣": "F-D0047-027",
    "嘉義縣": "F-D0047-031",
    "屏東縣": "F-D0047-035",
    "臺東縣": "F-D0047-039",
    "花蓮縣": "F-D0047-043",
    "澎湖縣": "F-D0047-047",
    "基隆市": "F-D0047-051",
    "新竹市": "F-D0047-055",
    "嘉義市": "F-D0047-059",
    "臺北市": "F-D0047-063",
    "高雄市": "F-D0047-067",
    "新北市": "F-D0047-071",
    "臺中市": "F-D0047-075",
    "臺南市": "F-D0047-079",
    "連江縣": "F-D0047-083",
    "金門縣": "F-D0047-087",
}
_AGGREGATE_DATASETS = {
    DATASET_NEAR: "F-D0047-089",
    DATASET_WEEK: "F-D0047-091",
}


def select_dataset(target_date: date, today: date | None = None) -> str:
    today = today or date.today()
    delta_days = (target_date - today).days
    return DATASET_NEAR if delta_days <= 2 else DATASET_WEEK


def resolve_live_dataset(logical_dataset: str, town: Town) -> str:
    if logical_dataset == DATASET_NEAR:
        return _NEAR_DATASETS_BY_CITY.get(town.city, _AGGREGATE_DATASETS[logical_dataset])
    if logical_dataset == DATASET_WEEK:
        return _WEEK_DATASETS_BY_CITY.get(town.city, _AGGREGATE_DATASETS[logical_dataset])
    raise UpstreamError(
        f"Unsupported logical dataset: {logical_dataset}",
        error_code="unsupported_dataset",
    )


@dataclass(frozen=True)
class ResolvedDataset:
    logical_dataset: str
    transport_dataset: str

    @property
    def source_label(self) -> str:
        if self.logical_dataset == self.transport_dataset:
            return self.logical_dataset
        return f"{self.logical_dataset} via {self.transport_dataset}"


@dataclass(frozen=True)
class UVStation:
    station_id: str
    station_name: str
    lat: float
    lon: float


class CWAAdapter:
    def __init__(self, settings: Settings, cache: TTLCache | None = None) -> None:
        self._settings = settings
        self._cache = cache

    async def fetch_time_slices(self, town: Town, target_date: date) -> tuple[list[TimeSlice], str]:
        logical_dataset = select_dataset(target_date)
        if self._settings.use_mock:
            return mock_time_slices(logical_dataset, town), f"mock:{logical_dataset}"

        resolved = ResolvedDataset(
            logical_dataset=logical_dataset,
            transport_dataset=resolve_live_dataset(logical_dataset, town),
        )
        payload = await self._request_json(
            resolved.transport_dataset,
            params={"LocationName": town.name},
        )
        slices = self._parse_forecast_payload(payload, town)
        if not slices:
            raise UpstreamError(
                f"CWA payload contained no forecast rows for {town.name}.",
                error_code="empty_forecast",
            )
        return slices, resolved.source_label

    async def fetch_all_towns(self) -> list[Town]:
        if self._settings.use_mock:
            raise UpstreamError(
                "Mock mode does not provide live town catalog.",
                error_code="mock_mode",
            )

        cached = self._cache_get(TOWNS_CACHE_KEY)
        if cached is not None:
            return cached

        towns: list[Town] = []
        seen_codes: set[str] = set()
        for dataset in _WEEK_DATASETS_BY_CITY.values():
            payload = await self._request_json(dataset)
            for town in self._parse_town_payload(payload):
                if town.code in seen_codes:
                    continue
                seen_codes.add(town.code)
                towns.append(town)

        towns.sort(key=lambda item: (item.city, item.name, item.code))
        if len(towns) < 300:
            raise UpstreamError(
                f"Live town catalog was unexpectedly small: {len(towns)} entries.",
                error_code="town_catalog_incomplete",
            )
        self._cache_set(TOWNS_CACHE_KEY, towns, TOWNS_CACHE_TTL)
        return towns

    async def fetch_sunrise_sunset(self, town: Town, target_date: date) -> SunriseSunset:
        if self._settings.use_mock:
            return mock_sunrise_sunset(town, target_date)

        payload = await self._request_json(
            DATASET_SUNRISE,
            cache_key=SUNRISE_CACHE_KEY,
            ttl=AUXILIARY_CACHE_TTL,
        )
        result = self._parse_sunrise_payload(payload, town.city, target_date)
        if result is None:
            raise UpstreamError(
                f"No sunrise/sunset data for {town.city} on {target_date.isoformat()}.",
                error_code="sunrise_not_found",
            )
        return result

    async def fetch_uv_info(self, town: Town) -> UVInfo:
        if self._settings.use_mock:
            return mock_uv_info(town, date.today())

        uv_payload = await self._request_json(
            DATASET_UV,
            cache_key=UV_CACHE_KEY,
            ttl=AUXILIARY_CACHE_TTL,
        )
        station_payload = await self._request_json(
            DATASET_STATIONS,
            cache_key=STATION_CACHE_KEY,
            ttl=TOWNS_CACHE_TTL,
        )
        result = self._parse_uv_payload(uv_payload, station_payload, town)
        if result is None:
            raise UpstreamError(
                f"No UV observation could be resolved for {town.name}.",
                error_code="uv_not_found",
            )
        return result

    async def _request_json(
        self,
        dataset: str,
        *,
        params: dict[str, str] | None = None,
        cache_key: str | None = None,
        ttl: int | None = None,
    ) -> dict[str, Any]:
        effective_cache_key = cache_key or self._build_cache_key(dataset, params)
        cached = self._cache_get(effective_cache_key)
        if cached is not None:
            return cached

        request_params = {
            "Authorization": self._settings.cwa_api_key,
            "format": "JSON",
        }
        if params:
            request_params.update(params)

        url = f"{self._settings.cwa_base_url}/{dataset}"
        try:
            async with httpx.AsyncClient(timeout=self._settings.upstream_timeout_seconds) as client:
                resp = await client.get(url, params=request_params)
                resp.raise_for_status()
                payload = resp.json()
        except httpx.TimeoutException as exc:
            raise UpstreamError("CWA request timed out.", error_code="upstream_timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise UpstreamError(
                f"CWA request failed: HTTP {exc.response.status_code}",
                error_code="upstream_http_error",
            ) from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(
                f"CWA request failed: {exc}",
                error_code="upstream_http_error",
            ) from exc
        except ValueError as exc:
            raise UpstreamError(
                "CWA returned invalid JSON.",
                error_code="upstream_invalid_json",
            ) from exc

        self._cache_set(effective_cache_key, payload, ttl)
        return payload

    @staticmethod
    def _parse_forecast_payload(payload: dict[str, Any], town: Town) -> list[TimeSlice]:
        locations = []
        records = payload.get("records")
        if isinstance(records, dict):
            raw_locations = records.get("Locations")
            if isinstance(raw_locations, list) and raw_locations:
                first_group = raw_locations[0]
                if isinstance(first_group, dict):
                    candidate_locations = first_group.get("Location")
                    if isinstance(candidate_locations, list):
                        locations = candidate_locations

        location = next(
            (
                loc
                for loc in locations
                if isinstance(loc, dict) and loc.get("LocationName") == town.name
            ),
            locations[0] if locations else None,
        )
        if not isinstance(location, dict):
            return []

        by_time: dict[str, TimeSlice] = {}
        for element in _as_list(location.get("WeatherElement")):
            if not isinstance(element, dict):
                continue
            name = str(element.get("ElementName", ""))
            for row in _as_list(element.get("Time")):
                if not isinstance(row, dict):
                    continue
                start = str(row.get("StartTime") or row.get("DataTime") or "")
                end = str(row.get("EndTime") or start)
                if not start:
                    continue
                slot = by_time.setdefault(start, TimeSlice(start=start, end=end))
                slot.end = end
                _apply_element(slot, name, _extract_element_values(row.get("ElementValue")))
        return [by_time[key] for key in sorted(by_time)]

    @staticmethod
    def _parse_town_payload(payload: dict[str, Any]) -> list[Town]:
        towns: list[Town] = []
        records = payload.get("records")
        if not isinstance(records, dict):
            return towns
        for group in _as_list(records.get("Locations")):
            if not isinstance(group, dict):
                continue
            city = str(group.get("LocationsName") or "").strip()
            for location in _as_list(group.get("Location")):
                if not isinstance(location, dict):
                    continue
                name = str(location.get("LocationName") or "").strip()
                geocode = str(location.get("Geocode") or "").strip()
                lat = _safe_float(location.get("Latitude"))
                lon = _safe_float(location.get("Longitude"))
                if not city or not name or not geocode or lat is None or lon is None:
                    continue
                towns.append(
                    Town(
                        code=f"cwa-{geocode}",
                        name=name,
                        city=city,
                        lat=lat,
                        lon=lon,
                    )
                )
        return towns

    @staticmethod
    def _parse_sunrise_payload(
        payload: dict[str, Any],
        county: str,
        target_date: date,
    ) -> SunriseSunset | None:
        records = payload.get("records")
        if not isinstance(records, dict):
            return None
        locations = records.get("locations")
        if not isinstance(locations, dict):
            return None
        target_iso = target_date.isoformat()
        target_month_day = target_iso[5:]
        for location in _as_list(locations.get("location")):
            if not isinstance(location, dict):
                continue
            if str(location.get("CountyName") or "").strip() != county:
                continue
            rows = [row for row in _as_list(location.get("time")) if isinstance(row, dict)]
            exact = next((row for row in rows if row.get("Date") == target_iso), None)
            approx = next(
                (row for row in rows if str(row.get("Date") or "")[5:] == target_month_day),
                None,
            )
            chosen = exact or approx or (rows[-1] if rows else None)
            if chosen is None:
                return None
            source_date = str(chosen.get("Date") or target_iso)
            return SunriseSunset(
                county=county,
                target_date=target_iso,
                source_date=source_date,
                sunrise_time=_clean_clock(chosen.get("SunRiseTime")),
                sunset_time=_clean_clock(chosen.get("SunSetTime")),
                is_approximate=source_date != target_iso,
            )
        return None

    @staticmethod
    def _parse_uv_payload(
        uv_payload: dict[str, Any],
        station_payload: dict[str, Any],
        town: Town,
    ) -> UVInfo | None:
        values, observed_at = _parse_uv_values(uv_payload)
        stations = _parse_station_metadata(station_payload)
        nearest: tuple[float, str, float, UVStation] | None = None
        for station_id, value in values.items():
            station = stations.get(station_id)
            if station is None:
                continue
            distance = _distance_km(town.lat, town.lon, station.lat, station.lon)
            candidate = (distance, station_id, value, station)
            if nearest is None or candidate < nearest:
                nearest = candidate
        if nearest is None:
            return None

        _, station_id, value, station = nearest
        return UVInfo(
            value=value,
            level=_uv_level(value),
            source_label="目前紫外線",
            source_type="observation",
            observed_at=observed_at,
            station_id=station_id,
            station_name=station.station_name,
        )

    def _cache_get(self, key: str) -> Any | None:
        if self._cache is None:
            return None
        return self._cache.get(key)

    def _cache_set(self, key: str, value: Any, ttl: int | None) -> None:
        if self._cache is None:
            return
        self._cache.set(key, value, ttl=ttl)

    @staticmethod
    def _build_cache_key(dataset: str, params: dict[str, str] | None) -> str:
        if not params:
            return f"cwa:{dataset}"
        suffix = ",".join(f"{key}={params[key]}" for key in sorted(params))
        return f"cwa:{dataset}:{suffix}"


def _extract_element_values(element_value: object) -> dict[str, str]:
    values: dict[str, str] = {}
    if not isinstance(element_value, list):
        return values
    for item in element_value:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if value in ("", None):
                continue
            text = str(value).strip()
            if text:
                values[str(key)] = text
    return values


def _pick_value(values: dict[str, str], *preferred_keys: str) -> str | None:
    for key in preferred_keys:
        value = values.get(key)
        if value:
            return value
    for value in values.values():
        if value:
            return value
    return None


def _apply_element(slot: TimeSlice, name: str, values: dict[str, str]) -> None:
    if not values:
        return

    value = _pick_value(values, name)
    weather_value = _pick_value(values, "Weather", "Wx", "天氣現象", "Value")
    weather_code = _pick_value(
        values,
        "WeatherCode",
        "WxCode",
        "天氣代碼",
        "weatherCode",
        "weather_code",
    )

    try:
        if name in {"溫度", "平均溫度", "T", "Temperature"}:
            slot.temp_c = float(value)
        elif name in {"體感溫度", "AT", "ApparentTemperature", "Apparent Temperature"}:
            slot.apparent_temp_c = float(value)
        elif name in {"最高溫度", "MaxT", "MaxTemperature"}:
            slot.temp_high_c = float(value)
        elif name in {"最低溫度", "MinT", "MinTemperature"}:
            slot.temp_low_c = float(value)
        elif "降雨機率" in name or "PoP" in name:
            slot.pop_percent = int(float(value))
        elif name in {"天氣現象", "Wx", "Weather"}:
            slot.weather = str(weather_value or value)
            slot.weather_code = weather_code or slot.weather_code
    except (ValueError, TypeError):
        pass

    if (
        slot.weather is None
        and weather_value
        and name not in {"溫度", "平均溫度", "T", "Temperature"}
    ):
        if name in {"天氣現象", "Wx", "Weather"}:
            slot.weather = weather_value
    if slot.weather_code is None and weather_code:
        slot.weather_code = weather_code


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_clock(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_uv_values(payload: dict[str, Any]) -> tuple[dict[str, float], str | None]:
    values: dict[str, float] = {}
    observed_at: str | None = None
    records = payload.get("records")
    if not isinstance(records, dict):
        return values, observed_at
    weather_element = records.get("weatherElement")
    if not isinstance(weather_element, dict):
        return values, observed_at
    observed_at = str(weather_element.get("Date") or "").strip() or None
    for location in _as_list(weather_element.get("location")):
        if not isinstance(location, dict):
            continue
        station_id = str(location.get("StationID") or "").strip()
        value = _safe_float(location.get("UVIndex"))
        if not station_id or value is None:
            continue
        values[station_id] = value
    return values, observed_at


def _parse_station_metadata(payload: dict[str, Any]) -> dict[str, UVStation]:
    stations: dict[str, UVStation] = {}
    records = payload.get("records")
    if not isinstance(records, dict):
        return stations
    for station in _as_list(records.get("Station")):
        if not isinstance(station, dict):
            continue
        station_id = str(station.get("StationId") or "").strip()
        station_name = str(station.get("StationName") or "").strip()
        geo_info = station.get("GeoInfo")
        if not isinstance(geo_info, dict):
            continue
        lat, lon = _extract_wgs84_coordinates(geo_info.get("Coordinates"))
        if not station_id or not station_name or lat is None or lon is None:
            continue
        stations[station_id] = UVStation(
            station_id=station_id,
            station_name=station_name,
            lat=lat,
            lon=lon,
        )
    return stations


def _extract_wgs84_coordinates(coordinates: object) -> tuple[float | None, float | None]:
    for coordinate in _as_list(coordinates):
        if not isinstance(coordinate, dict):
            continue
        if coordinate.get("CoordinateName") != "WGS84":
            continue
        lat = _safe_float(coordinate.get("StationLatitude"))
        lon = _safe_float(coordinate.get("StationLongitude"))
        return lat, lon
    return None, None


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat_scale = 111.0
    lon_scale = 111.0 * cos(radians((lat1 + lat2) / 2))
    return sqrt(((lat1 - lat2) * lat_scale) ** 2 + ((lon1 - lon2) * lon_scale) ** 2)


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

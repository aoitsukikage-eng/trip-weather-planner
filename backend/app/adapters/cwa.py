"""CWA (Central Weather Administration) adapter.

Responsibility: turn an upstream dataset into a provider-agnostic list of
`TimeSlice`. Everything downstream (normalization, API, frontend) is decoupled
from CWA's payload shape, so swapping providers only touches this file.

Logical dataset selection rule (matches the task card):
  - target date within 48h  -> F-D0047-093 family (3-hourly, near-term)
  - target date beyond 48h   -> F-D0047-091 family (12-hourly, 7-day)

Live transport note:
  - On 2026-07-02, the official `F-D0047-093` API returned HTTP 404.
  - CWA currently serves the same near-term township data via per-city datasets
    such as `F-D0047-061` (Taipei), while `F-D0047-091` remains live as the
    aggregate weekly dataset family.

When no CWA key is configured, `fetch_time_slices` returns deterministic mock
slices so the app is fully runnable without credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx

from app.adapters.mock_data import mock_time_slices
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.schemas.weather import TimeSlice, Town

DATASET_NEAR = "F-D0047-093"  # logical 2-day/3-hour family
DATASET_WEEK = "F-D0047-091"  # logical 7-day/12-hour family

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


class CWAAdapter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_time_slices(self, town: Town, target_date: date) -> tuple[list[TimeSlice], str]:
        """Return (slices, source_dataset_label)."""
        logical_dataset = select_dataset(target_date)
        if self._settings.use_mock:
            return mock_time_slices(logical_dataset, town), f"mock:{logical_dataset}"

        resolved = ResolvedDataset(
            logical_dataset=logical_dataset,
            transport_dataset=resolve_live_dataset(logical_dataset, town),
        )
        slices = await self._fetch_live(resolved, town)
        return slices, resolved.source_label

    async def _fetch_live(self, resolved: ResolvedDataset, town: Town) -> list[TimeSlice]:
        url = f"{self._settings.cwa_base_url}/{resolved.transport_dataset}"
        params = {
            "Authorization": self._settings.cwa_api_key,
            "LocationName": town.name,
            "format": "JSON",
        }
        try:
            async with httpx.AsyncClient(timeout=self._settings.upstream_timeout_seconds) as client:
                resp = await client.get(url, params=params)
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

        slices = self._parse_payload(payload, town)
        if not slices:
            raise UpstreamError(
                f"CWA payload contained no forecast rows for {town.name}.",
                error_code="empty_forecast",
            )
        return slices

    @staticmethod
    def _parse_payload(payload: dict, town: Town) -> list[TimeSlice]:
        """Parse CWA F-D0047 JSON into TimeSlice objects."""
        try:
            locations = payload["records"]["Locations"][0]["Location"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamError("Unexpected CWA payload shape.") from exc

        location = next(
            (loc for loc in locations if loc.get("LocationName") == town.name),
            locations[0] if locations else None,
        )
        if location is None:
            return []

        by_time: dict[str, TimeSlice] = {}
        for element in location.get("WeatherElement", []):
            name = str(element.get("ElementName", ""))
            for t in element.get("Time", []):
                start = str(t.get("StartTime") or t.get("DataTime") or "")
                end = str(t.get("EndTime") or start)
                if not start:
                    continue
                slot = by_time.setdefault(start, TimeSlice(start=start, end=end))
                slot.end = end
                _apply_element(slot, name, _first_value(t.get("ElementValue")))
        return [by_time[k] for k in sorted(by_time)]


def _first_value(element_value: object) -> str | None:
    if isinstance(element_value, list) and element_value:
        first = element_value[0]
        if isinstance(first, dict):
            for value in first.values():
                if value not in ("", None):
                    return str(value)
    return None


def _apply_element(slot: TimeSlice, name: str, value: str | None) -> None:
    if value is None:
        return

    try:
        if name in {"溫度", "平均溫度", "T", "Temperature"}:
            slot.temp_c = float(value)
        elif name in {"最高溫度", "MaxT", "MaxTemperature"}:
            slot.temp_high_c = float(value)
        elif name in {"最低溫度", "MinT", "MinTemperature"}:
            slot.temp_low_c = float(value)
        elif "降雨機率" in name or "PoP" in name:
            slot.pop_percent = int(float(value))
        elif name in {"天氣現象", "Wx", "Weather"}:
            slot.weather = str(value)
    except (ValueError, TypeError):
        # Ignore malformed individual fields rather than failing the whole parse.
        return

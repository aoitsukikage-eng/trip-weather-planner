"""CWA (Central Weather Administration) adapter.

Responsibility: turn an upstream dataset into a provider-agnostic list of
`TimeSlice`. Everything downstream (normalization, API, frontend) is decoupled
from CWA's payload shape, so swapping providers only touches this file.

Dataset selection rule (matches the master plan §8):
  - target date within 48h  -> F-D0047-093 (3-hourly, 2-day)
  - target date beyond 48h   -> F-D0047-091 (12-hourly, 7-day)

When no CWA key is configured, `fetch_time_slices` returns deterministic mock
slices so the app is fully runnable without credentials.
"""

from __future__ import annotations

from datetime import date

import httpx

from app.adapters.mock_data import mock_time_slices
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.schemas.weather import TimeSlice, Town

DATASET_NEAR = "F-D0047-093"  # 2-day, 3-hourly
DATASET_WEEK = "F-D0047-091"  # 7-day, 12-hourly


def select_dataset(target_date: date, today: date | None = None) -> str:
    today = today or date.today()
    delta_days = (target_date - today).days
    return DATASET_NEAR if delta_days <= 2 else DATASET_WEEK


class CWAAdapter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_time_slices(self, town: Town, target_date: date) -> tuple[list[TimeSlice], str]:
        """Return (slices, source_dataset_label)."""
        dataset = select_dataset(target_date)
        if self._settings.use_mock:
            return mock_time_slices(dataset, town), f"mock:{dataset}"
        slices = await self._fetch_live(dataset, town)
        return slices, dataset

    async def _fetch_live(self, dataset: str, town: Town) -> list[TimeSlice]:
        url = f"{self._settings.cwa_base_url}/{dataset}"
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
        except httpx.HTTPError as exc:
            raise UpstreamError(f"CWA request failed: {exc}") from exc
        return self._parse_payload(payload, town)

    @staticmethod
    def _parse_payload(payload: dict, town: Town) -> list[TimeSlice]:
        """Parse CWA F-D0047 JSON into TimeSlice objects.

        NOTE: validated against the live schema once the CWA key is available
        (see master plan §19 Step 1). CWA nests as:
        records -> Locations[0] -> Location[] -> WeatherElement[] -> Time[].
        Different elements (T, PoP12h, Wx) are separate arrays keyed by time, so
        we index by start-time and merge.
        """
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
            name = element.get("ElementName", "")
            for t in element.get("Time", []):
                start = t.get("StartTime") or t.get("DataTime") or ""
                end = t.get("EndTime", start)
                value = _first_value(t.get("ElementValue"))
                slot = by_time.setdefault(start, TimeSlice(start=start, end=end))
                _apply_element(slot, name, value)
        return [by_time[k] for k in sorted(by_time)]


def _first_value(element_value):
    if isinstance(element_value, list) and element_value:
        first = element_value[0]
        if isinstance(first, dict):
            # Take the first value field regardless of its key name.
            return next(iter(first.values()), None)
    return None


def _apply_element(slot: TimeSlice, name: str, value) -> None:
    if value is None:
        return
    lowered = name.lower()
    try:
        if lowered in ("溫度", "t", "temperature"):
            slot.temp_c = float(value)
        elif "pop" in lowered or "降雨機率" in name:
            slot.pop_percent = int(float(value))
        elif lowered in ("wx", "天氣現象", "天氣預報綜合描述"):
            slot.weather = str(value)
    except (ValueError, TypeError):
        # Ignore malformed individual fields rather than failing the whole parse.
        return

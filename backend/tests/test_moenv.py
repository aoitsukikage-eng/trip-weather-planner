"""MOENV adapter tests using fixtures only; no live requests are permitted."""

from __future__ import annotations

import asyncio

import pytest

from app.adapters.moenv import (
    COUNTY_ZONES,
    DATASET_CURRENT,
    DATASET_FORECAST,
    MOENVAdapter,
    _rows_from_payload,
)
from app.core.config import Settings
from app.data.towns import get_town

CURRENT_LIST_FIXTURE = [
    {"sitename": "遠方測站", "latitude": "24.0", "longitude": "120.0", "aqi": "80"},
    {
        "sitename": "最近測站",
        "latitude": "25.032",
        "longitude": "121.565",
        "aqi": "42",
        "status": "良好",
        "publishtime": "2026-07-15 12:00",
    },
]
FORECAST_LIST_FIXTURE = [
    {"area": "北部", "forecastdate": "2026-07-16", "aqi": "51"},
    {"area": "中部", "forecastdate": "2026-07-16", "aqi": "90"},
]


def _adapter() -> MOENVAdapter:
    return MOENVAdapter(Settings(cwa_api_key="test", moenv_api_key="test"))


def test_rows_accept_live_top_level_list_and_records_wrapper():
    assert _rows_from_payload(CURRENT_LIST_FIXTURE) == CURRENT_LIST_FIXTURE
    assert _rows_from_payload({"records": CURRENT_LIST_FIXTURE}) == CURRENT_LIST_FIXTURE
    assert _rows_from_payload({"records": "not-a-list"}) == []


def test_current_aqi_uses_nearest_station_from_list_fixture(monkeypatch: pytest.MonkeyPatch):
    town = get_town("taipei-xinyi")
    assert town is not None

    async def fake_request(dataset: str):
        assert dataset == DATASET_CURRENT
        return CURRENT_LIST_FIXTURE

    adapter = _adapter()
    monkeypatch.setattr(adapter, "_request", fake_request)

    aqi = asyncio.run(adapter.fetch_current(town))

    assert aqi is not None
    assert aqi.station_name == "最近測站"
    assert aqi.value == 42
    assert aqi.level == "良好"


def test_county_zone_mapping_attaches_forecast_by_date(monkeypatch: pytest.MonkeyPatch):
    async def fake_request(dataset: str):
        assert dataset == DATASET_FORECAST
        return FORECAST_LIST_FIXTURE

    adapter = _adapter()
    monkeypatch.setattr(adapter, "_request", fake_request)

    taipei = asyncio.run(adapter.fetch_forecast("臺北市"))
    taichung = asyncio.run(adapter.fetch_forecast("臺中市"))

    assert COUNTY_ZONES["臺北市"] == "北部"
    assert taipei["2026-07-16"].value == 51
    assert taichung["2026-07-16"].value == 90

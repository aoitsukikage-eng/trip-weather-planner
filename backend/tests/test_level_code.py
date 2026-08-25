"""Unit tests for level_code threshold boundaries and MOENV status string isolation."""

from __future__ import annotations

import asyncio

import pytest

from app.adapters.moenv import MOENVAdapter
from app.core.config import Settings
from app.i18n.weather_text import get_aqi_level_code, get_uv_level_code
from app.schemas.weather import AQIForecast, AQIInfo, Town, UVInfo


def test_uv_level_code_threshold_boundaries():
    assert get_uv_level_code(None) is None
    assert get_uv_level_code(0) == "low"
    assert get_uv_level_code(2.0) == "low"
    assert get_uv_level_code(2.1) == "moderate"
    assert get_uv_level_code(5.0) == "moderate"
    assert get_uv_level_code(5.1) == "high"
    assert get_uv_level_code(7.0) == "high"
    assert get_uv_level_code(7.1) == "very_high"
    assert get_uv_level_code(10.0) == "very_high"
    assert get_uv_level_code(10.1) == "extreme"
    assert get_uv_level_code(15.0) == "extreme"

    # Schema instantiation test
    uv_none = UVInfo(source_label="UV", source_type="obs")
    assert uv_none.level_code is None

    uv_extreme = UVInfo(
        value=11.0,
        level_code=get_uv_level_code(11.0),
        source_label="UV",
        source_type="obs",
    )
    assert uv_extreme.level_code == "extreme"


def test_aqi_level_code_threshold_boundaries():
    assert get_aqi_level_code(None) is None
    assert get_aqi_level_code(0) == "good"
    assert get_aqi_level_code(50) == "good"
    assert get_aqi_level_code(51) == "moderate"
    assert get_aqi_level_code(100) == "moderate"
    assert get_aqi_level_code(101) == "unhealthy_sensitive"
    assert get_aqi_level_code(150) == "unhealthy_sensitive"
    assert get_aqi_level_code(151) == "unhealthy"
    assert get_aqi_level_code(200) == "unhealthy"
    assert get_aqi_level_code(201) == "very_unhealthy"
    assert get_aqi_level_code(300) == "very_unhealthy"
    assert get_aqi_level_code(301) == "hazardous"
    assert get_aqi_level_code(500) == "hazardous"

    # Schema instantiation tests
    aqi_info_none = AQIInfo()
    assert aqi_info_none.level_code is None

    aqi_fc_none = AQIForecast(date="2026-08-23")
    assert aqi_fc_none.level_code is None


def test_moenv_unrecognised_status_string_yields_numeric_level_code(
    monkeypatch: pytest.MonkeyPatch,
):
    adapter = MOENVAdapter(Settings(moenv_api_key="demo-key"))
    town = Town(
        code="taipei-xinyi",
        name="信義區",
        city="臺北市",
        lat=25.03,
        lon=121.57,
    )

    async def fake_request(dataset: str):
        return [
            {
                "sitename": "TestStation",
                "latitude": "25.03",
                "longitude": "121.57",
                "aqi": "350",
                "status": "特殊緊急防護警報（非標準字串）",
                "publishtime": "2026-08-23 12:00",
            }
        ]

    monkeypatch.setattr(adapter, "_request", fake_request)
    info = asyncio.run(adapter.fetch_current(town))

    assert info is not None
    assert info.value == 350
    assert info.level_code == "hazardous"

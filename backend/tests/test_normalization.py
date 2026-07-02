"""Unit tests for dataset routing, payload parsing, and normalization."""

from __future__ import annotations

import asyncio
from datetime import date

import httpx
import pytest

from app.adapters.cwa import (
    DATASET_NEAR,
    DATASET_WEEK,
    CWAAdapter,
    resolve_live_dataset,
    select_dataset,
)
from app.adapters.mock_data import mock_time_slices
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.data.towns import get_town
from app.schemas.weather import TimeSlice
from app.services.weather import normalize_to_daily, pick_target_day


def _near_payload() -> dict:
    return {
        "success": "true",
        "records": {
            "Locations": [
                {
                    "LocationsName": "臺北市",
                    "Location": [
                        {
                            "LocationName": "中正區",
                            "WeatherElement": [
                                {
                                    "ElementName": "溫度",
                                    "Time": [
                                        {
                                            "DataTime": "2026-07-02T06:00:00+08:00",
                                            "ElementValue": [{"Temperature": "31"}],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [{"Temperature": "33"}],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "3小時降雨機率",
                                    "Time": [
                                        {
                                            "DataTime": "2026-07-02T06:00:00+08:00",
                                            "ElementValue": [{"ProbabilityOfPrecipitation": "20"}],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [{"ProbabilityOfPrecipitation": "80"}],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "天氣現象",
                                    "Time": [
                                        {
                                            "DataTime": "2026-07-02T06:00:00+08:00",
                                            "ElementValue": [{"Weather": "多雲"}],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [{"Weather": "短暫陣雨"}],
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ]
        },
    }


def _week_payload() -> dict:
    return {
        "success": "true",
        "records": {
            "Locations": [
                {
                    "LocationsName": "花蓮縣",
                    "Location": [
                        {
                            "LocationName": "花蓮市",
                            "WeatherElement": [
                                {
                                    "ElementName": "最高溫度",
                                    "Time": [
                                        {
                                            "StartTime": "2026-07-05T06:00:00+08:00",
                                            "EndTime": "2026-07-05T18:00:00+08:00",
                                            "ElementValue": [{"MaxTemperature": "31"}],
                                        },
                                        {
                                            "StartTime": "2026-07-05T18:00:00+08:00",
                                            "EndTime": "2026-07-06T06:00:00+08:00",
                                            "ElementValue": [{"MaxTemperature": "29"}],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "最低溫度",
                                    "Time": [
                                        {
                                            "StartTime": "2026-07-05T06:00:00+08:00",
                                            "EndTime": "2026-07-05T18:00:00+08:00",
                                            "ElementValue": [{"MinTemperature": "25"}],
                                        },
                                        {
                                            "StartTime": "2026-07-05T18:00:00+08:00",
                                            "EndTime": "2026-07-06T06:00:00+08:00",
                                            "ElementValue": [{"MinTemperature": "24"}],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "12小時降雨機率",
                                    "Time": [
                                        {
                                            "StartTime": "2026-07-05T06:00:00+08:00",
                                            "EndTime": "2026-07-05T18:00:00+08:00",
                                            "ElementValue": [{"ProbabilityOfPrecipitation": "60"}],
                                        },
                                        {
                                            "StartTime": "2026-07-05T18:00:00+08:00",
                                            "EndTime": "2026-07-06T06:00:00+08:00",
                                            "ElementValue": [{"ProbabilityOfPrecipitation": "20"}],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "天氣現象",
                                    "Time": [
                                        {
                                            "StartTime": "2026-07-05T06:00:00+08:00",
                                            "EndTime": "2026-07-05T18:00:00+08:00",
                                            "ElementValue": [{"Weather": "多雲時晴"}],
                                        },
                                        {
                                            "StartTime": "2026-07-05T18:00:00+08:00",
                                            "EndTime": "2026-07-06T06:00:00+08:00",
                                            "ElementValue": [{"Weather": "多雲"}],
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ]
        },
    }


def test_select_dataset_near_vs_week():
    today = date(2026, 7, 1)
    assert select_dataset(date(2026, 7, 2), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 3), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 5), today=today) == DATASET_WEEK


def test_resolve_live_dataset_maps_city_specific_codes():
    assert resolve_live_dataset(DATASET_NEAR, get_town("taipei-zhongzheng")) == "F-D0047-061"
    assert resolve_live_dataset(DATASET_WEEK, get_town("hualien-hualien")) == "F-D0047-043"


def test_parse_near_payload_and_normalize():
    town = get_town("taipei-zhongzheng")
    slices = CWAAdapter._parse_payload(_near_payload(), town)
    assert len(slices) == 2
    days = normalize_to_daily(slices)
    assert len(days) == 1
    assert days[0].date == "2026-07-02"
    assert days[0].temp_high_c == 33.0
    assert days[0].temp_low_c == 31.0
    assert days[0].max_pop_percent == 80


def test_parse_week_payload_uses_max_min_temperatures():
    town = get_town("hualien-hualien")
    slices = CWAAdapter._parse_payload(_week_payload(), town)
    assert len(slices) == 2
    assert slices[0].temp_high_c == 31.0
    assert slices[1].temp_low_c == 24.0

    days = normalize_to_daily(slices)
    assert len(days) == 1
    assert days[0].temp_high_c == 31.0
    assert days[0].temp_low_c == 24.0
    assert days[0].max_pop_percent == 60


def test_parse_payload_rejects_unexpected_shape():
    town = get_town("taipei-zhongzheng")
    with pytest.raises(UpstreamError, match="Unexpected CWA payload shape"):
        CWAAdapter._parse_payload({"records": {}}, town)


def test_fetch_live_surfaces_timeout(monkeypatch: pytest.MonkeyPatch):
    town = get_town("taipei-zhongzheng")
    adapter = CWAAdapter(Settings(cwa_api_key="test-key"))

    async def fake_get(self, url, params):  # noqa: ARG001
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(UpstreamError, match="timed out"):
        asyncio.run(
            adapter._fetch_live(  # noqa: SLF001
                resolved=type(
                    "Resolved",
                    (),
                    {
                        "transport_dataset": "F-D0047-061",
                        "logical_dataset": DATASET_NEAR,
                    },
                )(),
                town=town,
            )
        )


def test_normalize_groups_by_day_and_summarizes():
    slices = [
        TimeSlice(
            start="2026-07-01T06:00:00",
            end="2026-07-01T18:00:00",
            temp_c=24.0,
            pop_percent=20,
            weather="多雲",
        ),
        TimeSlice(
            start="2026-07-01T18:00:00",
            end="2026-07-02T06:00:00",
            temp_c=30.0,
            pop_percent=80,
            weather="陰時多雲短暫雨",
        ),
        TimeSlice(
            start="2026-07-02T06:00:00",
            end="2026-07-02T18:00:00",
            temp_c=26.0,
            pop_percent=10,
            weather="晴時多雲",
        ),
    ]
    days = normalize_to_daily(slices)
    assert [d.date for d in days] == ["2026-07-01", "2026-07-02"]

    day1 = days[0]
    assert day1.temp_high_c == 30.0
    assert day1.temp_low_c == 24.0
    assert day1.max_pop_percent == 80
    assert "攜傘" in day1.advice_hint


def test_pick_target_day_prefers_exact():
    slices = mock_time_slices(
        DATASET_WEEK,
        get_town("hualien-hualien"),
        horizon_start=date(2026, 7, 1),
    )
    days = normalize_to_daily(slices)
    picked = pick_target_day(days, "2026-07-03")
    assert len(picked) == 1
    assert picked[0].date == "2026-07-03"


def test_mock_is_deterministic():
    town = get_town("taipei-zhongzheng")
    start = date(2026, 7, 1)
    a = mock_time_slices(DATASET_WEEK, town, horizon_start=start)
    b = mock_time_slices(DATASET_WEEK, town, horizon_start=start)
    assert [s.temp_c for s in a] == [s.temp_c for s in b]
    assert len(a) == 14

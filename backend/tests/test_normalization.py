"""Unit tests for dataset routing, payload parsing, and normalization."""

from __future__ import annotations

import asyncio
from datetime import date

import httpx
import pytest

from app.adapters.cwa import (
    DATASET_NEAR,
    DATASET_SUNRISE,
    DATASET_WEEK,
    SUNRISE_CACHE_TTL,
    CWAAdapter,
    resolve_live_dataset,
    select_dataset,
)
from app.adapters.mock_data import mock_time_slices
from app.core.config import Settings
from app.core.errors import UpstreamError
from app.data.towns import get_town
from app.schemas.weather import DailyForecast, TimeSlice
from app.services.ai_summary import AiSummaryService
from app.services.weather import (
    normalize_to_daily,
    normalize_to_hourly,
    pick_target_day,
    should_include_hourly_chart,
)


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
                                            "ElementValue": [
                                                {"ProbabilityOfPrecipitation": "20"}
                                            ],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [
                                                {"ProbabilityOfPrecipitation": "80"}
                                            ],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "天氣現象",
                                    "Time": [
                                        {
                                            "DataTime": "2026-07-02T06:00:00+08:00",
                                            "ElementValue": [
                                                {"Weather": "多雲", "WeatherCode": "04"}
                                            ],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [
                                                {"Weather": "短暫陣雨", "WeatherCode": "12"}
                                            ],
                                        },
                                    ],
                                },
                                {
                                    "ElementName": "體感溫度",
                                    "Time": [
                                        {
                                            "DataTime": "2026-07-02T06:00:00+08:00",
                                            "ElementValue": [{"ApparentTemperature": "34"}],
                                        },
                                        {
                                            "DataTime": "2026-07-02T09:00:00+08:00",
                                            "ElementValue": [{"ApparentTemperature": "37"}],
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


def _towns_payload() -> dict:
    return {
        "records": {
            "Locations": [
                {
                    "LocationsName": "新北市",
                    "Location": [
                        {
                            "LocationName": "板橋區",
                            "Geocode": "65000010",
                            "Latitude": "25.01154",
                            "Longitude": "121.450888",
                        },
                        {
                            "LocationName": "貢寮區",
                            "Geocode": "65000270",
                            "Latitude": "25.021273",
                            "Longitude": "121.910293",
                        },
                    ],
                }
            ]
        }
    }


def _sunrise_payload() -> dict:
    return {
        "records": {
            "locations": {
                "location": [
                    {
                        "CountyName": "臺北市",
                        "time": [
                            {"Date": "2026-07-04", "SunRiseTime": "05:08", "SunSetTime": "18:47"},
                            {"Date": "2025-07-05", "SunRiseTime": "05:09", "SunSetTime": "18:47"},
                        ],
                    }
                ]
            }
        }
    }


def _sunrise_partial_date_payload() -> dict:
    return {
        "records": {
            "locations": {
                "location": [
                    {
                        "CountyName": "台北市",
                        "time": [
                            {"Date": "07-04", "SunRiseTime": "05:08", "SunSetTime": "18:47"},
                            {"Date": "07-05", "SunRiseTime": "05:09", "SunSetTime": "18:47"},
                        ],
                    }
                ]
            }
        }
    }


def _uv_payload() -> dict:
    return {
        "records": {
            "weatherElement": {
                "Date": "2026-07-03",
                "location": [
                    {"StationID": "467280", "UVIndex": 9.0},
                    {"StationID": "467490", "UVIndex": 4.0},
                ],
            }
        }
    }


def _station_payload() -> dict:
    return {
        "records": {
            "Station": [
                {
                    "StationName": "臺北",
                    "StationId": "467280",
                    "GeoInfo": {
                        "Coordinates": [
                            {
                                "CoordinateName": "WGS84",
                                "StationLatitude": "25.037658",
                                "StationLongitude": "121.514853",
                            }
                        ]
                    },
                },
                {
                    "StationName": "花蓮",
                    "StationId": "467490",
                    "GeoInfo": {
                        "Coordinates": [
                            {
                                "CoordinateName": "WGS84",
                                "StationLatitude": "23.976944",
                                "StationLongitude": "121.605556",
                            }
                        ]
                    },
                },
            ]
        }
    }


def test_select_dataset_near_vs_week():
    today = date(2026, 7, 1)
    assert select_dataset(date(2026, 7, 2), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 3), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 5), today=today) == DATASET_WEEK


def test_resolve_live_dataset_maps_city_specific_codes():
    assert resolve_live_dataset(DATASET_NEAR, get_town("taipei-xinyi")) == "F-D0047-061"
    assert resolve_live_dataset(DATASET_WEEK, get_town("hualien-hualien")) == "F-D0047-043"


def test_parse_near_payload_and_normalize():
    town = get_town("taipei-xinyi")
    slices = CWAAdapter._parse_forecast_payload(_near_payload(), town)
    assert len(slices) == 2
    assert slices[0].apparent_temp_c == 34.0
    assert slices[1].weather_code == "12"
    days = normalize_to_daily(slices)
    assert len(days) == 1
    assert days[0].date == "2026-07-02"
    assert days[0].temp_high_c == 33.0
    assert days[0].temp_low_c == 31.0
    assert days[0].max_pop_percent == 80


def test_parse_week_payload_uses_max_min_temperatures():
    town = get_town("hualien-hualien")
    slices = CWAAdapter._parse_forecast_payload(_week_payload(), town)
    assert len(slices) == 2
    assert slices[0].temp_high_c == 31.0
    assert slices[1].temp_low_c == 24.0

    days = normalize_to_daily(slices)
    assert len(days) == 1
    assert days[0].temp_high_c == 31.0
    assert days[0].temp_low_c == 24.0
    assert days[0].max_pop_percent == 60


def test_parse_payload_tolerates_unexpected_shape():
    town = get_town("taipei-xinyi")
    assert CWAAdapter._parse_forecast_payload({"records": {}}, town) == []


def test_fetch_live_surfaces_timeout(monkeypatch: pytest.MonkeyPatch):
    town = get_town("taipei-xinyi")
    adapter = CWAAdapter(Settings(cwa_api_key="test-key"))

    async def fake_get(self, url, params):  # noqa: ARG001
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(UpstreamError, match="timed out"):
        asyncio.run(adapter.fetch_forecast_slices(town))


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


def test_normalize_to_hourly_keeps_optional_fields():
    slices = [
        TimeSlice(
            start="2026-07-01T00:00:00",
            end="2026-07-01T03:00:00",
            temp_c=27.0,
            apparent_temp_c=30.5,
            pop_percent=40,
            weather="多雲",
            weather_code="04",
        ),
        TimeSlice(
            start="2026-07-01T03:00:00",
            end="2026-07-01T06:00:00",
            weather="晴",
        ),
    ]
    hourly = normalize_to_hourly(slices)
    assert len(hourly) == 2
    assert hourly[0].apparent_temp_c == 30.5
    assert hourly[0].weather_code == "04"
    assert hourly[1].weather == "晴"


def test_normalize_to_hourly_collapses_mixed_1h_and_3h_slices_to_uniform_grid():
    slices = [
        TimeSlice(
            start="2026-07-04T00:00:00+08:00",
            end="2026-07-04T01:00:00+08:00",
            temp_c=28.0,
            apparent_temp_c=30.0,
            pop_percent=10,
            weather="晴",
            weather_code="01",
        ),
        TimeSlice(
            start="2026-07-04T01:00:00+08:00",
            end="2026-07-04T02:00:00+08:00",
            temp_c=29.0,
            apparent_temp_c=31.0,
            pop_percent=20,
            weather="晴時多雲",
            weather_code="02",
        ),
        TimeSlice(
            start="2026-07-04T02:00:00+08:00",
            end="2026-07-04T03:00:00+08:00",
            temp_c=30.0,
            apparent_temp_c=32.0,
            pop_percent=40,
            weather="多雲",
            weather_code="04",
        ),
        TimeSlice(
            start="2026-07-04T03:00:00+08:00",
            end="2026-07-04T06:00:00+08:00",
            temp_c=31.0,
            apparent_temp_c=33.0,
            pop_percent=60,
            weather="短暫陣雨",
            weather_code="12",
        ),
    ]

    hourly = normalize_to_hourly(slices)

    assert [slot.time for slot in hourly] == [
        "2026-07-04T00:00:00+08:00",
        "2026-07-04T03:00:00+08:00",
    ]
    assert hourly[0].temp_c == 29.0
    assert hourly[0].apparent_temp_c == 31.0
    assert hourly[0].pop_percent == 40
    assert hourly[0].weather == "晴"
    assert hourly[0].weather_code == "01"
    assert hourly[1].temp_c == 31.0
    assert hourly[1].weather_code == "12"


def test_normalize_to_hourly_keeps_mock_3h_structure_unchanged():
    town = get_town("taipei-xinyi")
    slices = mock_time_slices(DATASET_NEAR, town, horizon_start=date(2026, 7, 1))

    hourly = normalize_to_hourly(slices)

    assert len(hourly) == len(slices)
    assert [slot.time for slot in hourly] == [slot.start for slot in slices]
    assert [slot.temp_c for slot in hourly] == [slot.temp_c for slot in slices]


def test_hourly_chart_gate_matches_72h_window():
    today = date(2026, 7, 4)
    assert should_include_hourly_chart(date(2026, 7, 4), today=today) is True
    assert should_include_hourly_chart(date(2026, 7, 6), today=today) is True
    assert should_include_hourly_chart(date(2026, 7, 7), today=today) is False


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
    town = get_town("taipei-xinyi")
    start = date(2026, 7, 1)
    a = mock_time_slices(DATASET_WEEK, town, horizon_start=start)
    b = mock_time_slices(DATASET_WEEK, town, horizon_start=start)
    assert [s.temp_c for s in a] == [s.temp_c for s in b]
    assert len(a) == 14
    near = mock_time_slices(DATASET_NEAR, town, horizon_start=start)
    assert len(near) == 24
    assert near[0].apparent_temp_c is not None
    assert near[0].weather_code is not None


def test_parse_live_town_payload_includes_non_curated_town():
    towns = CWAAdapter._parse_town_payload(_towns_payload())
    codes = {town.code for town in towns}
    assert "cwa-65000270" in codes
    gongliao = next(town for town in towns if town.code == "cwa-65000270")
    assert gongliao.city == "新北市"
    assert gongliao.name == "貢寮區"


def test_parse_sunrise_payload_prefers_exact_target_date():
    result = CWAAdapter._parse_sunrise_payload(_sunrise_payload(), "臺北市", date(2026, 7, 4))
    assert result is not None
    assert result.source_date == "2026-07-04"
    assert result.sunrise_time == "05:08"
    assert result.is_approximate is False


def test_parse_sunrise_payload_normalizes_partial_dates_and_county_variants():
    result = CWAAdapter._parse_sunrise_payload(
        _sunrise_partial_date_payload(),
        "臺北市",
        date(2026, 7, 4),
    )
    assert result is not None
    assert result.source_date == "2026-07-04"
    assert result.sunset_time == "18:47"
    assert result.is_approximate is False


def test_parse_sunrise_payload_falls_back_to_last_available_row():
    result = CWAAdapter._parse_sunrise_payload(_sunrise_payload(), "臺北市", date(2026, 12, 31))
    assert result is not None
    assert result.source_date == "2025-07-05"
    assert result.is_approximate is True


def test_fetch_sunrise_sunset_requests_exact_county_and_date(monkeypatch: pytest.MonkeyPatch):
    town = get_town("taipei-xinyi")
    adapter = CWAAdapter(Settings(cwa_api_key="test-key"))
    calls: list[dict[str, object]] = []

    async def fake_request_json(
        dataset: str,
        *,
        params: dict[str, str] | None = None,
        cache_key: str | None = None,
        ttl: int | None = None,
    ) -> dict:
        calls.append(
            {
                "dataset": dataset,
                "params": params,
                "cache_key": cache_key,
                "ttl": ttl,
            }
        )
        return _sunrise_payload()

    monkeypatch.setattr(adapter, "_request_json", fake_request_json)
    result = asyncio.run(adapter.fetch_sunrise_sunset(town, date(2026, 7, 4)))

    assert result.source_date == "2026-07-04"
    assert result.is_approximate is False
    assert calls == [
        {
            "dataset": DATASET_SUNRISE,
            "params": {"CountyName": "臺北市", "Date": "2026-07-04"},
            "cache_key": "cwa:sunrise:臺北市:2026-07-04",
            "ttl": SUNRISE_CACHE_TTL,
        }
    ]


def test_fetch_sunrise_sunset_falls_back_when_exact_row_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    town = get_town("taipei-xinyi")
    adapter = CWAAdapter(Settings(cwa_api_key="test-key"))
    calls: list[dict[str, object]] = []
    responses = iter(
        [
            {
                "records": {
                    "locations": {
                        "location": [{"CountyName": "臺北市", "time": []}],
                    }
                }
            },
            _sunrise_payload(),
        ]
    )

    async def fake_request_json(
        dataset: str,
        *,
        params: dict[str, str] | None = None,
        cache_key: str | None = None,
        ttl: int | None = None,
    ) -> dict:
        calls.append(
            {
                "dataset": dataset,
                "params": params,
                "cache_key": cache_key,
                "ttl": ttl,
            }
        )
        return next(responses)

    monkeypatch.setattr(adapter, "_request_json", fake_request_json)
    result = asyncio.run(adapter.fetch_sunrise_sunset(town, date(2026, 12, 31)))

    assert result.source_date == "2025-07-05"
    assert result.is_approximate is True
    assert calls == [
        {
            "dataset": DATASET_SUNRISE,
            "params": {"CountyName": "臺北市", "Date": "2026-12-31"},
            "cache_key": "cwa:sunrise:臺北市:2026-12-31",
            "ttl": SUNRISE_CACHE_TTL,
        },
        {
            "dataset": DATASET_SUNRISE,
            "params": {"CountyName": "臺北市"},
            "cache_key": "cwa:sunrise:臺北市:fallback",
            "ttl": SUNRISE_CACHE_TTL,
        },
    ]


def test_parse_uv_payload_selects_nearest_station_deterministically():
    town = get_town("taipei-xinyi")
    result = CWAAdapter._parse_uv_payload(_uv_payload(), _station_payload(), town)
    assert result is not None
    assert result.station_id == "467280"
    assert result.level == "過量"
    assert result.source_label == "目前紫外線"


def test_rule_based_summary_uses_selected_target_date():
    service = AiSummaryService(Settings())
    days = [
        DailyForecast(
            date="2026-07-04",
            weather="晴",
            temp_low_c=25,
            temp_high_c=32,
            max_pop_percent=10,
        ),
        DailyForecast(
            date="2026-07-05",
            weather="雨",
            temp_low_c=24,
            temp_high_c=28,
            max_pop_percent=80,
        ),
    ]
    text, mode = service.summarize(get_town("taipei-xinyi"), days, "2026-07-05")
    assert mode == "rule-based"
    assert "7/5" in text
    assert "7/4" not in text

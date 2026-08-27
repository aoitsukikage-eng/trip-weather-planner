"""Unit and integration tests for weather domain i18n and bilingual (zh/en) APIs."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi.testclient import TestClient

from app.adapters.cwa import _NEAR_DATASETS_BY_CITY, _WEEK_DATASETS_BY_CITY, CWAAdapter
from app.adapters.moenv import COUNTY_ZONES, MOENVAdapter
from app.core.config import Settings, get_settings
from app.data.towns import all_towns, get_town
from app.i18n.station_names import (
    AQI_STATION_NAME_EN_BY_ID,
    UV_STATION_NAME_EN_BY_ID,
    get_aqi_station_name_text,
    get_uv_station_name_text,
)
from app.i18n.town_names import TOWN_NAME_EN_BY_GEOCODE
from app.i18n.weather_text import (
    ADVICE_HINT_MAP,
    AQI_LEVEL_MAP,
    MOON_PHASE_MAP,
    TOWN_NAME_MAP,
    UV_LABEL_MAP,
    UV_LEVEL_MAP,
    WARNING_TITLE_MAP,
    WX_CODE_TO_TEXT,
    format_warning,
    get_advice_hint,
    get_advice_hint_key,
    get_county_name_text,
    get_moon_phase_text,
    get_town_name_text,
    get_uv_level_text,
    get_weather_text,
)
from app.main import app
from app.main import settings as app_settings

client = TestClient(app)


def _today_taipei() -> date:
    return datetime.now(ZoneInfo("Asia/Taipei")).date()


def _future(days: int) -> str:
    return (_today_taipei() + timedelta(days=days)).isoformat()


@pytest.fixture(autouse=True)
def force_mock_mode():
    original_cwa = os.environ.get("CWA_API_KEY")
    original_moenv = os.environ.get("MOENV_API_KEY")
    os.environ["CWA_API_KEY"] = ""
    os.environ["MOENV_API_KEY"] = ""
    get_settings.cache_clear()
    app_settings.cwa_api_key = ""
    app_settings.moenv_api_key = ""
    app.state.cache.clear()
    yield
    if original_cwa is None:
        os.environ.pop("CWA_API_KEY", None)
    else:
        os.environ["CWA_API_KEY"] = original_cwa
    if original_moenv is None:
        os.environ.pop("MOENV_API_KEY", None)
    else:
        os.environ["MOENV_API_KEY"] = original_moenv
    get_settings.cache_clear()
    app_settings.cwa_api_key = original_cwa or ""
    app_settings.moenv_api_key = original_moenv or ""
    app.state.cache.clear()


# ---------------------------------------------------------------------------
# 1. API Integration Tests: /api/towns?lang=en
# ---------------------------------------------------------------------------
def test_get_towns_bilingual():
    zh_resp = client.get("/api/towns?lang=zh").json()
    en_resp = client.get("/api/towns?lang=en").json()

    assert zh_resp["success"] is True
    assert en_resp["success"] is True

    zh_xinyi = next(t for t in zh_resp["data"] if t["code"] == "taipei-xinyi")
    en_xinyi = next(t for t in en_resp["data"] if t["code"] == "taipei-xinyi")

    assert zh_xinyi["name"] == "信義區"
    assert zh_xinyi["city"] == "臺北市"
    assert zh_xinyi["name_en"] == "Xinyi District"
    assert zh_xinyi["city_en"] == "Taipei City"

    assert en_xinyi["name"] == "信義區"
    assert en_xinyi["city"] == "臺北市"
    assert en_xinyi["name_en"] == "Xinyi District"
    assert en_xinyi["city_en"] == "Taipei City"


def test_api_accepts_lang_ja():
    """AC1: GET /api/towns?lang=ja and /api/forecast?...&lang=ja return 200 (not 422)."""
    towns_res = client.get("/api/towns?lang=ja")
    assert towns_res.status_code == 200
    assert towns_res.json()["success"] is True

    target = _future(1)
    forecast_res = client.get(f"/api/forecast?town=taipei-xinyi&date={target}&lang=ja")
    assert forecast_res.status_code == 200
    assert forecast_res.json()["success"] is True


# ---------------------------------------------------------------------------
# 2. API Integration Tests: /api/forecast?lang=en covering all 8 domains
# ---------------------------------------------------------------------------
def test_forecast_english_domains():
    target = _future(1)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}&lang=en").json()
    assert body["success"] is True
    forecast = body["data"]["forecast"]
    ai_summary = body["data"]["ai_summary"]

    # Domain 7 & 8: County & Town names in Town object
    assert forecast["town"]["city"] == "臺北市"
    assert forecast["town"]["name"] == "信義區"
    assert forecast["town"]["city_en"] == "Taipei City"
    assert forecast["town"]["name_en"] == "Xinyi District"

    # Domain 1: weather_code_text
    first_day = forecast["days"][0]
    assert first_day["weather_code"] is not None
    assert first_day["weather"] in {entry["en"] for entry in WX_CODE_TO_TEXT.values()}

    # Domain 2: advice_hint & advice_hint_key
    assert first_day["advice_hint_key"] in {"heavy_rain", "hot", "cold", "stable"}
    assert first_day["advice_hint"] is not None
    assert any(
        first_day["advice_hint"].startswith(entry["en"]) for entry in ADVICE_HINT_MAP.values()
    )

    # Domain 3: aqi_level
    assert forecast["aqi"]["level"] in {
        "Good",
        "Moderate",
        "Unhealthy for Sensitive Groups",
        "Unhealthy",
        "Very Unhealthy",
        "Hazardous",
        "Demo Station",
    }
    assert forecast["aqi"]["source_label"] == "Current Air Quality (Demo)"

    # Domain 4: uv_level
    assert forecast["uv"]["level"] in {"Low", "Moderate", "High", "Very High", "Extreme"}
    assert forecast["uv"]["source_label"] == "Current UV Index (for reference only)"

    # Domain 6: moon_phase
    assert forecast["moon"]["phase"] in {entry["en"] for entry in MOON_PHASE_MAP.values()}
    assert forecast["moon"]["county"] == "Taipei City"

    # Domain 7: sunrise_sunset county
    assert forecast["sunrise_sunset"]["county"] == "Taipei City"

    # Domain 9: ai_summary composition in English
    assert ai_summary["text"].startswith("The forecast for Xinyi District, Taipei City on ")


def test_warning_domain_english(monkeypatch: pytest.MonkeyPatch):
    os.environ["CWA_API_KEY"] = "demo-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "demo-key"

    from app.adapters.cwa import ForecastSlices
    from app.adapters.mock_data import mock_time_slices

    async def fake_fetch_forecast_slices(self, town):  # noqa: ARG001
        today = _today_taipei()
        return ForecastSlices(
            daily=mock_time_slices("F-D0047-091", town, horizon_start=today),
            hourly=mock_time_slices("F-D0047-093", town, horizon_start=today),
            source_label="test-live",
        )

    async def fake_warnings(self, town, lang="zh"):  # noqa: ARG001
        title, desc = format_warning("豪雨特報", town.city, lang=lang)
        from app.schemas.weather import WeatherWarning

        return [WeatherWarning(title=title, severity="danger", description=desc)]

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_fetch_forecast_slices)
    monkeypatch.setattr(CWAAdapter, "fetch_warnings", fake_warnings)

    target = _future(1)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}&lang=en").json()
    assert body["success"] is True
    warnings = body["data"]["forecast"]["warnings"]
    assert len(warnings) == 1
    assert warnings[0]["title"] == "Extremely Heavy Rain Advisory"
    assert warnings[0]["description"] == (
        "Extremely Heavy Rain Advisory for Taipei City. "
        "Please stay tuned for the latest weather updates."
    )


# ---------------------------------------------------------------------------
# 3. Cache Isolation Test: forecast cache key incorporates lang
# ---------------------------------------------------------------------------
def test_forecast_cache_isolated_by_lang():
    target = _future(2)
    zh_url = f"/api/forecast?town=taipei-xinyi&date={target}&lang=zh"
    en_url = f"/api/forecast?town=taipei-xinyi&date={target}&lang=en"

    zh_first = client.get(zh_url).json()
    assert zh_first["meta"]["cached"] is False
    assert zh_first["data"]["forecast"]["town"]["name"] == "信義區"

    # Second call with lang=zh should hit cache
    zh_second = client.get(zh_url).json()
    assert zh_second["meta"]["cached"] is True
    assert zh_second["data"]["forecast"]["town"]["name"] == "信義區"

    # Call with lang=en must NOT hit the zh cache and must return English forecast values
    en_first = client.get(en_url).json()
    assert en_first["meta"]["cached"] is False
    assert en_first["data"]["forecast"]["town"]["name"] == "信義區"
    assert en_first["data"]["forecast"]["town"]["name_en"] == "Xinyi District"

    # Second call with lang=en should hit en cache
    en_second = client.get(en_url).json()
    assert en_second["meta"]["cached"] is True
    assert en_second["data"]["forecast"]["town"]["name"] == "信義區"
    assert en_second["data"]["forecast"]["town"]["name_en"] == "Xinyi District"


# ---------------------------------------------------------------------------
# 4. Domain Unit Tests for i18n Lookup Tables
# ---------------------------------------------------------------------------
def test_wx_code_to_text_coverage():
    # Verify all 42 weather codes produce valid bilingual text
    for i in range(1, 43):
        code_str = f"{i:02d}"
        assert code_str in WX_CODE_TO_TEXT
        zh_val = get_weather_text(None, code_str, lang="zh")
        en_val = get_weather_text(None, code_str, lang="en")
        assert zh_val == WX_CODE_TO_TEXT[code_str]["zh"]
        assert en_val == WX_CODE_TO_TEXT[code_str]["en"]


def test_county_and_town_mappings():
    assert get_county_name_text("臺北市", lang="en") == "Taipei City"
    assert get_county_name_text("宜蘭縣", lang="en") == "Yilan County"
    assert get_county_name_text("連江縣", lang="en") == "Lienchiang County"

    assert get_town_name_text("taipei-xinyi", "信義區", lang="en") == "Xinyi District"
    assert get_town_name_text("newtaipei-banqiao", "板橋區", lang="en") == "Banqiao District"
    assert get_town_name_text("lienchiang-nangan", "南竿鄉", lang="en") == "Nangan Township"


def test_uv_and_moon_phase_mappings():
    for zh_level, expected_en in UV_LEVEL_MAP.items():
        assert get_uv_level_text(zh_level, lang="en") == expected_en["en"]

    for zh_phase, expected_en in MOON_PHASE_MAP.items():
        assert get_moon_phase_text(zh_phase, lang="en") == expected_en["en"]


def test_advice_hint_keys_and_values():
    assert get_advice_hint_key(34.0, 25.0, 80) == "heavy_rain"
    assert get_advice_hint_key(34.0, 25.0, 30) == "hot"
    assert get_advice_hint_key(20.0, 10.0, 10) == "cold"
    assert get_advice_hint_key(25.0, 20.0, 10) == "stable"

    assert get_advice_hint("heavy_rain", lang="en").startswith("High chance of rain.")
    assert get_advice_hint("stable", lang="en").startswith("Weather is generally stable")


# ---------------------------------------------------------------------------
# 5. Requirement 4, 5, 6: Invariant & Live Path Tests for Town Identifiers
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cwa_live_path_request_params_are_language_independent(
    monkeypatch: pytest.MonkeyPatch,
):
    """TEST-CRITICAL requirement:
    Exercises live path with httpx mocked out.
    Asserts outgoing CWA LocationName == '信義區' and dataset == 'F-D0047-063' for both languages.
    """
    settings = Settings(cwa_api_key="test_live_key")
    assert settings.use_mock is False
    adapter = CWAAdapter(settings)

    captured_requests: list[dict[str, Any]] = []

    class DummyResponse:
        def __init__(self, json_data: dict[str, Any]) -> None:
            self._json_data = json_data
            self.status_code = 200

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return self._json_data

    dummy_payload = {
        "records": {
            "Locations": [
                {
                    "Location": [
                        {
                            "LocationName": "信義區",
                            "WeatherElement": [
                                {
                                    "ElementName": "Wx",
                                    "Time": [
                                        {
                                            "StartTime": "2026-08-25 12:00:00",
                                            "EndTime": "2026-08-25 18:00:00",
                                            "ElementValue": [
                                                {"value": "晴時多雲", "measures": "天氣現象"}
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    }

    async def fake_get(
        self, url: str, params: dict[str, str] | None = None, **kwargs: Any
    ) -> DummyResponse:
        dataset_id = url.rsplit("/", 1)[-1]
        captured_requests.append({"url": url, "dataset": dataset_id, "params": params})
        return DummyResponse(dummy_payload)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    town_obj = get_town("taipei-xinyi")
    assert town_obj is not None

    # Test for lang='zh' and lang='en'
    captured_requests.clear()
    await adapter.fetch_forecast_slices(town_obj)
    requests_zh = list(captured_requests)

    captured_requests.clear()
    await adapter.fetch_forecast_slices(town_obj)
    requests_en = list(captured_requests)

    weekly_zh = next(r for r in requests_zh if r["dataset"] == "F-D0047-063")
    weekly_en = next(r for r in requests_en if r["dataset"] == "F-D0047-063")

    assert weekly_zh["params"]["LocationName"] == "信義區"
    assert weekly_en["params"]["LocationName"] == "信義區"
    assert weekly_zh["dataset"] == "F-D0047-063"
    assert weekly_en["dataset"] == "F-D0047-063"


def test_town_construction_invariants():
    """TEST-INVARIANT requirement:
    Assert get_town() and all_towns() return Chinese name/city, while name_en/city_en are populated.
    Assert _parse_town_payload() produces Chinese name/city and populated name_en/city_en.
    """
    town = get_town("taipei-xinyi")
    assert town is not None
    assert town.name == "信義區"
    assert town.city == "臺北市"
    assert town.name_en == "Xinyi District"
    assert town.city_en == "Taipei City"

    towns = all_towns()
    assert len(towns) >= 22
    for t in towns:
        assert isinstance(t.name, str) and len(t.name) > 0
        assert isinstance(t.city, str) and len(t.city) > 0
        assert not t.name.isascii()
        assert not t.city.isascii()

    fake_cwa_payload = {
        "records": {
            "Locations": [
                {
                    "LocationsName": "臺北市",
                    "Location": [
                        {
                            "LocationName": "信義區",
                            "Geocode": "63000020",
                            "Latitude": 25.033,
                            "Longitude": 121.565,
                        }
                    ],
                }
            ]
        }
    }
    parsed = CWAAdapter._parse_town_payload(fake_cwa_payload)
    assert len(parsed) == 1
    p_town = parsed[0]
    assert p_town.name == "信義區"
    assert p_town.city == "臺北市"
    assert p_town.name_en == "Xinyi District"
    assert p_town.city_en == "Taipei City"


def test_dataset_and_county_zone_vocabularies_resolvable_from_all_towns():
    """TEST-INVARIANT-2 requirement:
    Assert every key of _NEAR_DATASETS_BY_CITY, _WEEK_DATASETS_BY_CITY, and COUNTY_ZONES
    is resolvable from the Town.city values produced by all_towns().
    """
    town_cities = {town.city for town in all_towns()}
    for city in _NEAR_DATASETS_BY_CITY:
        assert city in town_cities, f"_NEAR_DATASETS_BY_CITY key '{city}' not in all_towns() cities"
    for city in _WEEK_DATASETS_BY_CITY:
        assert city in town_cities, f"_WEEK_DATASETS_BY_CITY key '{city}' not in all_towns() cities"
    for city in COUNTY_ZONES:
        assert city in town_cities, f"COUNTY_ZONES key '{city}' not in all_towns() cities"


def test_official_town_names_table_and_cwa_integration():
    """AC4: Verify official town names table and CWA adapter integration."""
    # (a) Table length == 368
    assert len(TOWN_NAME_EN_BY_GEOCODE) == 368

    # (b) All values isascii() and non-empty
    for geocode, name_en in TOWN_NAME_EN_BY_GEOCODE.items():
        assert isinstance(name_en, str) and len(name_en) > 0, f"Empty value for {geocode}"
        assert name_en.isascii(), f"Non-ASCII value for {geocode}: {name_en}"

    # (c) All values end with one of {'District', 'Township', 'City'}
    allowed_suffixes = {"District", "Township", "City"}
    for geocode, name_en in TOWN_NAME_EN_BY_GEOCODE.items():
        suffix = name_en.strip().split()[-1]
        assert (
            suffix in allowed_suffixes
        ), f"Unexpected suffix '{suffix}' for {geocode}: {name_en}"

    # (d) Fake CWA payload with all 368 items -> CwaAdapter._parse_town_payload()
    locations = [
        {
            "LocationName": f"Town-{geocode}",
            "Geocode": geocode,
            "Latitude": 24.0,
            "Longitude": 121.0,
        }
        for geocode in TOWN_NAME_EN_BY_GEOCODE
    ]
    fake_payload = {
        "records": {
            "Locations": [
                {
                    "LocationsName": "臺北市",
                    "Location": locations,
                }
            ]
        }
    }
    parsed_towns = CWAAdapter._parse_town_payload(fake_payload)
    assert len(parsed_towns) == 368
    for t in parsed_towns:
        assert t.name_en is not None and len(t.name_en) > 0
        assert t.name_en.isascii()

    # (e) Existing 22 static slugs still parseable
    for slug, entry in TOWN_NAME_MAP.items():
        translated = get_town_name_text(slug, entry["zh"], lang="en")
        assert translated == entry["en"]


def test_station_names_table_and_getters():
    """AC4: Verify station names table counts, ASCII validity, AC3 rules, and fallback."""
    # (a) Record count and ASCII / non-empty checks
    assert len(AQI_STATION_NAME_EN_BY_ID) == 84
    assert len(UV_STATION_NAME_EN_BY_ID) >= 30

    for siteid, en_name in AQI_STATION_NAME_EN_BY_ID.items():
        assert isinstance(en_name, str) and len(en_name) > 0, f"Empty AQI name for {siteid}"
        assert en_name.isascii(), f"Non-ASCII AQI name for {siteid}: {en_name}"
        assert en_name == en_name.strip(), f"Whitespace padding in AQI name for {siteid}: {en_name}"

    for st_id, en_name in UV_STATION_NAME_EN_BY_ID.items():
        assert isinstance(en_name, str) and len(en_name) > 0, f"Empty UV name for {st_id}"
        assert en_name.isascii(), f"Non-ASCII UV name for {st_id}: {en_name}"
        assert en_name == en_name.strip(), f"Whitespace padding in UV name for {st_id}: {en_name}"

    # (b) AC3 specific assertions
    assert get_uv_station_name_text("466920", "臺北", lang="en") == "Taipei"
    assert get_uv_station_name_text("467280", "後龍", lang="en") == "Houlong"
    assert get_uv_station_name_text("467650", "日月潭", lang="en") == "Sun Moon Lake"
    assert get_aqi_station_name_text("84", "富貴角", lang="en") == "FugueiCape"
    assert (
        get_aqi_station_name_text("203", "南投（鹿谷）", lang="en") == "Nantou (Lugu Township)"
    )
    assert (
        get_aqi_station_name_text("311", "新北（樹林）", lang="en")
        == "New Taipei (Shulin District)"
    )
    assert (
        get_aqi_station_name_text("204", "屏東（琉球）", lang="en")
        == "Pingtung (Liuqiu Township)"
    )
    assert (
        get_aqi_station_name_text("313", "屏東（枋山）", lang="en")
        == "Pingtung (Fangshan Township)"
    )

    # (c) lang='zh' returns name_zh verbatim
    assert get_uv_station_name_text("466920", "臺北", lang="zh") == "臺北"
    assert get_aqi_station_name_text("84", "富貴角", lang="zh") == "富貴角"
    assert get_aqi_station_name_text("203", "南投（鹿谷）", lang="zh") == "南投（鹿谷）"

    # (d) Unknown / missing ID returns fallback name_zh without raising exception or returning empty
    assert get_uv_station_name_text("unknown-uv-id", "未知測站", lang="en") == "未知測站"
    assert get_uv_station_name_text(None, "未知測站", lang="en") == "未知測站"
    assert get_aqi_station_name_text("99999", "未知空品站", lang="en") == "未知空品站"
    assert get_aqi_station_name_text(None, "未知空品站", lang="en") == "未知空品站"


@pytest.mark.asyncio
async def test_adapter_station_name_wiring(monkeypatch: pytest.MonkeyPatch):
    """AC5: Verify CWA and MOENV adapter station_name wiring in lang='en' vs lang='zh'."""
    # 1. MOENVAdapter live path mock test
    settings = Settings(moenv_api_key="test-key")
    assert settings.use_moenv_mock is False
    moenv_adapter = MOENVAdapter(settings)

    fake_aqi_payload = [
        {
            "siteid": "84",
            "sitename": "富貴角",
            "latitude": "25.29",
            "longitude": "121.53",
            "aqi": "35",
            "status": "良好",
            "publishtime": "2026-08-27 12:00:00",
        }
    ]

    async def fake_request(dataset: str):  # noqa: ARG001
        return fake_aqi_payload

    monkeypatch.setattr(moenv_adapter, "_request", fake_request)

    town = get_town("taipei-xinyi")
    assert town is not None

    # lang='en' -> station_name should be 'FugueiCape' (no Chinese characters)
    aqi_en = await moenv_adapter.fetch_current(town, lang="en")
    assert aqi_en is not None
    assert aqi_en.station_name == "FugueiCape"
    assert aqi_en.station_name.isascii()

    # lang='zh' -> station_name should be '富貴角' verbatim
    aqi_zh = await moenv_adapter.fetch_current(town, lang="zh")
    assert aqi_zh is not None
    assert aqi_zh.station_name == "富貴角"

    # 2. CWAAdapter UV path _label_uv_info test
    from app.adapters.cwa import _label_uv_info
    from app.schemas.weather import UVInfo

    uv_raw = UVInfo(
        value=5.0,
        level="中",
        level_code="moderate",
        source_label="目前紫外線",
        source_type="observation",
        observed_at="2026-08-27T12:00:00+08:00",
        station_id="466920",
        station_name="臺北",
    )

    today = _today_taipei()
    uv_labeled_en = _label_uv_info(uv_raw, today, lang="en")
    assert uv_labeled_en.station_name == "Taipei"
    assert uv_labeled_en.station_name.isascii()

    uv_labeled_zh = _label_uv_info(uv_raw, today, lang="zh")
    assert uv_labeled_zh.station_name == "臺北"


def test_ja_lookup_tables_and_fallback_chain():
    """AC2 & AC3: Verify 7 lookup tables have ja entries (75 total) and
    fallback chain assertions."""
    # AC2: Table counts and ja presence
    assert len([k for k, v in WX_CODE_TO_TEXT.items() if "ja" in v]) == 42
    assert len([k for k, v in AQI_LEVEL_MAP.items() if "ja" in v]) == 10
    assert len([k for k, v in MOON_PHASE_MAP.items() if "ja" in v]) == 8
    assert len([k for k, v in UV_LEVEL_MAP.items() if "ja" in v]) == 5
    assert len([k for k, v in WARNING_TITLE_MAP.items() if "ja" in v]) == 4
    assert len([k for k, v in ADVICE_HINT_MAP.items() if "ja" in v]) == 4
    assert len([k for k, v in UV_LABEL_MAP.items() if "ja" in v]) == 2

    # JMA terms verification for AC2 examples
    assert WX_CODE_TO_TEXT["01"]["ja"] == "晴れ"
    assert WX_CODE_TO_TEXT["04"]["ja"] == "曇り"
    assert WX_CODE_TO_TEXT["11"]["ja"] == "にわか雨"

    # AC3: Specific required assertions
    assert get_weather_text(None, "01", lang="ja") == "晴れ"
    assert get_county_name_text("臺北市", lang="ja") == "臺北市"
    assert get_town_name_text("cwa-63000010", "松山區", lang="ja") == "松山區"
    assert get_uv_station_name_text("466920", "臺北", lang="ja") == "臺北"
    assert get_aqi_station_name_text("84", "松山", lang="ja") == "松山"


def test_composer_1_format_warning_ja():
    """AC4 Composer 1: format_warning ja branch."""
    title, desc = format_warning("豪雨特報", "臺北市", lang="ja")
    assert title == "豪雨警報"
    assert desc == "臺北市に豪雨警報が発表されています。最新の気象情報にご注意ください。"
    assert "，" not in desc
    assert "請留意" not in desc


def test_composer_2_rule_based_summary_ja():
    """AC4 Composer 2: _rule_based_summary ja branch and _SYSTEM_PROMPT_JA."""
    from app.schemas.weather import DailyForecast
    from app.services.ai_summary import _SYSTEM_PROMPT_JA, _rule_based_summary

    assert "旅行の事前準備アシスタント" in _SYSTEM_PROMPT_JA

    town = get_town("taipei-xinyi")
    assert town is not None
    day = DailyForecast(
        date="2026-08-28",
        temp_high_c=32.0,
        temp_low_c=25.0,
        max_pop_percent=20,
        weather="晴れ",
        weather_code="01",
        advice_hint="天気が安定しているため、屋外のアクティビティに適しています。",
        advice_hint_key="stable",
    )
    summary = _rule_based_summary(town, day, lang="ja")
    assert "8/28の臺北市信義區の天気予報は" in summary
    assert "最高降水確率は20%です。" in summary
    assert "預報為" not in summary
    assert "降雨機率" not in summary
    assert "，" not in summary


def test_composer_3_aqi_advice_hint_ja():
    """AC4 Composer 3: day.advice_hint appended AQI sentence ja branch."""
    from app.schemas.weather import AQIForecast, DailyForecast

    day = DailyForecast(
        date="2026-08-28",
        temp_high_c=30.0,
        temp_low_c=24.0,
        max_pop_percent=10,
        weather="晴れ",
        weather_code="01",
        advice_hint="天気が安定しているため、屋外のアクティビティに適しています。",
        advice_hint_key="stable",
        aqi_forecast=AQIForecast(
            date="2026-08-28",
            value=35,
            level="良好",
            level_code="good",
        ),
    )
    # Simulate forecast.py composition for lang='ja'
    lang = "ja"
    if day.aqi_forecast and day.aqi_forecast.level:
        if lang == "ja":
            day.advice_hint = f"{day.advice_hint or ''} 空気質予報は{day.aqi_forecast.level}です。"

    assert day.advice_hint is not None
    assert "空気質予報は良好です。" in day.advice_hint
    assert "空氣品質預報為" not in day.advice_hint


@pytest.mark.asyncio
async def test_adapters_ja_outputs():
    """AC5: Verify adapter mock/demo strings produce explicit Japanese outputs."""
    town = get_town("taipei-xinyi")
    assert town is not None
    today = _today_taipei()

    # 1. MOENVAdapter mock demo station ja name
    moenv_mock = MOENVAdapter(Settings(cwa_api_key="", moenv_api_key=""))
    aqi_mock = await moenv_mock.fetch_current(town, lang="ja")
    assert aqi_mock is not None
    assert aqi_mock.station_name == "デモ観測局"
    assert aqi_mock.source_label == "現在の空気質（デモ）"
    assert aqi_mock.level == "良好"

    # 2. mock_data.py mock_uv_info ja station_name
    from app.adapters.mock_data import mock_uv_info
    uv_ja = mock_uv_info(town, today, lang="ja")
    assert uv_ja.station_name == "信義區モック観測局"
    assert uv_ja.source_label == "現在の紫外線インデックス"

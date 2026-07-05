"""API-level tests via TestClient (mock mode, no credentials, no network)."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.main import settings as app_settings
from app.schemas.weather import TimeSlice

client = TestClient(app)


def _today_taipei() -> date:
    return datetime.now(ZoneInfo("Asia/Taipei")).date()


def _future(days: int) -> str:
    return (_today_taipei() + timedelta(days=days)).isoformat()


def _past(days: int) -> str:
    return (_today_taipei() - timedelta(days=days)).isoformat()


@pytest.fixture(autouse=True)
def force_mock_mode():
    original = os.environ.get("CWA_API_KEY")
    os.environ["CWA_API_KEY"] = ""
    get_settings.cache_clear()
    app_settings.cwa_api_key = ""
    app.state.cache.clear()
    yield
    if original is None:
        os.environ.pop("CWA_API_KEY", None)
    else:
        os.environ["CWA_API_KEY"] = original
    get_settings.cache_clear()
    app_settings.cwa_api_key = original or ""
    app.state.cache.clear()


def test_health_mock_mode():
    body = client.get("/api/health").json()
    assert body["success"] is True
    assert body["data"]["mock_mode"] is True


def test_towns_cover_all_22_divisions():
    body = client.get("/api/towns").json()
    cities = {t["city"] for t in body["data"]}
    # All 22 counties/cities of Taiwan must be represented.
    assert len(cities) == 22
    assert body["meta"]["source"] == "mock"


def test_towns_live_mode_prefers_full_live_catalog(monkeypatch: pytest.MonkeyPatch):
    os.environ["CWA_API_KEY"] = "demo-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "demo-key"

    from app.adapters.cwa import CWAAdapter

    fake_towns = [
        {
            "code": f"cwa-{index:05d}",
            "name": f"測試鄉鎮{index}",
            "city": "新北市" if index % 2 == 0 else "臺北市",
            "lat": 25.0 + index * 0.001,
            "lon": 121.0 + index * 0.001,
        }
        for index in range(300)
    ]
    fake_towns.append(
        {
            "code": "cwa-65000270",
            "name": "貢寮區",
            "city": "新北市",
            "lat": 25.021273,
            "lon": 121.910293,
        }
    )

    async def fake_fetch_all_towns(self):  # noqa: ARG001
        from app.schemas.weather import Town

        return [Town(**item) for item in fake_towns]

    monkeypatch.setattr(CWAAdapter, "fetch_all_towns", fake_fetch_all_towns)
    body = client.get("/api/towns").json()
    assert body["success"] is True
    assert len(body["data"]) >= 300
    assert any(item["name"] == "貢寮區" and item["city"] == "新北市" for item in body["data"])
    assert body["meta"]["source"] == "cwa-live"


def test_forecast_returns_multiple_days_and_marks_target():
    target = _future(4)  # >2 days -> 7-day dataset -> multiple days
    body = client.get(f"/api/forecast?town=hualien-hualien&date={target}").json()
    assert body["success"] is True
    forecast = body["data"]["forecast"]
    assert forecast["target_date"] == target
    assert len(forecast["days"]) == 7
    # The target date must be present among the returned days (so UI can highlight).
    assert any(d["date"] == target for d in forecast["days"])
    assert forecast["hourly"] is not None
    assert len(forecast["hourly"]) == 24
    assert forecast["sunrise_sunset"]["target_date"] == target
    assert forecast["uv"]["source_label"] == "目前紫外線僅供參考"


def test_forecast_includes_hourly_for_next_72_hours():
    target = _future(1)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}").json()
    assert body["success"] is True
    forecast = body["data"]["forecast"]
    assert forecast["hourly"] is not None
    assert len(forecast["hourly"]) == 24
    first_slot = forecast["hourly"][0]
    assert first_slot["time"].startswith(_today_taipei().isoformat())
    assert "apparent_temp_c" in first_slot
    assert "weather_code" in first_slot


def test_forecast_week_and_hourly_are_stable_across_all_seven_chips():
    states = []
    for offset in range(7):
        target = _future(offset)
        body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}").json()
        assert body["success"] is True
        forecast = body["data"]["forecast"]
        states.append((len(forecast["days"]), forecast["hourly"] is not None))
        assert forecast["target_date"] == target
        assert any(day["date"] == target for day in forecast["days"])

    assert states == [(7, True)] * 7


def test_forecast_cache_hit_on_second_call():
    target = _future(3)
    url = f"/api/forecast?town=taipei-xinyi&date={target}"
    first = client.get(url).json()
    second = client.get(url).json()
    assert first["meta"]["cached"] is False
    assert second["meta"]["cached"] is True


def test_unknown_town_and_bad_date():
    assert client.get(f"/api/forecast?town=nope&date={_future(2)}").status_code == 404
    assert client.get("/api/forecast?town=taipei-xinyi&date=2026-13-40").status_code == 400
    assert client.get(f"/api/forecast?town=taipei-xinyi&date={_past(1)}").status_code == 400
    assert client.get(f"/api/forecast?town=taipei-xinyi&date={_future(11)}").status_code == 400


def test_forecast_discards_partial_eighth_day_from_live_horizon(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.adapters.mock_data import mock_time_slices

    os.environ["CWA_API_KEY"] = "demo-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "demo-key"

    async def fake_fetch_forecast_slices(self, town):  # noqa: ARG001
        daily = []
        anchor = _today_taipei()
        for offset in range(8):
            start_at = datetime.combine(anchor + timedelta(days=offset), datetime.min.time()).replace(
                hour=6
            )
            daily.append(
                TimeSlice(
                    start=start_at.isoformat(),
                    end=(start_at + timedelta(hours=12)).isoformat(),
                    temp_c=28 + offset,
                    apparent_temp_c=30 + offset,
                    pop_percent=20 + offset,
                    weather="多雲",
                    weather_code="04",
                )
            )
        return ForecastSlices(
            daily=daily,
            hourly=mock_time_slices("F-D0047-093", town, horizon_start=_today_taipei()),
            source_label="test-live",
        )

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_fetch_forecast_slices)

    target = _future(6)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}").json()
    assert body["success"] is True
    assert body["data"]["forecast"]["target_date"] == target
    assert [day["date"] for day in body["data"]["forecast"]["days"]] == [
        _future(offset) for offset in range(7)
    ]
    assert body["data"]["forecast"]["days"][-1]["date"] == _future(6)

    rejected = client.get(f"/api/forecast?town=taipei-xinyi&date={_future(7)}").json()
    assert rejected["success"] is False
    assert rejected["error"]["message"] == "Date must be within the available forecast horizon."


def test_summary_text_follows_selected_non_first_day():
    target = _future(4)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}").json()
    assert body["success"] is True
    summary_text = body["data"]["ai_summary"]["text"]
    month, day = target.split("-")[1:]
    assert f"{int(month)}/{int(day)}" in summary_text


def test_forecast_uses_plain_uv_label_for_today_only():
    target = _future(0)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={target}").json()
    assert body["success"] is True
    assert body["data"]["forecast"]["uv"]["source_label"] == "目前紫外線"

"""API-level tests via TestClient (mock mode, no credentials, no network)."""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
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
    original_cwa = os.environ.get("CWA_API_KEY")
    original_moenv = os.environ.get("MOENV_API_KEY")
    os.environ["CWA_API_KEY"] = ""
    os.environ["MOENV_API_KEY"] = ""
    get_settings.cache_clear()
    app_settings.cwa_api_key = ""
    app_settings.moenv_api_key = ""
    app.state.cache.clear()
    if getattr(app.state, "single_flight", None) is not None:
        app.state.single_flight.clear()
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
    if getattr(app.state, "single_flight", None) is not None:
        app.state.single_flight.clear()


def test_health_mock_mode():
    body = client.get("/api/health").json()
    assert body["success"] is True
    assert body["data"]["mock_mode"] is True


def test_towns_cover_all_22_divisions():
    body = client.get("/api/towns").json()
    cities = {t["city"] for t in body["data"]}
    # All 22 counties/cities of Taiwan must be represented.
    assert len(cities) == 22
    assert body["meta"]["source"] == "local-catalog"


def test_towns_use_local_catalog_when_cwa_catalog_scan_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    os.environ["CWA_API_KEY"] = "demo-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "demo-key"

    from app.adapters.cwa import CWAAdapter

    async def fail_fetch_all_towns(self):  # noqa: ARG001
        raise AssertionError("request path must not scan CWA town datasets")

    monkeypatch.setattr(CWAAdapter, "fetch_all_towns", fail_fetch_all_towns)
    body = client.get("/api/towns").json()
    assert body["success"] is True
    assert len(body["data"]) >= 368
    assert all(item["code"].startswith("cwa-") for item in body["data"])
    assert body["meta"]["source"] == "local-catalog"

    os.environ["CWA_API_KEY"] = ""
    get_settings.cache_clear()
    app_settings.cwa_api_key = ""
    forecast = client.get(f"/api/forecast?town=cwa-63000020&date={_future(0)}")
    assert forecast.status_code == 200
    assert forecast.json()["data"]["forecast"]["town"]["code"] == "cwa-63000020"


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
    assert forecast["moon"]["county"] == "花蓮縣"
    assert forecast["moon"]["source_date"] == target
    assert forecast["moon"]["moonrise_time"] == "18:42"
    assert forecast["moon"]["moonset_time"] == "05:11"
    assert 0 <= forecast["moon"]["illumination_fraction"] <= 1
    assert isinstance(forecast["moon"]["waxing"], bool)


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


def test_forecast_cache_isolated_by_town_and_requested_date_and_not_http_cacheable():
    today = _future(0)
    tomorrow = _future(1)
    first = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    same = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    other_town = client.get(f"/api/forecast?town=hualien-hualien&date={today}")
    other_date = client.get(f"/api/forecast?town=taipei-xinyi&date={tomorrow}")

    assert first.headers["cache-control"] == "no-store"
    assert same.headers["cache-control"] == "no-store"
    assert first.json()["meta"]["cached"] is False
    assert same.json()["meta"]["cached"] is True
    assert other_town.json()["meta"]["cached"] is False
    assert other_date.json()["meta"]["cached"] is False


def test_forecast_error_response_is_not_http_cacheable():
    response = client.get(f"/api/forecast?town=nope&date={_future(0)}")

    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"


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
            start_day = anchor + timedelta(days=offset)
            start_at = datetime.combine(start_day, datetime.min.time()).replace(hour=6)
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


def test_today_outside_live_horizon_focuses_earliest_available_day(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.core.errors import UpstreamError

    os.environ["CWA_API_KEY"] = "demo-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "demo-key"
    first_day = _today_taipei() + timedelta(days=1)

    def build_slice(offset: int) -> TimeSlice:
        start_at = datetime.combine(
            first_day + timedelta(days=offset), datetime.min.time()
        ).isoformat()
        return TimeSlice(
            start=start_at,
            end=start_at,
            temp_c=28,
            pop_percent=20,
            weather="多雲",
        )

    async def fake_fetch_forecast_slices(self, town):  # noqa: ARG001
        daily = [build_slice(offset) for offset in range(7)]
        return ForecastSlices(daily=daily, hourly=[], source_label="test-live")

    async def unavailable(*args, **kwargs):  # noqa: ARG001
        raise UpstreamError("test upstream unavailable", error_code="test_upstream")

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_fetch_forecast_slices)
    monkeypatch.setattr(CWAAdapter, "fetch_sunrise_sunset", unavailable)
    monkeypatch.setattr(CWAAdapter, "fetch_uv_info", unavailable)
    monkeypatch.setattr(CWAAdapter, "fetch_moon", unavailable)

    today = _future(0)
    body = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()

    assert body["success"] is True
    forecast = body["data"]["forecast"]
    assert forecast["requested_date"] == today
    assert forecast["date_adjusted"] is True
    assert forecast["target_date"] == _future(1)
    assert any(day["date"] == forecast["target_date"] for day in forecast["days"])


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


def test_lifespan_manages_shared_http_client():
    from starlette.testclient import TestClient

    with TestClient(app) as tc:
        assert tc.app.state.http_client is not None
        assert not tc.app.state.http_client.is_closed
    assert getattr(app.state, "http_client", None) is None


def test_forecast_identity_isolation_alias_first():
    today = _future(0)
    # Request alias first
    res_alias = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res_alias["success"] is True
    assert res_alias["data"]["forecast"]["town"]["code"] == "taipei-xinyi"

    # Request canonical second
    res_canon = client.get(f"/api/forecast?town=cwa-63000020&date={today}").json()
    assert res_canon["success"] is True
    assert res_canon["data"]["forecast"]["town"]["code"] == "cwa-63000020"

    # Request alias again to ensure it remains alias
    res_alias_again = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res_alias_again["data"]["forecast"]["town"]["code"] == "taipei-xinyi"


def test_forecast_identity_isolation_canonical_first():
    today = _future(0)
    # Request canonical first
    res_canon = client.get(f"/api/forecast?town=cwa-63000020&date={today}").json()
    assert res_canon["success"] is True
    assert res_canon["data"]["forecast"]["town"]["code"] == "cwa-63000020"

    # Request alias second
    res_alias = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res_alias["success"] is True
    assert res_alias["data"]["forecast"]["town"]["code"] == "taipei-xinyi"

    # Request canonical again
    res_canon_again = client.get(f"/api/forecast?town=cwa-63000020&date={today}").json()
    assert res_canon_again["data"]["forecast"]["town"]["code"] == "cwa-63000020"


@pytest.mark.asyncio
async def test_forecast_coalescing_same_key(monkeypatch: pytest.MonkeyPatch):
    import httpx

    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.adapters.mock_data import mock_time_slices

    build_calls = 0

    async def fake_fetch_slices(self, town):
        nonlocal build_calls
        build_calls += 1
        await asyncio.sleep(0.05)
        return ForecastSlices(
            daily=mock_time_slices("F-D0047-091", town, horizon_start=_today_taipei()),
            hourly=mock_time_slices("F-D0047-093", town, horizon_start=_today_taipei()),
            source_label="test-slices",
        )

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_fetch_slices)

    today = _future(1)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r1, r2 = await asyncio.gather(
            ac.get(f"/api/forecast?town=taipei-xinyi&date={today}"),
            ac.get(f"/api/forecast?town=taipei-xinyi&date={today}"),
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["data"]["forecast"]["town"]["code"] == "taipei-xinyi"
        assert r2.json()["data"]["forecast"]["town"]["code"] == "taipei-xinyi"
        assert build_calls == 1


@pytest.mark.asyncio
async def test_forecast_global_concurrency_ceiling_across_requests_with_mock_transport(
    monkeypatch: pytest.MonkeyPatch,
):
    from typing import Any

    import httpx

    from app.main import lifespan

    os.environ["CWA_API_KEY"] = "test-cwa-key"
    os.environ["MOENV_API_KEY"] = "test-moenv-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "test-cwa-key"
    app_settings.moenv_api_key = "test-moenv-key"

    active_ops = 0
    max_active_ops = 0
    today = _today_taipei()

    def make_cwa_slices_payload(location_name: str) -> dict[str, Any]:
        times_wx, times_t, times_mint, times_maxt, times_pop = [], [], [], [], []
        for i in range(14):
            dt_start = datetime.combine(today, datetime.min.time()) + timedelta(hours=i * 12)
            dt_end = dt_start + timedelta(hours=12)
            st = dt_start.strftime("%Y-%m-%d %H:%M:%S")
            et = dt_end.strftime("%Y-%m-%d %H:%M:%S")
            times_wx.append({
                "StartTime": st,
                "EndTime": et,
                "ElementValue": [{"value": "晴時多雲", "Wx": "晴時多雲", "WxCode": "02"}],
            })
            times_t.append({
                "StartTime": st,
                "EndTime": et,
                "ElementValue": [{"value": "26", "T": "26"}],
            })
            times_mint.append({
                "StartTime": st,
                "EndTime": et,
                "ElementValue": [{"value": "22", "MinT": "22"}],
            })
            times_maxt.append({
                "StartTime": st,
                "EndTime": et,
                "ElementValue": [{"value": "30", "MaxT": "30"}],
            })
            times_pop.append({
                "StartTime": st,
                "EndTime": et,
                "ElementValue": [{"value": "10", "PoP": "10"}],
            })

        return {
            "records": {
                "Locations": [
                    {
                        "Location": [
                            {
                                "LocationName": location_name,
                                "WeatherElement": [
                                    {"ElementName": "Wx", "Time": times_wx},
                                    {"ElementName": "T", "Time": times_t},
                                    {"ElementName": "MinT", "Time": times_mint},
                                    {"ElementName": "MaxT", "Time": times_maxt},
                                    {"ElementName": "PoP", "Time": times_pop},
                                ],
                            }
                        ]
                    }
                ]
            }
        }

    async def handle_request(request: httpx.Request) -> httpx.Response:
        nonlocal active_ops, max_active_ops
        active_ops += 1
        max_active_ops = max(max_active_ops, active_ops)
        await asyncio.sleep(0.04)
        active_ops -= 1

        url_str = str(request.url)
        params = dict(request.url.params)
        loc = params.get("LocationName", "信義區")

        if "F-D0047" in url_str:
            return httpx.Response(200, json=make_cwa_slices_payload(loc))
        if "A-B0062-001" in url_str:
            return httpx.Response(
                200,
                json={
                    "records": {
                        "locations": {
                            "location": [
                                {
                                    "CountyName": "臺北市",
                                    "time": [
                                        {
                                            "Date": today.isoformat(),
                                            "SunRiseTime": "05:45",
                                            "SunSetTime": "17:45",
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                },
            )
        if "A-B0063-001" in url_str:
            return httpx.Response(
                200,
                json={
                    "CountyName": "臺北市",
                    "MoonRiseTime": "18:00",
                    "MoonSetTime": "06:00",
                },
            )
        if "O-A0005-001" in url_str or "O-A0001-001" in url_str:
            return httpx.Response(200, json={"records": {"location": []}})
        if "W-C0033-001" in url_str:
            return httpx.Response(200, json={"records": ""})
        if "aqx_p_432" in url_str:
            return httpx.Response(
                200,
                json=[
                    {
                        "sitename": "測試站",
                        "siteid": "1",
                        "latitude": "25.03",
                        "longitude": "121.56",
                        "aqi": "40",
                        "status": "良好",
                        "publishtime": "2026-10-02 12:00",
                    }
                ],
            )
        if "aqf_p_01" in url_str:
            return httpx.Response(
                200,
                json=[
                    {"area": "北部", "forecastdate": today.isoformat(), "aqi": "40"}
                ],
            )
        return httpx.Response(200, json={})

    async with lifespan(app):
        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handle_request))
        app.state.http_client = mock_client
        app.state.cache.clear()
        app.state.single_flight.clear()

        # At least four concurrent requests with different final build/cache keys
        towns = ["cwa-63000010", "cwa-63000020", "cwa-63000030", "cwa-63000040"]
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            tasks = [
                ac.get(f"/api/forecast?town={t}&date={today.isoformat()}")
                for t in towns
            ]
            responses = await asyncio.gather(*tasks)

        for t, r in zip(towns, responses, strict=True):
            assert r.status_code == 200, f"Status: {r.status_code}, Body: {r.text}"
            body = r.json()
            assert body["success"] is True
            assert body["data"]["forecast"]["town"]["code"] == t

        # Verify real concurrency occurred and application-wide limit 3 was never exceeded
        assert 2 <= max_active_ops <= 3


def test_near_hourly_degradation_preserves_daily_forecast(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.adapters.mock_data import mock_time_slices

    async def fake_fetch_slices(self, town):
        # Slices with empty hourly (near term failed)
        return ForecastSlices(
            daily=mock_time_slices("F-D0047-091", town, horizon_start=_today_taipei()),
            hourly=[],
            source_label="F-D0047-091",
        )

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_fetch_slices)

    today = _future(1)
    res = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res["success"] is True
    assert len(res["data"]["forecast"]["days"]) == 7
    assert res["data"]["forecast"]["hourly"] is None


def test_optional_enrichments_degradation_preserves_daily(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter
    from app.adapters.moenv import MOENVAdapter
    from app.core.errors import UpstreamError

    async def fail(*args, **kwargs):
        raise UpstreamError("service down", error_code="service_down")

    monkeypatch.setattr(CWAAdapter, "fetch_sunrise_sunset", fail)
    monkeypatch.setattr(CWAAdapter, "fetch_uv_info", fail)
    monkeypatch.setattr(CWAAdapter, "fetch_moon", fail)
    monkeypatch.setattr(CWAAdapter, "fetch_warnings", fail)
    monkeypatch.setattr(MOENVAdapter, "fetch_current", fail)
    monkeypatch.setattr(MOENVAdapter, "fetch_forecast", fail)

    today = _future(1)
    res = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res["success"] is True
    forecast = res["data"]["forecast"]
    assert len(forecast["days"]) == 7
    assert forecast["sunrise_sunset"] is None
    assert forecast["uv"] is None
    assert forecast["moon"] is None
    assert forecast["warnings"] == []
    assert forecast["aqi"] is None


def test_forecast_total_timeout_with_stale(monkeypatch: pytest.MonkeyPatch):
    today = _future(2)
    # 1. Warm cache
    warmed = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert warmed["success"] is True

    # 2. Make the entry stale by setting its fresh_until into the past
    key = f"forecast:taipei-xinyi:{today}:zh"
    entry = app.state.cache._store[key]
    app.state.cache._store[key] = (0.0, 9999999999.0, entry[2])

    # 3. Next build times out: simulate genuine timeout via small timeout and delay
    from app.adapters.cwa import CWAAdapter
    from app.core.errors import UpstreamError

    async def slow_fetch(self, town):
        await asyncio.sleep(1.0)
        raise UpstreamError("timed out", error_code="upstream_timeout")

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", slow_fetch)
    monkeypatch.setattr(get_settings(), "forecast_timeout_seconds", 0.01)

    res = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert res["success"] is True
    assert res["meta"]["cached"] is True
    assert res["meta"]["source"] == "stale-cache"
    assert res["data"]["forecast"]["town"]["code"] == "taipei-xinyi"


def test_forecast_total_timeout_without_stale(monkeypatch: pytest.MonkeyPatch):
    today = _future(3)

    from app.adapters.cwa import CWAAdapter
    from app.core.errors import UpstreamError

    async def slow_fetch(self, town):
        await asyncio.sleep(1.0)
        raise UpstreamError("timed out", error_code="upstream_timeout")

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", slow_fetch)
    monkeypatch.setattr(get_settings(), "forecast_timeout_seconds", 0.01)

    resp = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    assert resp.status_code == 502
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["error_code"] == "upstream_timeout"


def test_structured_log_content_and_secret_redaction(caplog: pytest.LogCaptureFixture):
    import logging

    today = _future(1)
    with caplog.at_level(logging.INFO, logger="app.routers.forecast"):
        res = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
        assert res.status_code == 200

    found = False
    for record in caplog.records:
        if record.name == "app.routers.forecast":
            found = True
            assert hasattr(record, "canonical_town")
            assert hasattr(record, "cache_result")
            assert hasattr(record, "source")
            assert hasattr(record, "duration_ms")
            assert hasattr(record, "degraded_fields")
            assert hasattr(record, "request_id")
            assert record.canonical_town == "cwa-63000020"

    assert found is True
    assert "Authorization" not in caplog.text
    assert "CWA-" not in caplog.text


@pytest.mark.asyncio
async def test_forecast_leader_deadline_cancels_underlying_build_and_cleans_state(
    monkeypatch: pytest.MonkeyPatch,
):
    import httpx

    from app.main import lifespan

    os.environ["CWA_API_KEY"] = "test-cwa-key"
    os.environ["MOENV_API_KEY"] = "test-moenv-key"
    get_settings.cache_clear()
    app_settings.cwa_api_key = "test-cwa-key"
    app_settings.moenv_api_key = "test-moenv-key"

    active_ops = 0
    cancelled_ops = 0
    today = _today_taipei()
    town = "cwa-63000020"
    flight_key = f"build:{town}:{today.isoformat()}:zh"

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        nonlocal active_ops, cancelled_ops
        active_ops += 1
        try:
            await asyncio.sleep(5.0)
            return httpx.Response(200, json={})
        except asyncio.CancelledError:
            cancelled_ops += 1
            raise
        finally:
            active_ops -= 1

    monkeypatch.setattr(get_settings(), "forecast_timeout_seconds", 0.05)

    async with lifespan(app):
        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(slow_handler))
        app.state.http_client = mock_client
        app.state.cache.clear()
        app.state.single_flight.clear()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(f"/api/forecast?town={town}&date={today.isoformat()}")
            assert resp.status_code == 502
            body = resp.json()
            assert body["success"] is False
            assert body["error"]["error_code"] == "upstream_timeout"

        # Allow cancelled coroutines to complete cleanup
        await asyncio.sleep(0.02)

        # Underlying build cancelled and active counter returns to 0
        assert cancelled_ops >= 1
        assert active_ops == 0
        assert app.state.single_flight.is_inflight(flight_key) is False

        # No orphan tasks remain on event loop
        remaining = [
            t
            for t in asyncio.all_tasks()
            if t is not asyncio.current_task() and not t.done()
        ]
        assert len(remaining) == 0


@pytest.mark.asyncio
async def test_forecast_waiter_cancellation_does_not_cancel_leader(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.adapters.mock_data import mock_time_slices

    today = _future(2)
    town = "taipei-xinyi"
    flight_key = f"build:{town}:{today}:zh"
    leader_running = asyncio.Event()
    allow_finish = asyncio.Event()

    async def controlled_slices(self, town_obj):
        leader_running.set()
        await allow_finish.wait()
        return ForecastSlices(
            daily=mock_time_slices("F-D0047-091", town_obj, horizon_start=_today_taipei()),
            hourly=[],
            source_label="test",
        )

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", controlled_slices)

    # Reset cache and single-flight
    app.state.cache.clear()
    app.state.single_flight.clear()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        req_url = f"/api/forecast?town={town}&date={today}"

        # Start leader request
        t1 = asyncio.create_task(ac.get(req_url))
        await leader_running.wait()

        # Start waiter request
        t2 = asyncio.create_task(ac.get(req_url))
        await asyncio.sleep(0.01)

        # Cancel waiter
        t2.cancel()
        with pytest.raises(asyncio.CancelledError):
            await t2

        # Allow leader to finish
        allow_finish.set()
        r1 = await t1
        assert r1.status_code == 200
        assert r1.json()["success"] is True
        assert app.state.single_flight.is_inflight(flight_key) is False


def test_forecast_unexpected_runtime_error_not_masked_by_stale_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services.ai_summary import AiSummaryService

    today = _future(2)
    # 1. Warm cache
    warmed = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert warmed["success"] is True

    # 2. Make the entry stale
    key = f"forecast:taipei-xinyi:{today}:zh"
    entry = app.state.cache._store[key]
    app.state.cache._store[key] = (0.0, 9999999999.0, entry[2])

    # 3. Simulate unexpected RuntimeError during build
    def exploding_summarize(*args, **kwargs):
        raise RuntimeError("database crash or unexpected bug")

    monkeypatch.setattr(AiSummaryService, "summarize", exploding_summarize)

    unhandled_client = TestClient(app, raise_server_exceptions=False)
    resp = unhandled_client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    assert resp.status_code == 500
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["error_code"] == "internal_error"


def test_forecast_non_upstream_app_error_not_masked_by_stale_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter
    from app.core.errors import AppError

    today = _future(2)
    # 1. Warm cache
    warmed = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert warmed["success"] is True

    # 2. Make the entry stale
    key = f"forecast:taipei-xinyi:{today}:zh"
    entry = app.state.cache._store[key]
    app.state.cache._store[key] = (0.0, 9999999999.0, entry[2])

    # 3. Simulate non-upstream AppError during build
    async def bad_input_error(*args, **kwargs):
        raise AppError(
            "Custom validation failure",
            error_code="validation_failure",
            status_code=400,
        )

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", bad_input_error)

    resp = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["error_code"] == "validation_failure"


def test_forecast_upstream_error_uses_stale_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.adapters.cwa import CWAAdapter
    from app.core.errors import UpstreamError

    today = _future(2)
    # 1. Warm cache
    warmed = client.get(f"/api/forecast?town=taipei-xinyi&date={today}").json()
    assert warmed["success"] is True

    # 2. Make the entry stale
    key = f"forecast:taipei-xinyi:{today}:zh"
    entry = app.state.cache._store[key]
    app.state.cache._store[key] = (0.0, 9999999999.0, entry[2])

    # 3. Simulate genuine UpstreamError
    async def upstream_fail(*args, **kwargs):
        raise UpstreamError("CWA connection failed", error_code="upstream_http_error")

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", upstream_fail)

    resp = client.get(f"/api/forecast?town=taipei-xinyi&date={today}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["meta"]["cached"] is True
    assert body["meta"]["source"] == "stale-cache"

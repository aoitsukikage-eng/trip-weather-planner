"""API-level tests via TestClient (mock mode, no credentials, no network)."""

from __future__ import annotations

import asyncio
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
async def test_forecast_concurrency_ceiling_never_exceeded(
    monkeypatch: pytest.MonkeyPatch,
):
    import httpx

    from app.adapters.cwa import CWAAdapter, ForecastSlices
    from app.adapters.mock_data import mock_sunrise_sunset, mock_time_slices, mock_uv_info
    from app.adapters.moenv import MOENVAdapter
    from app.schemas.weather import MoonInfo

    active_ops = 0
    max_active_ops = 0

    async def tracked_op(result_fn):
        nonlocal active_ops, max_active_ops
        active_ops += 1
        max_active_ops = max(max_active_ops, active_ops)
        await asyncio.sleep(0.02)
        active_ops -= 1
        return result_fn()

    async def fake_slices(self, town):
        return await tracked_op(
            lambda: ForecastSlices(
                daily=mock_time_slices(
                    "F-D0047-091", town, horizon_start=_today_taipei()
                ),
                hourly=mock_time_slices(
                    "F-D0047-093", town, horizon_start=_today_taipei()
                ),
                source_label="test",
            )
        )

    async def fake_sunrise(self, town, d, lang="zh"):
        return await tracked_op(lambda: mock_sunrise_sunset(town, d, lang=lang))

    async def fake_uv(self, town, d, lang="zh"):
        return await tracked_op(lambda: mock_uv_info(town, d, lang=lang))

    async def fake_moon(self, town, d, lang="zh"):
        return await tracked_op(
            lambda: MoonInfo(
                county="臺北市",
                target_date=d.isoformat(),
                source_date=d.isoformat(),
                phase="滿月",
                icon="🌕",
                illumination_fraction=1.0,
                waxing=False,
            )
        )

    async def fake_warnings(self, town, lang="zh"):
        return await tracked_op(lambda: [])

    async def fake_current_aqi(self, town, lang="zh"):
        return await tracked_op(lambda: None)

    async def fake_forecast_aqi(self, county, lang="zh"):
        return await tracked_op(lambda: {})

    monkeypatch.setattr(CWAAdapter, "fetch_forecast_slices", fake_slices)
    monkeypatch.setattr(CWAAdapter, "fetch_sunrise_sunset", fake_sunrise)
    monkeypatch.setattr(CWAAdapter, "fetch_uv_info", fake_uv)
    monkeypatch.setattr(CWAAdapter, "fetch_moon", fake_moon)
    monkeypatch.setattr(CWAAdapter, "fetch_warnings", fake_warnings)
    monkeypatch.setattr(MOENVAdapter, "fetch_current", fake_current_aqi)
    monkeypatch.setattr(MOENVAdapter, "fetch_forecast", fake_forecast_aqi)

    today = _future(2)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get(f"/api/forecast?town=taipei-xinyi&date={today}")
        assert res.status_code == 200
        # Configured ceiling is 3; verify active operations never exceeded 3
        assert max_active_ops <= 3


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

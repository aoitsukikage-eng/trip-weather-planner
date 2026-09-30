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


@pytest.mark.asyncio
async def test_moenv_uses_injected_client_with_mock_transport():
    import httpx

    called = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called += 1
        assert "aqx_p_432" in str(request.url)
        return httpx.Response(200, json=CURRENT_LIST_FIXTURE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MOENVAdapter(
            Settings(cwa_api_key="test", moenv_api_key="test"),
            client=client,
        )
        town = get_town("taipei-xinyi")
        assert town is not None
        aqi = await adapter.fetch_current(town)
        assert aqi is not None
        assert aqi.value == 42
        assert called == 1


@pytest.mark.asyncio
async def test_moenv_stale_fallback_on_upstream_failure():
    import httpx

    from app.core.cache import TTLCache

    clock_time = 1000.0
    cache = TTLCache(default_ttl=60, stale_retention=3600, clock=lambda: clock_time)

    # First call succeeds
    def handler_ok(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=CURRENT_LIST_FIXTURE)

    transport = httpx.MockTransport(handler_ok)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MOENVAdapter(
            Settings(cwa_api_key="test", moenv_api_key="test"),
            cache=cache,
            client=client,
        )
        town = get_town("taipei-xinyi")
        assert town is not None
        aqi = await adapter.fetch_current(town)
        assert aqi is not None
        assert aqi.value == 42

    # Advance clock past fresh TTL (60s) into stale retention
    clock_time = 1100.0

    # Next call upstream returns HTTP 500 error
    def handler_fail(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    fail_transport = httpx.MockTransport(handler_fail)
    async with httpx.AsyncClient(transport=fail_transport) as client:
        fail_adapter = MOENVAdapter(
            Settings(cwa_api_key="test", moenv_api_key="test"),
            cache=cache,
            client=client,
        )
        # Should gracefully return stale cached data instead of raising UpstreamError
        stale_aqi = await fail_adapter.fetch_current(town)
        assert stale_aqi is not None
        assert stale_aqi.value == 42


@pytest.mark.asyncio
async def test_moenv_upstream_error_preserved_when_no_stale():
    import httpx

    from app.core.errors import UpstreamError

    def handler_fail(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler_fail)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MOENVAdapter(
            Settings(cwa_api_key="test", moenv_api_key="test"),
            client=client,
        )
        town = get_town("taipei-xinyi")
        assert town is not None
        with pytest.raises(UpstreamError) as exc_info:
            await adapter.fetch_current(town)
        assert exc_info.value.error_code == "moenv_upstream_error"


@pytest.mark.asyncio
async def test_moenv_single_flight_coalescing():
    import httpx

    from app.core.cache import AsyncSingleFlight, TTLCache

    call_count = 0

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        return httpx.Response(200, json=CURRENT_LIST_FIXTURE)

    transport = httpx.MockTransport(slow_handler)
    cache = TTLCache(default_ttl=60)
    sf = AsyncSingleFlight()

    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MOENVAdapter(
            Settings(cwa_api_key="test", moenv_api_key="test"),
            cache=cache,
            client=client,
            single_flight=sf,
        )
        town = get_town("taipei-xinyi")
        assert town is not None

        # Two concurrent calls for current AQI
        r1, r2 = await asyncio.gather(
            adapter.fetch_current(town),
            adapter.fetch_current(town),
        )
        assert r1 is not None and r2 is not None
        assert r1.value == 42
        assert r2.value == 42
        # Only 1 upstream request made due to single-flight!
        assert call_count == 1

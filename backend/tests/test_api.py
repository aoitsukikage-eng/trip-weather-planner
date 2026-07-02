"""API-level tests via TestClient (mock mode, no credentials, no network)."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.main import settings as app_settings

client = TestClient(app)


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture(autouse=True)
def force_mock_mode():
    original = os.environ.get("CWA_API_KEY")
    os.environ["CWA_API_KEY"] = ""
    get_settings.cache_clear()
    app_settings.cwa_api_key = ""
    yield
    if original is None:
        os.environ.pop("CWA_API_KEY", None)
    else:
        os.environ["CWA_API_KEY"] = original
    get_settings.cache_clear()
    app_settings.cwa_api_key = original or ""


def test_health_mock_mode():
    body = client.get("/api/health").json()
    assert body["success"] is True
    assert body["data"]["mock_mode"] is True


def test_towns_cover_all_22_divisions():
    body = client.get("/api/towns").json()
    cities = {t["city"] for t in body["data"]}
    # All 22 counties/cities of Taiwan must be represented.
    assert len(cities) == 22


def test_forecast_returns_multiple_days_and_marks_target():
    target = _future(4)  # >2 days -> 7-day dataset -> multiple days
    body = client.get(f"/api/forecast?town=hualien-hualien&date={target}").json()
    assert body["success"] is True
    forecast = body["data"]["forecast"]
    assert forecast["target_date"] == target
    # Multi-day: the full horizon is returned, not just the single target day.
    assert len(forecast["days"]) > 1
    # The target date must be present among the returned days (so UI can highlight).
    assert any(d["date"] == target for d in forecast["days"])


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

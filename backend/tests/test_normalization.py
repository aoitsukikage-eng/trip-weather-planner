"""Unit tests for weather normalization and dataset selection.

These run without any credentials and without network access.
"""

from __future__ import annotations

from datetime import date

from app.adapters.cwa import DATASET_NEAR, DATASET_WEEK, select_dataset
from app.adapters.mock_data import mock_time_slices
from app.data.towns import get_town
from app.schemas.weather import TimeSlice
from app.services.weather import normalize_to_daily, pick_target_day


def test_select_dataset_near_vs_week():
    today = date(2026, 7, 1)
    assert select_dataset(date(2026, 7, 2), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 3), today=today) == DATASET_NEAR
    assert select_dataset(date(2026, 7, 5), today=today) == DATASET_WEEK


def test_normalize_groups_by_day_and_summarizes():
    slices = [
        TimeSlice(start="2026-07-01T06:00:00", end="2026-07-01T18:00:00",
                  temp_c=24.0, pop_percent=20, weather="多雲"),
        TimeSlice(start="2026-07-01T18:00:00", end="2026-07-02T06:00:00",
                  temp_c=30.0, pop_percent=80, weather="陰時多雲短暫雨"),
        TimeSlice(start="2026-07-02T06:00:00", end="2026-07-02T18:00:00",
                  temp_c=26.0, pop_percent=10, weather="晴時多雲"),
    ]
    days = normalize_to_daily(slices)
    assert [d.date for d in days] == ["2026-07-01", "2026-07-02"]

    day1 = days[0]
    assert day1.temp_high_c == 30.0
    assert day1.temp_low_c == 24.0
    assert day1.max_pop_percent == 80
    assert "攜傘" in day1.advice_hint  # high PoP triggers umbrella advice


def test_pick_target_day_prefers_exact():
    slices = mock_time_slices(DATASET_WEEK, get_town("hualien-hualien"),
                              horizon_start=date(2026, 7, 1))
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
    assert len(a) == 14  # 7 days * 2 slices/day (12h cadence)

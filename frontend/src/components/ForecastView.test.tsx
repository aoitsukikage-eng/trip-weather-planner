import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";
import ForecastView, { getHourlyAnnotationStep } from "./ForecastView";
import type { ForecastResult, HourlyForecast } from "../lib/api";

function buildHourly(count: number): HourlyForecast[] {
  const start = new Date("2026-07-04T00:00:00+08:00");
  return Array.from({ length: count }, (_, index) => {
    const current = new Date(start);
    current.setHours(current.getHours() + index * 3);
    return {
      time: current.toISOString(),
      temp_c: 27 + (index % 3),
      apparent_temp_c: 29 + (index % 3),
      pop_percent: (index * 10) % 100,
      weather: index % 2 === 0 ? "晴時多雲" : "多雲",
      weather_code: index % 2 === 0 ? "01" : "04",
    };
  });
}

function buildResult(
  city: string,
  town: string,
  hourly: HourlyForecast[] = buildHourly(6),
): ForecastResult {
  return {
    forecast: {
      town: {
        code: `${city}-${town}`,
        city,
        name: town,
        lat: 25.0,
        lon: 121.5,
      },
      target_date: "2026-07-04",
      source_dataset: "cwa-live",
      days: [
        {
          date: "2026-07-04",
          temp_high_c: 32,
          temp_low_c: 26,
          max_pop_percent: 40,
          weather: "多雲",
          advice_hint: "帶傘。",
        },
        {
          date: "2026-07-05",
          temp_high_c: 31,
          temp_low_c: 25,
          max_pop_percent: 20,
          weather: "晴時多雲",
          advice_hint: "適合輕鬆出遊。",
        },
      ],
      hourly,
      sunrise_sunset: {
        county: city,
        target_date: "2026-07-04",
        source_date: "2026-06-29",
        sunrise_time: "05:12",
        sunset_time: "18:48",
        is_approximate: true,
      },
      uv: {
        value: 8,
        level: "過量",
        source_label: "目前紫外線",
        source_type: "observation",
        observed_at: "2026-07-04T12:00:00+08:00",
        station_id: "466920",
        station_name: "臺北",
      },
      generated_at: "2026-07-04T00:00:00Z",
    },
    ai_summary: {
      text: "test summary",
      mode: "rule-based",
    },
  };
}

describe("ForecastView", () => {
  afterEach(() => {
    cleanup();
  });

  test("shows the queried place in the chart section and updates on rerender", () => {
    const { rerender } = render(<ForecastView result={buildResult("新北市", "貢寮區")} />);

    expect(screen.getByText("新北市 貢寮區")).not.toBeNull();

    rerender(<ForecastView result={buildResult("臺北市", "信義區")} />);

    expect(screen.getByText("臺北市 信義區")).not.toBeNull();
    expect(screen.queryByText("新北市 貢寮區")).toBeNull();
  });

  test("shows selected sunrise date and centered chart place label", () => {
    render(<ForecastView result={buildResult("臺北市", "信義區")} />);

    expect(screen.getByText(/7\/4（六） 日出 05:12 · 日落 18:48/)).not.toBeNull();
    expect(screen.getByText(/參考 2026-06-29 天文資料/)).not.toBeNull();
    expect(screen.getByTestId("chart-place").textContent).toBe("臺北市 信義區");
  });

  test("thins hourly annotations when the chart gets too dense", () => {
    render(<ForecastView result={buildResult("新北市", "貢寮區", buildHourly(24))} />);

    const labels = screen.getAllByTestId("hourly-time-label");
    expect(labels.length).toBeLessThan(24);
    expect(labels.length).toBe(13);
  });
});

describe("getHourlyAnnotationStep", () => {
  test("returns a larger step when spacing is too tight", () => {
    expect(getHourlyAnnotationStep(24, 890)).toBe(2);
    expect(getHourlyAnnotationStep(8, 890)).toBe(1);
  });
});

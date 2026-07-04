import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, test, vi } from "vitest";
import App from "./App";

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 400): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

const townsBody = {
  success: true,
  data: [
    { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  ],
  error: null,
  meta: { request_id: "towns-1", cached: false, source: "mock" },
};

const liveForecastBody = {
  success: true,
  data: {
    forecast: {
      town: townsBody.data[0],
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
          advice_hint: "記得補水。",
        },
        {
          date: "2026-07-06",
          temp_high_c: 32,
          temp_low_c: 25,
          max_pop_percent: 30,
          weather: "多雲",
          advice_hint: "午後留意陣雨。",
        },
        {
          date: "2026-07-07",
          temp_high_c: 33,
          temp_low_c: 26,
          max_pop_percent: 50,
          weather: "陰短暫雨",
          advice_hint: "雨具備用。",
        },
        {
          date: "2026-07-08",
          temp_high_c: 34,
          temp_low_c: 26,
          max_pop_percent: 60,
          weather: "多雲時陰",
          advice_hint: "留意悶熱。",
        },
        {
          date: "2026-07-09",
          temp_high_c: 33,
          temp_low_c: 25,
          max_pop_percent: 30,
          weather: "晴時多雲",
          advice_hint: "適合外出。",
        },
        {
          date: "2026-07-10",
          temp_high_c: 32,
          temp_low_c: 25,
          max_pop_percent: 20,
          weather: "多雲",
          advice_hint: "補水防曬。",
        },
      ],
      hourly: [
        {
          time: "2026-07-04T00:00:00+08:00",
          temp_c: 28,
          apparent_temp_c: 30,
          pop_percent: 20,
          weather: "多雲",
          weather_code: "04",
        },
      ],
      sunrise_sunset: {
        county: "臺北市",
        target_date: "2026-07-04",
        source_date: "2026-07-04",
        sunrise_time: "05:12",
        sunset_time: "18:48",
        is_approximate: false,
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
      text: "7/4 留意午後陣雨。",
      mode: "rule-based",
    },
  },
  error: null,
  meta: { request_id: "forecast-live-1", cached: false, source: "cwa-live" },
};

const nextDayForecastBody = {
  ...liveForecastBody,
  data: {
    ...liveForecastBody.data,
    forecast: {
      ...liveForecastBody.data.forecast,
      target_date: "2026-07-05",
      sunrise_sunset: {
        county: "臺北市",
        target_date: "2026-07-05",
        source_date: "2026-07-05",
        sunrise_time: "05:13",
        sunset_time: "18:48",
        is_approximate: false,
      },
    },
    ai_summary: {
      text: "7/5 白天炎熱，記得補水。",
      mode: "rule-based",
    },
  },
  meta: { request_id: "forecast-live-2", cached: true, source: "cwa-live" },
};

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("shows a visible error when the backend returns a validation error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      return Promise.resolve(
        jsonResponse(
          {
            success: false,
            data: null,
            error: {
              error_code: "date_out_of_range",
              message: "Date must be within today..today+6.",
            },
            meta: { request_id: "forecast-1", cached: false, source: null },
          },
          false,
          400,
        ),
      );
    }));

    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Date must be within today..today+6.");
    expect(screen.queryByText("示範資料")).toBeNull();
  });

  test("renders only the friendly mock badge when the backend is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      return Promise.reject(new TypeError("Failed to fetch"));
    }));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("示範資料")).not.toBeNull();
    });
    expect(screen.queryByText(/mock:frontend-fallback/)).toBeNull();
    expect(screen.queryByText(/rule-based/)).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("clicking a day card re-queries that date and updates advice plus sunrise", async () => {
    const user = userEvent.setup();
    let forecastCallCount = 0;
    const scrollYBeforeClick = window.scrollY;
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      forecastCallCount += 1;
      if (forecastCallCount > 1) {
        return Promise.resolve(jsonResponse(nextDayForecastBody));
      }
      return Promise.resolve(jsonResponse(liveForecastBody));
    }));

    render(<App />);

    await screen.findByText("7/4 留意午後陣雨。");
    await user.click(screen.getByRole("button", { name: /7\/5/ }));

    await screen.findByText("7/5 白天炎熱，記得補水。");
    expect(screen.getByText("7/5（日） 日出 05:13 · 日落 18:48")).not.toBeNull();
    expect(screen.getByRole("button", { name: /7\/5/ }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.queryByText("帶傘。")).toBeNull();
    expect(window.scrollY).toBe(scrollYBeforeClick);
  });
});

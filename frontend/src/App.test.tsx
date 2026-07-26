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
    { code: "hualien-hualien", name: "花蓮市", city: "花蓮縣", lat: 23.98, lon: 121.6 },
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
        {
          time: "2026-07-04T03:00:00+08:00",
          temp_c: 27,
          apparent_temp_c: 29,
          pop_percent: 35,
          weather: "晴時多雲",
          weather_code: "01",
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
      hourly: [
        {
          time: "2026-07-05T00:00:00+08:00",
          temp_c: 35,
          apparent_temp_c: 38,
          pop_percent: 90,
          weather: "短暫陣雨或雷雨",
          weather_code: "13",
        },
        {
          time: "2026-07-05T03:00:00+08:00",
          temp_c: 34,
          apparent_temp_c: 37,
          pop_percent: 85,
          weather: "陰短暫雨",
          weather_code: "12",
        },
      ],
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

const lastDayForecastBody = {
  ...liveForecastBody,
  data: {
    ...liveForecastBody.data,
    forecast: {
      ...liveForecastBody.data.forecast,
      target_date: "2026-07-10",
      sunrise_sunset: {
        county: "臺北市",
        target_date: "2026-07-10",
        source_date: "2026-07-10",
        sunrise_time: "05:16",
        sunset_time: "18:49",
        is_approximate: false,
      },
    },
    ai_summary: {
      text: "7/10 天氣穩定，適合安排長時間戶外行程。",
      mode: "rule-based",
    },
  },
  meta: { request_id: "forecast-live-7", cached: true, source: "cwa-live" },
};

const validationErrorBody = {
  success: false,
  data: null,
  error: {
    error_code: "date_out_of_range",
    message: "Date must be within the available forecast horizon.",
  },
  meta: { request_id: "forecast-live-err", cached: false, source: null },
};

const otherTownForecastBody = {
  ...liveForecastBody,
  data: {
    ...liveForecastBody.data,
    forecast: {
      ...liveForecastBody.data.forecast,
      town: townsBody.data[1],
      hourly: [
        {
          time: "2026-07-04T00:00:00+08:00",
          temp_c: 24,
          apparent_temp_c: 26,
          pop_percent: 75,
          weather: "陰短暫雨",
          weather_code: "12",
        },
        {
          time: "2026-07-04T03:00:00+08:00",
          temp_c: 23,
          apparent_temp_c: 25,
          pop_percent: 70,
          weather: "陰短暫雨",
          weather_code: "12",
        },
      ],
      sunrise_sunset: {
        county: "花蓮縣",
        target_date: "2026-07-04",
        source_date: "2026-07-04",
        sunrise_time: "05:09",
        sunset_time: "18:42",
        is_approximate: false,
      },
      uv: {
        value: 6,
        level: "高量",
        source_label: "目前紫外線",
        source_type: "observation",
        observed_at: "2026-07-04T12:00:00+08:00",
        station_id: "466990",
        station_name: "花蓮",
      },
    },
    ai_summary: {
      text: "花蓮市天氣偏濕，注意短時降雨。",
      mode: "rule-based",
    },
  },
  meta: { request_id: "forecast-live-3", cached: false, source: "cwa-live" },
};

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    localStorage.clear();
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

  test("clicking a day card keeps the chart pinned while updating advice plus sunrise", async () => {
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
    expect(screen.queryByText(/參考 .* 天文資料/)).toBeNull();
    const chartBeforeClick = document.querySelector(".hourly-chart svg")?.innerHTML;
    await user.click(screen.getByRole("button", { name: /7\/5/ }));

    const selectedButton = await screen.findByRole("button", { name: /7\/5/ });
    await screen.findByText("7/5 白天炎熱，記得補水。");
    expect(screen.getByText("7/5 白天炎熱，記得補水。").closest(".summary-panel")?.getAttribute("aria-live")).toBe(
      "polite",
    );
    expect(screen.getByText("05:13")).not.toBeNull();
    expect(screen.getByText("18:48")).not.toBeNull();
    expect(screen.queryByText(/參考 .* 天文資料/)).toBeNull();
    expect(selectedButton.getAttribute("aria-pressed")).toBe("true");
    expect(document.activeElement).toBe(selectedButton);
    expect(screen.queryByText("帶傘。")).toBeNull();
    expect(document.querySelector(".hourly-chart svg")?.innerHTML).toBe(chartBeforeClick);
    expect(screen.getByTestId("chart-place").textContent).toBe("臺北市 信義區");
    expect(window.scrollY).toBe(scrollYBeforeClick);
  });

  test("clicking the last visible day card updates the selected advice and sunrise", async () => {
    const user = userEvent.setup();
    let forecastCallCount = 0;
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      forecastCallCount += 1;
      if (forecastCallCount > 1) {
        return Promise.resolve(jsonResponse(lastDayForecastBody));
      }
      return Promise.resolve(jsonResponse(liveForecastBody));
    }));

    render(<App />);

    await screen.findByText("7/4 留意午後陣雨。");
    await user.click(screen.getByTestId("day-card-2026-07-10"));

    const selectedButton = await screen.findByTestId("day-card-2026-07-10");
    expect(selectedButton.getAttribute("aria-pressed")).toBe("true");
    expect(selectedButton.getAttribute("aria-current")).toBe("date");
    expect(screen.getByText("7/10 天氣穩定，適合安排長時間戶外行程。")).not.toBeNull();
    expect(screen.getByText("05:16")).not.toBeNull();
    expect(screen.getByText("18:49")).not.toBeNull();
    expect(screen.queryByRole("status")).toBeNull();
  });

  test("keeps the current week view and selection when a day click re-query fails", async () => {
    const user = userEvent.setup();
    let forecastCallCount = 0;
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      forecastCallCount += 1;
      if (forecastCallCount === 1) {
        return Promise.resolve(jsonResponse(liveForecastBody));
      }
      return Promise.resolve(jsonResponse(validationErrorBody, false, 400));
    }));

    render(<App />);

    await screen.findByText("7/4 留意午後陣雨。");
    const chartBeforeClick = document.querySelector(".hourly-chart svg")?.innerHTML;
    const initiallySelected = screen.getByTestId("day-card-2026-07-04");

    await user.click(screen.getByTestId("day-card-2026-07-05"));

    expect(await screen.findByRole("status")).not.toBeNull();
    expect(screen.getByText(/日期切換失敗：Date must be within the available forecast horizon\./)).not.toBeNull();
    expect(screen.getByText("7/4 留意午後陣雨。")).not.toBeNull();
    expect(screen.getByText("05:12")).not.toBeNull();
    expect(screen.getByText("18:48")).not.toBeNull();
    expect(initiallySelected.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByTestId("day-card-2026-07-05").getAttribute("aria-pressed")).toBe("false");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.querySelector(".hourly-chart svg")?.innerHTML).toBe(chartBeforeClick);
  });

  test("querying a different town refreshes the chart to that town", async () => {
    const user = userEvent.setup();
    let forecastCallCount = 0;
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      forecastCallCount += 1;
      if (forecastCallCount === 1) {
        return Promise.resolve(jsonResponse(liveForecastBody));
      }
      return Promise.resolve(jsonResponse(otherTownForecastBody));
    }));

    render(<App />);

    await screen.findByText("7/4 留意午後陣雨。");
    const initialChart = document.querySelector(".hourly-chart svg")?.innerHTML;

    await user.selectOptions(screen.getByLabelText("縣市"), "花蓮縣");
    await user.selectOptions(screen.getByLabelText("鄉鎮市區"), "hualien-hualien");
    await user.click(screen.getByRole("button", { name: "查詢天氣" }));

    await screen.findByText("花蓮市天氣偏濕，注意短時降雨。");
    expect(screen.getByTestId("chart-place").textContent).toBe("花蓮縣 花蓮市");
    expect(document.querySelector(".hourly-chart svg")?.innerHTML).not.toBe(initialChart);
  });
});

// ── AC1: Initialization priority ─────────────────────────────────────────────

describe("App — initialization priority (AC1)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  function forecastFetch(first: unknown, other = first) {
    let count = 0;
    return vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      count += 1;
      return Promise.resolve(jsonResponse(count === 1 ? first : other));
    });
  }

  function firstForecastUrl(fetchMock: ReturnType<typeof vi.fn>): string {
    const calls = (fetchMock.mock.calls as unknown[][]).filter((args) =>
      String(args[0]).includes("/api/forecast"),
    );
    return String(calls[0]?.[0] ?? "");
  }

  test("defaultTown takes highest priority over lastTown and taipei-xinyi", async () => {
    localStorage.setItem("trip-weather-planner:default-town:v1", "hualien-hualien");
    localStorage.setItem("trip-weather-planner:last-town:v1", "taipei-xinyi");
    const fetchMock = forecastFetch(otherTownForecastBody);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=hualien-hualien");
    });
  });

  test("lastTown used when no defaultTown is stored", async () => {
    localStorage.setItem("trip-weather-planner:last-town:v1", "hualien-hualien");
    const fetchMock = forecastFetch(otherTownForecastBody);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=hualien-hualien");
    });
  });

  test("taipei-xinyi used when no stored prefs and it exists in towns list", async () => {
    // Put hualien-hualien first so towns[0] !== taipei-xinyi
    const reorderedTowns = {
      ...townsBody,
      data: [townsBody.data[1], townsBody.data[0]],
    };
    const fetchMock = vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(reorderedTowns));
      return Promise.resolve(jsonResponse(liveForecastBody));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=taipei-xinyi");
    });
  });

  test("falls back to towns[0] when no prefs and no taipei-xinyi in list", async () => {
    const noXinyiTowns = { ...townsBody, data: [townsBody.data[1]] };
    const fetchMock = vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(noXinyiTowns));
      return Promise.resolve(jsonResponse(otherTownForecastBody));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=hualien-hualien");
    });
  });

  test("ignores invalid defaultTown code and uses next fallback", async () => {
    localStorage.setItem("trip-weather-planner:default-town:v1", "defunct-code");
    const fetchMock = forecastFetch(liveForecastBody);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=taipei-xinyi");
    });
  });

  test("ignores invalid lastTown code and uses next fallback", async () => {
    localStorage.setItem("trip-weather-planner:last-town:v1", "defunct-code");
    const fetchMock = forecastFetch(liveForecastBody);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=taipei-xinyi");
    });
  });

  test("corrupt localStorage favorites does not crash the app", async () => {
    localStorage.setItem("trip-weather-planner:favorites:v1", "{{invalid}}");
    const fetchMock = forecastFetch(liveForecastBody);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(firstForecastUrl(fetchMock)).toContain("town=taipei-xinyi");
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

// ── AC1: TripForm sync with FavoriteTowns ─────────────────────────────────────

describe("App — TripForm and FavoriteTowns sync (AC1)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  test("clicking a favorite chip syncs TripForm city and townCode selects", async () => {
    const user = userEvent.setup();
    localStorage.setItem(
      "trip-weather-planner:favorites:v1",
      JSON.stringify(["hualien-hualien"]),
    );

    let forecastCount = 0;
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      forecastCount += 1;
      return Promise.resolve(
        jsonResponse(forecastCount === 1 ? liveForecastBody : otherTownForecastBody),
      );
    }));

    render(<App />);
    await screen.findByText("7/4 留意午後陣雨。");

    await user.click(screen.getByRole("button", { name: /花蓮市/ }));

    await waitFor(() => {
      const citySelect = screen.getByLabelText("縣市") as HTMLSelectElement;
      expect(citySelect.value).toBe("花蓮縣");
      const townSelect = screen.getByLabelText("鄉鎮市區") as HTMLSelectElement;
      expect(townSelect.value).toBe("hualien-hualien");
    });
  });
});

// ── AC4: Date preservation and lastTown write ─────────────────────────────────

describe("App — date preservation and lastTown write (AC4)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  test("form submit preserves the currently viewed date (not reset to today)", async () => {
    const user = userEvent.setup();
    let count = 0;
    const fetchMock = vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      count += 1;
      if (count === 1) return Promise.resolve(jsonResponse(liveForecastBody));
      if (count === 2) return Promise.resolve(jsonResponse(nextDayForecastBody));
      return Promise.resolve(jsonResponse(otherTownForecastBody));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByText("7/4 留意午後陣雨。");

    // Navigate to 7/5
    await user.click(screen.getByRole("button", { name: /7\/5/ }));
    await screen.findByText("7/5 白天炎熱，記得補水。");

    // Submit form for different town — should preserve date 2026-07-05
    await user.selectOptions(screen.getByLabelText("縣市"), "花蓮縣");
    await user.selectOptions(screen.getByLabelText("鄉鎮市區"), "hualien-hualien");
    await user.click(screen.getByRole("button", { name: "查詢天氣" }));

    const forecastUrls = fetchMock.mock.calls
      .map((args: unknown[]) => String(args[0]))
      .filter((u: string) => u.includes("/api/forecast"));
    expect(forecastUrls[2]).toContain("date=2026-07-05");
    expect(forecastUrls[2]).toContain("town=hualien-hualien");
  });

  test("favorite chip click preserves currently viewed date", async () => {
    const user = userEvent.setup();
    localStorage.setItem(
      "trip-weather-planner:favorites:v1",
      JSON.stringify(["hualien-hualien"]),
    );
    let count = 0;
    const fetchMock = vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      count += 1;
      if (count === 1) return Promise.resolve(jsonResponse(liveForecastBody));
      if (count === 2) return Promise.resolve(jsonResponse(nextDayForecastBody));
      return Promise.resolve(jsonResponse(otherTownForecastBody));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByText("7/4 留意午後陣雨。");

    // Navigate to 7/5
    await user.click(screen.getByRole("button", { name: /7\/5/ }));
    await screen.findByText("7/5 白天炎熱，記得補水。");

    // Click favorite chip — should preserve date 2026-07-05
    await user.click(screen.getByRole("button", { name: /花蓮市/ }));

    const forecastUrls = fetchMock.mock.calls
      .map((args: unknown[]) => String(args[0]))
      .filter((u: string) => u.includes("/api/forecast"));
    expect(forecastUrls[2]).toContain("date=2026-07-05");
    expect(forecastUrls[2]).toContain("town=hualien-hualien");
  });

  test("writes lastTown to localStorage after a successful query", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      return Promise.resolve(jsonResponse(liveForecastBody));
    }));

    render(<App />);

    await screen.findByText("7/4 留意午後陣雨。");
    expect(localStorage.getItem("trip-weather-planner:last-town:v1")).toBe("taipei-xinyi");
  });

  test("does NOT write lastTown when the query fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) return Promise.resolve(jsonResponse(townsBody));
      return Promise.resolve(jsonResponse(validationErrorBody, false, 400));
    }));

    render(<App />);

    await screen.findByRole("alert");
    expect(localStorage.getItem("trip-weather-planner:last-town:v1")).toBeNull();
  });
});

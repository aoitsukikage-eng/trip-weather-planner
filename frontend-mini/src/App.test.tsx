import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { Forecast, Town } from "./lib/domain";

const api = vi.hoisted(() => ({ getTowns: vi.fn(), getForecast: vi.fn() }));
const dates = ["2026-07-31", "2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06"];
vi.mock("./lib/api", () => ({
  getTowns: api.getTowns,
  getForecast: api.getForecast,
  RequestError: class RequestError extends Error {},
}));
vi.mock("./lib/date", () => ({ taipeiToday: () => "2026-07-31", untilNextTaipeiMidnight: () => 3600000, nextDays: () => dates }));

const towns: Town[] = [
  { code: "taipei-xinyi", city: "臺北市", name: "信義區", lat: 25.03, lon: 121.57 },
  { code: "tainan-west-central", city: "臺南市", name: "中西區", lat: 22.99, lon: 120.2 },
];
const forecast = (town = towns[0], overrides: Partial<Forecast["forecast"]> = {}): Forecast => ({
  forecast: {
    town,
    target_date: "2026-07-31",
    source_dataset: "live:cwa",
    generated_at: "2026-07-31T08:00:00+08:00",
    days: dates.map((date, index) => ({ date, weather: index === 0 ? "晴朗" : "多雲", temp_low_c: 25 + index, temp_high_c: 31 + index, max_pop_percent: 20 + index, advice_hint: "帶水出門" })),
    aqi: { value: 42, level: "良好", source_label: "環境部" },
    warnings: [],
    ...overrides,
  },
  ai_summary: { text: "適合安排戶外行程", mode: "live" },
});
const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
};

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.clearAllMocks();
  history.replaceState({}, "", "/");
});

describe("Mini UI", () => {
  it("shows deterministic Demo Data, CTA and seven days", () => {
    history.replaceState({}, "", "/?demo=1");
    render(<App />);
    expect(screen.getByText("Demo")).toBeTruthy();
    expect(screen.getByText(/Open Full Planner/).getAttribute("rel")).toBe("noopener noreferrer");
    expect(screen.getAllByText(/晴時多雲|午後短暫雨/).length).toBeGreaterThan(1);
  });

  it("shows safe error actions", async () => {
    api.getTowns.mockRejectedValue(new TypeError("offline"));
    render(<App />);
    expect(await screen.findByText("暫時無法取得預報")).toBeTruthy();
    expect(screen.getByText("Use Demo Data")).toBeTruthy();
  });

  it("keeps the newest town result when an older request resolves late", async () => {
    const first = deferred<Forecast>();
    const second = deferred<Forecast>();
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise);
    render(<App />);
    const select = await screen.findByLabelText("縣市／鄉鎮");
    fireEvent.change(select, { target: { value: towns[1].code } });
    expect(api.getForecast).toHaveBeenNthCalledWith(1, towns[0].code, "2026-07-31", expect.any(AbortSignal));
    expect(api.getForecast).toHaveBeenNthCalledWith(2, towns[1].code, "2026-07-31", expect.any(AbortSignal));

    await act(async () => { second.resolve(forecast(towns[1])); });
    await act(async () => { first.resolve(forecast(towns[0])); });
    expect(await screen.findByText("臺南市 · 中西區")).toBeTruthy();
    expect(screen.queryByText("臺北市 · 信義區")).toBeNull();
  });

  it("maps a live success response into weather, metrics, strip and provenance", async () => {
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast());
    render(<App />);
    expect((await screen.findAllByText("晴朗")).length).toBeGreaterThan(1);
    expect(screen.getByText("25° / 31°")).toBeTruthy();
    expect(screen.getByText("降雨 20%")).toBeTruthy();
    expect(screen.getByText("08-06")).toBeTruthy();
    expect(screen.getByText(/Last updated: 2026-07-31T08:00:00\+08:00 · source: live:cwa/)).toBeTruthy();
    expect(screen.queryByText("Demo Data")).toBeNull();
  });

  it("keeps warning and AQI as separate signals", async () => {
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast(towns[0], { warnings: [{ title: "大雨特報", severity: "yellow" }] }));
    render(<App />);
    expect(await screen.findByText("⚠ 1 則警特報：大雨特報")).toBeTruthy();
    expect(screen.getByText("AQI 42 · 良好")).toBeTruthy();
  });

  it("shows AQI when there are no warnings", async () => {
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast());
    render(<App />);
    expect(await screen.findByText("AQI 42 · 良好")).toBeTruthy();
  });

  it("shows loading then cold-start messaging and skeleton for a pending forecast", async () => {
    vi.useFakeTimers();
    const pending = deferred<Forecast>();
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockReturnValue(pending.promise);
    render(<App />);
    await act(async () => {});
    expect(screen.getByText("正在取得天氣…")).toBeTruthy();
    expect(screen.getByLabelText("載入中")).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(2500); });
    expect(screen.getByText("服務可能正在喚醒，請稍候…")).toBeTruthy();
    expect(screen.getByLabelText("載入中")).toBeTruthy();
    await act(async () => { pending.resolve(forecast()); });
  });

  it("shows the empty recovery UI when the target date is absent", async () => {
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast(towns[0], { days: [{ date: "2026-08-01", weather: "多雲", temp_low_c: 25, temp_high_c: 30, max_pop_percent: 20 }] }));
    render(<App />);
    expect(await screen.findByText("目前沒有可顯示的預報")).toBeTruthy();
    expect(screen.getByText("Retry Live Data")).toBeTruthy();
    expect(screen.getByText("Use Demo Data")).toBeTruthy();
  });

  it("renders compact mode with its compact selector, weather icon and production CTA", () => {
    history.replaceState({}, "", "/?view=compact&demo=1");
    render(<App />);
    expect(screen.getByLabelText("縣市／鄉鎮").closest(".weather-card")).toBeTruthy();
    expect(screen.queryByText("臺北市 · 信義區")).toBeNull();
    expect(screen.queryByLabelText("未來七日預報")).toBeNull();
    expect(screen.getByText("UV 7 · 過量級")).toBeTruthy();
    expect(screen.getByTestId("compact-weather-icon").getAttribute("aria-label")).toBe("晴朗天氣圖示");
    const cta = screen.getByText(/查看完整天氣預覽/);
    expect(cta.getAttribute("href")).toBe("https://twpfe5ce0.z23.web.core.windows.net/");
    expect(cta.getAttribute("target")).toBe("_top");
  });

  it("maps rainy compact weather to the rain icon", async () => {
    history.replaceState({}, "", "/?view=compact");
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast(towns[0], { days: [{ date: "2026-07-31", weather: "午後短暫雨", temp_low_c: 25, temp_high_c: 30, max_pop_percent: 80 }] }));
    render(<App />);
    expect((await screen.findByTestId("compact-weather-icon")).getAttribute("aria-label")).toBe("雨天天氣圖示");
  });

  it("keeps the full strip, location eyebrow and CTA behavior outside compact mode", () => {
    history.replaceState({}, "", "/?demo=1");
    render(<App />);
    expect(screen.getByLabelText("未來七日預報")).toBeTruthy();
    expect(screen.getByText("臺北市 · 信義區")).toBeTruthy();
    const cta = screen.getByText(/Open Full Planner/);
    expect(cta.getAttribute("href")).toBe("https://twpfe5ce0.z23.web.core.windows.net/");
    expect(cta.getAttribute("target")).toBe("_blank");
  });

  it("shows warning, AQI and UV together in compact mode", async () => {
    history.replaceState({}, "", "/?view=compact");
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast(towns[0], { warnings: [{ title: "大雨特報", severity: "yellow" }], uv: { value: 8, level: "高量級", source_label: "CWA" } }));
    render(<App />);
    expect(await screen.findByText("⚠ 1 則警特報：大雨特報")).toBeTruthy();
    expect(screen.getByText("AQI 42 · 良好")).toBeTruthy();
    expect(screen.getByText("UV 8 · 高量級")).toBeTruthy();
  });

  it("omits a null UV signal safely", async () => {
    history.replaceState({}, "", "/?view=compact");
    api.getTowns.mockResolvedValue(towns);
    api.getForecast.mockResolvedValue(forecast(towns[0], { uv: null }));
    render(<App />);
    await screen.findByText("AQI 42 · 良好");
    expect(screen.queryByText(/^UV /)).toBeNull();
  });
});

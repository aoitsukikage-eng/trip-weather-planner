import { afterEach, describe, expect, test, vi } from "vitest";
import { getForecast, type Town } from "./api";

const TOWN: Town = {
  code: "taipei-xinyi",
  name: "信義區",
  city: "臺北市",
  lat: 25.03,
  lon: 121.57,
};

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 400): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

describe("getForecast", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  test("falls back to frontend mock only on network failure", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-05T10:00:00+08:00"));
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const result = await getForecast(TOWN, "2026-07-04");

    expect(result.forecast.source_dataset).toBe("mock:frontend-fallback");
    expect(result.forecast.target_date).toBe("2026-07-05");
  });

  test("surfaces backend validation errors instead of masking them with mock data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            success: false,
            data: null,
            error: {
              error_code: "date_out_of_range",
              message: "Date must be within today..today+6.",
            },
            meta: { request_id: "req-1", cached: false, source: null },
          },
          false,
          400,
        ),
      ),
    );

    await expect(getForecast(TOWN, "2026-07-20")).rejects.toMatchObject({
      message: "Date must be within today..today+6.",
      errorCode: "date_out_of_range",
      status: 400,
    });
  });

  test("anchors frontend mock days at today and clamps out-of-window requests", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-05T10:00:00+08:00"));
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const result = await getForecast(TOWN, "2026-07-20");

    expect(result.forecast.days.map((day) => day.date)).toEqual([
      "2026-07-05",
      "2026-07-06",
      "2026-07-07",
      "2026-07-08",
      "2026-07-09",
      "2026-07-10",
      "2026-07-11",
    ]);
    expect(result.forecast.target_date).toBe("2026-07-11");
    expect(result.forecast.sunrise_sunset?.target_date).toBe("2026-07-11");
    expect(result.forecast.hourly?.[0]?.time.startsWith("2026-07-11T00:00:00")).toBe(true);
  });
});

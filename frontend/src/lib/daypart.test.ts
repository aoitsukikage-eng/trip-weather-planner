import { describe, expect, test } from "vitest";
import { resolveDaypart, taipeiMinutesOfDay } from "./daypart";
import type { SunriseSunset } from "./api";

function sunriseSunset(sunrise: string | null, sunset: string | null): SunriseSunset {
  return {
    county: "臺北市",
    target_date: "2026-07-04",
    source_date: "2026-07-04",
    sunrise_time: sunrise,
    sunset_time: sunset,
    is_approximate: false,
  };
}

describe("taipeiMinutesOfDay", () => {
  test("reads the Asia/Taipei clock regardless of the runner's timezone", () => {
    expect(taipeiMinutesOfDay(new Date("2026-07-04T04:00:00Z"))).toBe(12 * 60);
  });
});

describe("resolveDaypart", () => {
  const sun = sunriseSunset("05:12", "18:46");

  test("is night before sunrise", () => {
    expect(resolveDaypart(sun, new Date("2026-07-03T21:00:00Z"))).toBe("night"); // 05:00 Taipei
  });

  test("is day right at sunrise", () => {
    expect(resolveDaypart(sun, new Date("2026-07-03T21:12:00Z"))).toBe("day"); // 05:12 Taipei
  });

  test("is day at midday", () => {
    expect(resolveDaypart(sun, new Date("2026-07-04T04:00:00Z"))).toBe("day"); // 12:00 Taipei
  });

  test("is night right at sunset", () => {
    expect(resolveDaypart(sun, new Date("2026-07-04T10:46:00Z"))).toBe("night"); // 18:46 Taipei
  });

  test("is night after sunset", () => {
    expect(resolveDaypart(sun, new Date("2026-07-04T11:00:00Z"))).toBe("night"); // 19:00 Taipei
  });

  test("falls back to a fixed 06:00–18:00 window when sunrise/sunset is missing", () => {
    expect(resolveDaypart(null, new Date("2026-07-03T21:00:00Z"))).toBe("night"); // 05:00 Taipei
    expect(resolveDaypart(null, new Date("2026-07-04T04:00:00Z"))).toBe("day"); // 12:00 Taipei
    expect(resolveDaypart(null, new Date("2026-07-04T10:00:00Z"))).toBe("night"); // 18:00 Taipei
  });

  test("falls back to the fixed window when the times fail to parse", () => {
    const malformed = sunriseSunset(null, "not-a-time");
    expect(resolveDaypart(malformed, new Date("2026-07-04T04:00:00Z"))).toBe("day"); // 12:00 Taipei
  });
});

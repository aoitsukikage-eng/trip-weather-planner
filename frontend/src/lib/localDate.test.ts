import { describe, expect, test } from "vitest";
import {
  buildDateOptions,
  formatLocalDate,
  millisecondsUntilNextTaipeiDay,
  taipeiIsoDate,
} from "./localDate";

describe("localDate helpers", () => {
  test("formatLocalDate keeps the local calendar day before 08:00 in UTC+8", () => {
    const earlyMorning = new Date(2026, 6, 4, 1, 17, 0);

    expect(formatLocalDate(earlyMorning)).toBe("2026-07-04");
  });

  test("buildDateOptions advances by local calendar days", () => {
    const base = new Date(2026, 6, 4, 1, 17, 0);

    expect(buildDateOptions(3, base).map((option) => option.iso)).toEqual([
      "2026-07-04",
      "2026-07-05",
      "2026-07-06",
    ]);
  });

  test("anchors today to Asia/Taipei instead of the browser timezone", () => {
    expect(taipeiIsoDate(new Date("2026-07-04T15:59:00Z"))).toBe("2026-07-04");
    expect(taipeiIsoDate(new Date("2026-07-04T16:00:00Z"))).toBe("2026-07-05");
  });

  test("calculates the next Asia/Taipei midnight boundary", () => {
    expect(millisecondsUntilNextTaipeiDay(new Date("2026-07-04T15:59:00Z"))).toBe(60_000);
  });
});

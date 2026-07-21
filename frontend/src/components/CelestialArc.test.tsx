import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import CelestialArc, { getArcProgress } from "./CelestialArc";

describe("getArcProgress", () => {
  test("calculates a progress fraction during a same-day rise/set window", () => {
    expect(getArcProgress("06:00", "18:00", "2026-07-04", new Date("2026-07-04T12:00:00"))).toBe(0.5);
  });

  test("handles moonset after midnight without a negative progress value", () => {
    const progress = getArcProgress("18:42", "05:11", "2026-07-04", new Date("2026-07-04T23:00:00"));

    expect(progress).not.toBeNull();
    expect(progress).toBeGreaterThan(0);
    expect(progress).toBeLessThan(1);
  });

  test("hides the marker for another date or outside the rise/set window", () => {
    const now = new Date("2026-07-04T12:00:00");
    const { rerender } = render(<CelestialArc label="sun" riseTime="06:00" setTime="18:00" targetDate="2026-07-05" now={now} />);

    expect(screen.queryByTestId("sun-arc-marker")).toBeNull();

    rerender(<CelestialArc label="sun" riseTime="06:00" setTime="18:00" targetDate="2026-07-04" now={new Date("2026-07-04T03:00:00")} />);
    expect(screen.queryByTestId("sun-arc-marker")).toBeNull();
  });
});

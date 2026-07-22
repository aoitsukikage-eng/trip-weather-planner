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

  test("renders a same-hue track and traveled segment only while the marker is valid", () => {
    const { rerender } = render(<CelestialArc label="sun" riseTime="06:00" setTime="18:00" targetDate="2026-07-04" now={new Date("2026-07-04T12:00:00")} />);
    const sunArc = screen.getAllByTestId("sun-arc").slice(-1)[0];
    const sunTrack = screen.getAllByTestId("sun-arc-track").slice(-1)[0];
    const sunTraveled = screen.getAllByTestId("sun-arc-traveled").slice(-1)[0];

    expect(sunArc?.getAttribute("class")).toContain("celestial-arc-sun");
    expect(sunTrack).not.toBeNull();
    expect(sunTraveled?.getAttribute("stroke-dasharray")).toBe("0.5 1");
    expect(screen.getAllByText("06:00").slice(-1)[0]).not.toBeNull();
    expect(screen.getAllByText("18:00").slice(-1)[0]).not.toBeNull();

    rerender(<CelestialArc label="moon" riseTime="18:42" setTime="05:11" targetDate="2026-07-05" now={new Date("2026-07-04T23:00:00")} />);
    expect(screen.getByTestId("moon-arc").getAttribute("class")).toContain("celestial-arc-moon");
    expect(screen.queryByTestId("moon-arc-traveled")).toBeNull();
  });

  test("renders a gradient-shaded moon phase marker at a larger radius", () => {
    const { rerender } = render(
      <CelestialArc
        label="moon"
        riseTime="06:00"
        setTime="18:00"
        targetDate="2026-07-04"
        now={new Date("2026-07-04T12:00:00")}
        illuminationFraction={0.02}
        waxing
        phaseName="新月"
      />,
    );
    const marker = screen.getByTestId("moon-arc-marker");
    const newMoonPath = screen.getByTestId("moon-phase-terminator").getAttribute("d");

    expect(marker.getAttribute("data-illumination")).toBe("0.020");
    expect(marker.getAttribute("data-waxing")).toBe("true");
    expect(screen.getByTestId("moon-phase-gradient").tagName).toBe("linearGradient");
    expect(screen.getByTestId("moon-phase-terminator").getAttribute("fill")).toContain("url(#moon-terminator-waxing-20)");
    expect(marker.querySelector(".celestial-moon-shadow")?.getAttribute("r")).toBe("12");

    rerender(
      <CelestialArc
        label="moon"
        riseTime="06:00"
        setTime="18:00"
        targetDate="2026-07-04"
        now={new Date("2026-07-04T12:00:00")}
        illuminationFraction={0.5}
        waxing
      />,
    );
    expect(screen.getByTestId("moon-phase-terminator").getAttribute("d")).not.toBe(newMoonPath);

    rerender(
      <CelestialArc
        label="moon"
        riseTime="06:00"
        setTime="18:00"
        targetDate="2026-07-04"
        now={new Date("2026-07-04T12:00:00")}
        illuminationFraction={0.98}
        waxing={false}
      />,
    );
    expect(screen.getByTestId("moon-arc-marker").getAttribute("data-waxing")).toBe("false");
    expect(screen.getByTestId("moon-phase-terminator").getAttribute("d")).not.toBe(newMoonPath);
  });

  test("keeps the sun marker as the original plain 4.5-radius circle without phase props", () => {
    render(
      <CelestialArc
        label="sun"
        riseTime="06:00"
        setTime="18:00"
        targetDate="2026-07-04"
        now={new Date("2026-07-04T12:00:00")}
      />,
    );

    const marker = screen.getByTestId("sun-arc-marker");
    expect(marker.tagName).toBe("circle");
    expect(marker.getAttribute("class")).toBe("celestial-position");
    expect(marker.getAttribute("r")).toBe("4.5");
    expect(marker.parentElement?.querySelector("[data-testid='moon-phase-gradient']")).toBeNull();
  });
});

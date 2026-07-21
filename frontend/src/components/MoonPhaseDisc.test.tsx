import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import MoonPhaseDisc from "./MoonPhaseDisc";

describe("MoonPhaseDisc", () => {
  test("renders distinct shading attributes for illumination levels and directions", () => {
    const { rerender } = render(<MoonPhaseDisc illuminationFraction={0.02} waxing phase="新月" />);
    const disc = screen.getByTestId("moon-phase-disc");
    const newMoonPath = screen.getByTestId("moon-phase-light").getAttribute("d");

    expect(disc.getAttribute("data-illumination")).toBe("0.020");
    expect(disc.getAttribute("data-waxing")).toBe("true");

    rerender(<MoonPhaseDisc illuminationFraction={0.5} waxing phase="上弦月" />);
    expect(screen.getByTestId("moon-phase-light").getAttribute("d")).not.toBe(newMoonPath);

    rerender(<MoonPhaseDisc illuminationFraction={0.98} waxing={false} phase="滿月" />);
    expect(disc.getAttribute("data-illumination")).toBe("0.980");
    expect(disc.getAttribute("data-waxing")).toBe("false");
    expect(screen.getByTestId("moon-phase-light").getAttribute("d")).not.toBe(newMoonPath);
  });
});

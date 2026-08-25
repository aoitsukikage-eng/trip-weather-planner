import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";
import StatusGauge, { getSeverityTier } from "./StatusGauge";

describe("StatusGauge bilingual & severity tier tests", () => {
  afterEach(() => {
    cleanup();
  });

  test("(a) extreme/hazardous level_code renders severe/hazard tier and NOT 'good'", () => {
    expect(getSeverityTier("uv", "extreme")).toBe("hazard");
    expect(getSeverityTier("aqi", "hazardous")).toBe("hazard");
    expect(getSeverityTier("uv", "very_high")).toBe("severe");

    const { getByTestId: getUvGauge } = render(
      <StatusGauge
        kind="uv"
        label="Current UV Index"
        value={11}
        level="Extreme"
        levelCode="extreme"
        maximum={14}
        detail="Observation"
      />,
    );

    const uvGauge = getUvGauge("uv-gauge");
    const uvCard = uvGauge.closest(".status-gauge-card");
    expect(uvCard?.getAttribute("data-severity")).toBe("hazard");
    expect(uvCard?.getAttribute("data-severity")).not.toBe("good");

    const { getByTestId: getAqiGauge } = render(
      <StatusGauge
        kind="aqi"
        label="Current Air Quality"
        value={350}
        level="Hazardous"
        levelCode="hazardous"
        maximum={300}
        detail="Observation"
      />,
    );

    const aqiGauge = getAqiGauge("aqi-gauge");
    const aqiCard = aqiGauge.closest(".status-gauge-card");
    expect(aqiCard?.getAttribute("data-severity")).toBe("hazard");
    expect(aqiCard?.getAttribute("data-severity")).not.toBe("good");
  });

  test("(b) unrecognised or null level_code renders 'unknown' tier and NOT 'good'", () => {
    expect(getSeverityTier("uv", null, null)).toBe("unknown");
    expect(getSeverityTier("aqi", "unmapped_gov_variant", null)).toBe("unknown");

    const { getByTestId } = render(
      <StatusGauge
        kind="uv"
        label="Current UV Index"
        value={null}
        level={null}
        levelCode={null}
        maximum={14}
        detail="Observation"
      />,
    );

    const gauge = getByTestId("uv-gauge");
    const card = gauge.closest(".status-gauge-card");
    expect(card?.getAttribute("data-severity")).toBe("unknown");
    expect(card?.getAttribute("data-severity")).not.toBe("good");
  });
});

import { useState } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, test } from "vitest";
import ForecastView, { getHourlyAnnotationStep } from "./ForecastView";
import type { ForecastResult, HourlyForecast } from "../lib/api";

function buildHourly(count: number): HourlyForecast[] {
  const start = new Date("2026-07-04T00:00:00+08:00");
  return Array.from({ length: count }, (_, index) => {
    const current = new Date(start);
    current.setHours(current.getHours() + index * 3);
    return {
      time: current.toISOString(),
      temp_c: 27 + (index % 3),
      apparent_temp_c: 29 + (index % 3),
      pop_percent: (index * 10) % 100,
      weather: index % 2 === 0 ? "晴時多雲" : "多雲",
      weather_code: index % 2 === 0 ? "01" : "04",
    };
  });
}

function buildResult(
  city: string,
  town: string,
  hourly: HourlyForecast[] = buildHourly(6),
  dayOverrides: Partial<ForecastResult["forecast"]["days"][number]>[] = [],
): ForecastResult {
  const dates = [
    "2026-07-04",
    "2026-07-05",
    "2026-07-06",
    "2026-07-07",
    "2026-07-08",
    "2026-07-09",
    "2026-07-10",
  ];

  return {
    forecast: {
      town: {
        code: `${city}-${town}`,
        city,
        name: town,
        lat: 25.0,
        lon: 121.5,
      },
      target_date: "2026-07-04",
      source_dataset: "cwa-live",
      days: dates.map((date, index) => ({
        date,
        temp_high_c: 32 - (index % 3),
        temp_low_c: 25 - (index % 2),
        max_pop_percent: 20 + index * 10,
        weather: index % 2 === 0 ? "多雲" : "晴時多雲",
        advice_hint: index % 2 === 0 ? "帶傘。" : "適合輕鬆出遊。",
        ...dayOverrides[index],
      })),
      hourly,
      sunrise_sunset: {
        county: city,
        target_date: "2026-07-04",
        source_date: "2026-06-29",
        sunrise_time: "05:12",
        sunset_time: "18:48",
        is_approximate: true,
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
      text: "test summary",
      mode: "rule-based",
    },
  };
}

describe("ForecastView", () => {
  afterEach(() => {
    cleanup();
  });

  test("shows the queried place in the chart section and updates on rerender", () => {
    const { rerender } = render(<ForecastView result={buildResult("新北市", "貢寮區")} />);

    expect(screen.getByText("新北市 貢寮區")).not.toBeNull();

    rerender(<ForecastView result={buildResult("臺北市", "信義區")} />);

    expect(screen.getByText("臺北市 信義區")).not.toBeNull();
    expect(screen.queryByText("新北市 貢寮區")).toBeNull();
  });

  test("shows selected sunrise date and centered chart place label", () => {
    render(<ForecastView result={buildResult("臺北市", "信義區")} />);

    expect(screen.getByText(/7\/4（六） 日出 05:12 · 日落 18:48/)).not.toBeNull();
    expect(screen.getByText(/參考 2026-06-29 天文資料/)).not.toBeNull();
    expect(screen.getByTestId("chart-place").textContent).toBe("臺北市 信義區");
  });

  test("renders the day strip before advice and chart with seven compact cells", () => {
    const { container } = render(<ForecastView result={buildResult("臺北市", "信義區")} />);

    const result = container.querySelector(".result");
    const dayStripSection = container.querySelector(".day-strip-section");
    const summaryPanel = container.querySelector(".summary-panel");
    const factGrid = container.querySelector(".fact-grid");
    const hourlyChart = container.querySelector(".hourly-chart");
    const buttons = screen.getAllByRole("button");
    const firstButton = buttons[0];
    const firstCardHeader = container.querySelector(".day-strip-head");
    const dayStrip = screen.getByTestId("day-strip");

    expect(result).not.toBeNull();
    expect(dayStripSection).not.toBeNull();
    expect(summaryPanel).not.toBeNull();
    expect(factGrid).not.toBeNull();
    expect(hourlyChart).not.toBeNull();
    if (!dayStripSection || !summaryPanel || !factGrid || !hourlyChart) {
      throw new Error("expected layout sections to exist");
    }
    expect(screen.getByTestId("day-strip-scroll")).not.toBeNull();
    expect(dayStrip.getAttribute("data-layout")).toBe("single-row");
    expect(dayStrip.getAttribute("style")).toContain("--day-count: 7");
    expect(buttons).toHaveLength(7);
    expect(firstButton).toBeDefined();
    expect(firstCardHeader?.firstElementChild?.className).toContain("day-strip-icon");
    expect(firstButton?.textContent).toContain("7/4");
    expect(firstButton?.textContent).toContain("週六");
    expect(firstButton?.textContent).toContain("多雲");
    expect(firstButton?.textContent).toContain("高 32°");
    expect(firstButton?.textContent).toContain("低 25°");
    expect(firstButton?.textContent).toContain("降雨 20%");
    expect(firstButton?.textContent).not.toContain("帶傘");
    expect(firstButton?.getAttribute("aria-pressed")).toBe("true");
    expect(dayStripSection.compareDocumentPosition(summaryPanel) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    expect(summaryPanel.compareDocumentPosition(factGrid) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    expect(factGrid.compareDocumentPosition(hourlyChart) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
  });

  test("hides the rain row entirely when PoP is null", () => {
    render(
      <ForecastView
        result={buildResult("臺北市", "信義區", buildHourly(6), [{}, {}, {}, { max_pop_percent: null }])}
      />,
    );

    const fourthCard = screen.getByTestId("day-card-2026-07-07");

    expect(fourthCard.textContent).toContain("7/7");
    expect(fourthCard.textContent).not.toContain("降雨");
    expect(fourthCard.querySelector(".day-strip-pop")).toBeNull();
    expect(fourthCard.getAttribute("aria-label")).not.toContain("降雨");
  });

  test("keeps click and keyboard selection interactions in place", async () => {
    function Harness() {
      const [targetDate, setTargetDate] = useState("2026-07-04");
      const result = buildResult("臺北市", "信義區");
      return (
        <ForecastView
          onSelectDate={setTargetDate}
          result={{
            ...result,
            forecast: {
              ...result.forecast,
              target_date: targetDate,
            },
            ai_summary: {
              ...result.ai_summary,
              text: `summary for ${targetDate}`,
            },
          }}
        />
      );
    }

    const user = userEvent.setup();
    render(<Harness />);

    const secondCard = screen.getByTestId("day-card-2026-07-05");
    const thirdCard = screen.getByTestId("day-card-2026-07-06");

    await user.click(secondCard);
    expect(secondCard.getAttribute("aria-pressed")).toBe("true");
    expect(secondCard).toBe(document.activeElement);
    expect(screen.getByText("summary for 2026-07-05")).not.toBeNull();
    expect(screen.getByText(/7\/5（日） 日出 05:12 · 日落 18:48/)).not.toBeNull();

    thirdCard.focus();
    await user.keyboard("{Enter}");
    expect(thirdCard.getAttribute("aria-pressed")).toBe("true");
    expect(thirdCard).toBe(document.activeElement);
    expect(screen.getByText("summary for 2026-07-06")).not.toBeNull();
    expect(screen.getByText(/7\/6（一） 日出 05:12 · 日落 18:48/)).not.toBeNull();
  });

  test("thins hourly annotations when the chart gets too dense", () => {
    render(<ForecastView result={buildResult("新北市", "貢寮區", buildHourly(24))} />);

    const labels = screen.getAllByTestId("hourly-time-label");
    expect(labels.length).toBeLessThan(24);
    expect(labels.length).toBe(13);
  });
});

describe("getHourlyAnnotationStep", () => {
  test("returns a larger step when spacing is too tight", () => {
    expect(getHourlyAnnotationStep(24, 890)).toBe(2);
    expect(getHourlyAnnotationStep(8, 890)).toBe(1);
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import TripForm from "./TripForm";
import type { Town } from "../lib/api";

const TOWNS: Town[] = [
  { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  { code: "taipei-daan", name: "大安區", city: "臺北市", lat: 25.03, lon: 121.54 },
];

describe("TripForm", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 4, 1, 17, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("submits the same local date as the clicked chip", async () => {
    const onSubmit = vi.fn();

    render(<TripForm towns={TOWNS} loading={false} onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole("button", { name: "7/5（日）" }));
    fireEvent.click(screen.getByRole("button", { name: "查詢天氣" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0]?.[1]).toBe("2026-07-05");
  });
});

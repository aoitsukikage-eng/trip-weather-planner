import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import TripForm from "./TripForm";
import type { Town } from "../lib/api";

const TOWNS: Town[] = [
  { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  { code: "taipei-daan", name: "大安區", city: "臺北市", lat: 25.03, lon: 121.54 },
];

describe("TripForm", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  test("submits with the selected region only", async () => {
    const onSubmit = vi.fn();

    render(<TripForm towns={TOWNS} loading={false} onSubmit={onSubmit} />);

    expect(screen.queryByLabelText("旅遊日期")).toBeNull();
    fireEvent.change(screen.getByLabelText("鄉鎮市區"), { target: { value: "taipei-daan" } });
    fireEvent.click(screen.getByRole("button", { name: "查詢天氣" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ code: "taipei-daan" });
  });
});

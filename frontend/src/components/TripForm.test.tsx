import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { useState } from "react";
import TripForm from "./TripForm";
import type { Town } from "../lib/api";

const TOWNS: Town[] = [
  { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  { code: "taipei-daan", name: "大安區", city: "臺北市", lat: 25.03, lon: 121.54 },
];

function ControlledTripForm({
  onSubmit,
  loading = false,
}: {
  onSubmit: ReturnType<typeof vi.fn>;
  loading?: boolean;
}) {
  const [city, setCity] = useState(TOWNS[0].city);
  const [townCode, setTownCode] = useState(TOWNS[0].code);
  return (
    <TripForm
      towns={TOWNS}
      loading={loading}
      city={city}
      townCode={townCode}
      onCityChange={setCity}
      onTownCodeChange={setTownCode}
      onSubmit={onSubmit}
    />
  );
}

describe("TripForm", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  test("submits with the selected region only", async () => {
    const onSubmit = vi.fn();

    render(<ControlledTripForm onSubmit={onSubmit} />);

    expect(screen.queryByLabelText("旅遊日期")).toBeNull();
    fireEvent.change(screen.getByLabelText("鄉鎮市區"), { target: { value: "taipei-daan" } });
    fireEvent.click(screen.getByRole("button", { name: "查詢天氣" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ code: "taipei-daan" });
  });

  test("submit button is disabled while loading", () => {
    const onSubmit = vi.fn();
    render(<ControlledTripForm onSubmit={onSubmit} loading={true} />);
    expect((screen.getByRole("button", { name: "查詢中…" }) as HTMLButtonElement).disabled).toBe(true);
  });
});

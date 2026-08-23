import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { useState } from "react";
import TripForm from "./TripForm";
import type { Town } from "../lib/api";
import { LocaleContext } from "../lib/locale";
import { getDictionary } from "../i18n";

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

  test("(d) TripForm in en renders English town/city names and uses en collation", () => {
    const enTowns: Town[] = [
      {
        code: "town-b",
        name: "乙鎮",
        city: "甲市",
        name_en: "Banana Town",
        city_en: "Apple City",
        lat: 25.0,
        lon: 121.5,
      },
      {
        code: "town-a",
        name: "甲鎮",
        city: "甲市",
        name_en: "Apple Town",
        city_en: "Apple City",
        lat: 25.0,
        lon: 121.5,
      },
    ];

    render(
      <LocaleContext.Provider value={{ locale: "en", setLocale: vi.fn(), t: getDictionary("en") }}>
        <TripForm
          towns={enTowns}
          loading={false}
          city="甲市"
          townCode="town-b"
          onCityChange={vi.fn()}
          onTownCodeChange={vi.fn()}
          onSubmit={vi.fn()}
        />
      </LocaleContext.Provider>,
    );

    const cityOption = screen.getByRole("option", { name: "Apple City" });
    expect(cityOption).not.toBeNull();

    const townOptions = screen.getAllByRole("option").filter((opt) => (opt as HTMLOptionElement).value.startsWith("town-"));
    const optionTexts = townOptions.map((opt) => opt.textContent);

    expect(optionTexts).toEqual(["Apple Town", "Banana Town"]);
  });
});

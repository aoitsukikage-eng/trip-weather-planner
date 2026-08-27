import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { getDictionary, isSupportedLocale, LOCALE_NAMES, SUPPORTED_LOCALES } from "../i18n";
import { LocaleProvider, useLocale } from "./locale";

function TestConsumer() {
  const { locale, setLocale, t } = useLocale();
  return (
    <div>
      <span data-testid="current-locale">{locale}</span>
      <span data-testid="app-title">{t.appTitle}</span>
      {SUPPORTED_LOCALES.map((loc) => (
        <button key={loc} type="button" onClick={() => setLocale(loc)}>
          {LOCALE_NAMES[loc]}
        </button>
      ))}
    </div>
  );
}

describe("locale context & provider", () => {
  const originalLocation = window.location.href;

  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState(null, "", "/");
  });

  afterEach(() => {
    cleanup();
    localStorage.clear();
    window.history.replaceState(null, "", originalLocation);
  });

  test("defaults to zh when query param and localStorage are empty", () => {
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("zh");
    expect(screen.getByTestId("app-title").textContent).toBe("旅遊行前天氣規劃");
  });

  test("initializes from ?lang= query param if valid", () => {
    window.history.replaceState(null, "", "/?lang=en");
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("en");
    expect(screen.getByTestId("app-title").textContent).toBe("Trip Weather Planner");
  });

  test("initializes from localStorage if query param is absent", () => {
    localStorage.setItem("twp:locale", "en");
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("en");
  });

  test("query param overrides localStorage", () => {
    localStorage.setItem("twp:locale", "zh");
    window.history.replaceState(null, "", "/?lang=en");
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("en");
  });

  test("switches locale, updates localStorage, and updates URL query string", async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByTestId("current-locale").textContent).toBe("zh");

    await user.click(screen.getByRole("button", { name: "English" }));

    expect(screen.getByTestId("current-locale").textContent).toBe("en");
    expect(screen.getByTestId("app-title").textContent).toBe("Trip Weather Planner");
    expect(localStorage.getItem("twp:locale")).toBe("en");
    expect(window.location.search).toContain("lang=en");
  });

  test("formats dates and weekdays in Japanese (AC2)", () => {
    const jaDict = getDictionary("ja");
    expect(jaDict.weekdaysShort).toEqual(["日", "月", "火", "水", "木", "金", "土"]);
    expect(jaDict.formatWeekday("月")).toBe("月曜日");
    expect(jaDict.formatDate(8, 28, "月曜日")).toBe("8/28（月曜日）");
  });

  test("supports ja locale initialization and persistence (AC5)", async () => {
    const user = userEvent.setup();

    // isSupportedLocale check
    expect(isSupportedLocale("ja")).toBe(true);
    expect(isSupportedLocale("ko")).toBe(false);

    // Initializing from ?lang=ja query param
    window.history.replaceState(null, "", "/?lang=ja");
    const { unmount: unmount1 } = render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("ja");
    expect(screen.getByTestId("app-title").textContent).toBe("旅行お天気プランナー");
    unmount1();

    // Initializing from localStorage 'twp:locale' = 'ja'
    window.history.replaceState(null, "", "/");
    localStorage.setItem("twp:locale", "ja");
    const { unmount: unmount2 } = render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    expect(screen.getByTestId("current-locale").textContent).toBe("ja");
    unmount2();

    // Switching to Japanese updates localStorage and URL query string
    localStorage.clear();
    window.history.replaceState(null, "", "/");
    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole("button", { name: "日本語" }));
    expect(screen.getByTestId("current-locale").textContent).toBe("ja");
    expect(localStorage.getItem("twp:locale")).toBe("ja");
    expect(window.location.search).toContain("lang=ja");
  });
});

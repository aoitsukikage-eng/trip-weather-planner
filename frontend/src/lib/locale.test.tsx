import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { SUPPORTED_LOCALES } from "../i18n";
import { LocaleProvider, useLocale } from "./locale";

function TestConsumer() {
  const { locale, setLocale, t } = useLocale();
  const nextLocale = SUPPORTED_LOCALES[(SUPPORTED_LOCALES.indexOf(locale) + 1) % SUPPORTED_LOCALES.length];
  return (
    <div>
      <span data-testid="current-locale">{locale}</span>
      <span data-testid="app-title">{t.appTitle}</span>
      <button type="button" onClick={() => setLocale(nextLocale)}>
        {t.switchLangLabel}
      </button>
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

    await user.click(screen.getByRole("button", { name: "EN" }));

    expect(screen.getByTestId("current-locale").textContent).toBe("en");
    expect(screen.getByTestId("app-title").textContent).toBe("Trip Weather Planner");
    expect(localStorage.getItem("twp:locale")).toBe("en");
    expect(window.location.search).toContain("lang=en");
  });
});

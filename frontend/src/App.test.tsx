import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import App from "./App";

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 400): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

const townsBody = {
  success: true,
  data: [
    { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  ],
  error: null,
  meta: { request_id: "towns-1", cached: false, source: "mock" },
};

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("shows a visible error when the backend returns a validation error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      return Promise.resolve(
        jsonResponse(
          {
            success: false,
            data: null,
            error: {
              error_code: "date_out_of_range",
              message: "Date must be within today..today+6.",
            },
            meta: { request_id: "forecast-1", cached: false, source: null },
          },
          false,
          400,
        ),
      );
    }));

    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Date must be within today..today+6.");
    expect(screen.queryByText(/mock:frontend-fallback/)).toBeNull();
  });

  test("renders frontend mock fallback when the backend is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("/api/towns")) {
        return Promise.resolve(jsonResponse(townsBody));
      }
      return Promise.reject(new TypeError("Failed to fetch"));
    }));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/mock:frontend-fallback/)).not.toBeNull();
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

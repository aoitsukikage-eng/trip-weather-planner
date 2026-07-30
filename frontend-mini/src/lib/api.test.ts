import { afterEach, describe, expect, it, vi } from "vitest";
import { getForecast, getTowns, RequestError } from "./api";

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("API", () => {
  it("uses safe query and no-store", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ success: true, data: [], error: null, meta: {} })));
    await getTowns();
    expect(fetchMock).toHaveBeenCalledWith("/api/towns", expect.objectContaining({ cache: "no-store" }));
  });

  it("maps invalid envelope to response error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ success: false, data: null, error: { message: "bad" }, meta: {} }), { status: 400 }));
    await expect(getForecast("a b", "2026-07-30")).rejects.toBeInstanceOf(RequestError);
  });

  it("aborts the internal request at eight seconds and reports timeout", async () => {
    vi.useFakeTimers();
    let requestSignal: AbortSignal | undefined;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => new Promise((_resolve, reject) => {
      requestSignal = init?.signal as AbortSignal;
      requestSignal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
    }));

    const request = getForecast("taipei-xinyi", "2026-07-31");
    const timeout = expect(request).rejects.toMatchObject({ kind: "timeout" });
    await vi.advanceTimersByTimeAsync(8000);

    expect(requestSignal?.aborted).toBe(true);
    await timeout;
    expect(fetchMock).toHaveBeenCalledWith("/api/forecast?town=taipei-xinyi&date=2026-07-31", expect.objectContaining({ cache: "no-store", signal: requestSignal }));
  });

  it("propagates an external abort without misclassifying it as timeout", async () => {
    let requestSignal: AbortSignal | undefined;
    vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => new Promise((_resolve, reject) => {
      requestSignal = init?.signal as AbortSignal;
      requestSignal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
    }));
    const controller = new AbortController();
    const request = getTowns(controller.signal);
    controller.abort();

    expect(requestSignal?.aborted).toBe(true);
    await expect(request).rejects.toMatchObject({ kind: "network" });
  });
});

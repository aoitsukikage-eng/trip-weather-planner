import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import {
  STORAGE_KEYS,
  MAX_FAVORITES,
  getFavorites,
  addFavorite,
  removeFavorite,
  moveFavoriteForward,
  moveFavoriteBack,
  getDefaultTown,
  setDefaultTown,
  clearDefaultTown,
  getLastTown,
  setLastTown,
} from "./favoriteTowns";

type LocalStorageMock = {
  store: Record<string, string>;
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
  clear: () => void;
};

function makeLocalStorageMock(): LocalStorageMock {
  const store: Record<string, string> = {};
  return {
    store,
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      for (const k in store) delete store[k];
    },
  };
}

describe("favoriteTowns", () => {
  let ls: LocalStorageMock;

  beforeEach(() => {
    ls = makeLocalStorageMock();
    vi.stubGlobal("localStorage", ls);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // ── getFavorites ──────────────────────────────────────────────────────────

  describe("getFavorites", () => {
    test("returns empty array when nothing stored", () => {
      expect(getFavorites()).toEqual([]);
    });

    test("returns stored favorites", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["code-a", "code-b"]));
      expect(getFavorites()).toEqual(["code-a", "code-b"]);
    });

    test("returns empty array when JSON is corrupt", () => {
      ls.setItem(STORAGE_KEYS.favorites, "not-valid-json{{{");
      expect(getFavorites()).toEqual([]);
    });

    test("returns empty array when stored value is not an array", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify({ a: 1 }));
      expect(getFavorites()).toEqual([]);
    });

    test("filters out non-string entries from mixed array", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["code-a", 42, null, "code-b"]));
      expect(getFavorites()).toEqual(["code-a", "code-b"]);
    });

    test("does not crash when localStorage.getItem throws", () => {
      vi.stubGlobal("localStorage", {
        getItem: () => {
          throw new Error("storage unavailable");
        },
        setItem: () => {},
        removeItem: () => {},
      });
      expect(getFavorites()).toEqual([]);
    });
  });

  // ── addFavorite ───────────────────────────────────────────────────────────

  describe("addFavorite", () => {
    test("adds a code to an empty list", () => {
      expect(addFavorite("code-a")).toEqual(["code-a"]);
      expect(getFavorites()).toEqual(["code-a"]);
    });

    test("is a no-op for an existing code", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["code-a"]));
      const result = addFavorite("code-a");
      expect(result).toEqual(["code-a"]);
    });

    test("does not add beyond MAX_FAVORITES", () => {
      const full = Array.from({ length: MAX_FAVORITES }, (_, i) => `code-${i}`);
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(full));
      const result = addFavorite("code-new");
      expect(result).toHaveLength(MAX_FAVORITES);
      expect(result).not.toContain("code-new");
    });

    test("does not crash when localStorage.setItem throws", () => {
      vi.stubGlobal("localStorage", {
        getItem: () => null,
        setItem: () => {
          throw new Error("quota exceeded");
        },
        removeItem: () => {},
      });
      expect(() => addFavorite("code-a")).not.toThrow();
    });
  });

  // ── removeFavorite ────────────────────────────────────────────────────────

  describe("removeFavorite", () => {
    test("removes a code from the list", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b", "c"]));
      expect(removeFavorite("b")).toEqual(["a", "c"]);
      expect(getFavorites()).toEqual(["a", "c"]);
    });

    test("clears defaultTown from storage when removing the current default", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b"]));
      ls.setItem(STORAGE_KEYS.defaultTown, "b");
      removeFavorite("b");
      expect(getDefaultTown()).toBeNull();
    });

    test("does not clear defaultTown when removing a non-default town", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b"]));
      ls.setItem(STORAGE_KEYS.defaultTown, "a");
      removeFavorite("b");
      expect(getDefaultTown()).toBe("a");
    });

    test("is a no-op for a code not in the list", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b"]));
      expect(removeFavorite("x")).toEqual(["a", "b"]);
    });
  });

  // ── moveFavoriteForward ───────────────────────────────────────────────────

  describe("moveFavoriteForward", () => {
    test("moves code one position toward the front", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b", "c"]));
      expect(moveFavoriteForward("b")).toEqual(["b", "a", "c"]);
    });

    test("is a no-op when code is already at position 0", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b", "c"]));
      expect(moveFavoriteForward("a")).toEqual(["a", "b", "c"]);
    });

    test("is a no-op when code is not found", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b"]));
      expect(moveFavoriteForward("x")).toEqual(["a", "b"]);
    });
  });

  // ── moveFavoriteBack ──────────────────────────────────────────────────────

  describe("moveFavoriteBack", () => {
    test("moves code one position toward the end", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b", "c"]));
      expect(moveFavoriteBack("b")).toEqual(["a", "c", "b"]);
    });

    test("is a no-op when code is already at the last position", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b", "c"]));
      expect(moveFavoriteBack("c")).toEqual(["a", "b", "c"]);
    });

    test("is a no-op when code is not found", () => {
      ls.setItem(STORAGE_KEYS.favorites, JSON.stringify(["a", "b"]));
      expect(moveFavoriteBack("x")).toEqual(["a", "b"]);
    });
  });

  // ── defaultTown ───────────────────────────────────────────────────────────

  describe("defaultTown", () => {
    test("returns null when nothing stored", () => {
      expect(getDefaultTown()).toBeNull();
    });

    test("round-trips setDefaultTown / getDefaultTown", () => {
      setDefaultTown("taipei-xinyi");
      expect(getDefaultTown()).toBe("taipei-xinyi");
    });

    test("clearDefaultTown removes the stored value", () => {
      setDefaultTown("taipei-xinyi");
      clearDefaultTown();
      expect(getDefaultTown()).toBeNull();
    });

    test("does not crash when localStorage throws on setDefaultTown", () => {
      vi.stubGlobal("localStorage", {
        getItem: () => null,
        setItem: () => {
          throw new Error("quota exceeded");
        },
        removeItem: () => {},
      });
      expect(() => setDefaultTown("taipei-xinyi")).not.toThrow();
    });
  });

  // ── lastTown ──────────────────────────────────────────────────────────────

  describe("lastTown", () => {
    test("returns null when nothing stored", () => {
      expect(getLastTown()).toBeNull();
    });

    test("round-trips setLastTown / getLastTown", () => {
      setLastTown("hualien-hualien");
      expect(getLastTown()).toBe("hualien-hualien");
    });

    test("does not crash when localStorage throws on setLastTown", () => {
      vi.stubGlobal("localStorage", {
        getItem: () => null,
        setItem: () => {
          throw new Error("quota exceeded");
        },
        removeItem: () => {},
      });
      expect(() => setLastTown("hualien-hualien")).not.toThrow();
    });
  });
});

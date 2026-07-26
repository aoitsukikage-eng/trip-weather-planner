export const STORAGE_KEYS = {
  favorites: "trip-weather-planner:favorites:v1",
  defaultTown: "trip-weather-planner:default-town:v1",
  lastTown: "trip-weather-planner:last-town:v1",
} as const;

export const MAX_FAVORITES = 6;

function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore storage quota / security errors
  }
}

function safeRemoveItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

export function getFavorites(): string[] {
  const raw = safeGetItem(STORAGE_KEYS.favorites);
  if (raw === null) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
}

function persistFavorites(codes: string[]): void {
  safeSetItem(STORAGE_KEYS.favorites, JSON.stringify(codes));
}

export function addFavorite(code: string): string[] {
  const current = getFavorites();
  if (current.includes(code)) return current;
  if (current.length >= MAX_FAVORITES) return current;
  const next = [...current, code];
  persistFavorites(next);
  return next;
}

export function removeFavorite(code: string): string[] {
  const current = getFavorites();
  const next = current.filter((c) => c !== code);
  persistFavorites(next);
  if (getDefaultTown() === code) {
    clearDefaultTown();
  }
  return next;
}

export function moveFavoriteForward(code: string): string[] {
  const current = getFavorites();
  const idx = current.indexOf(code);
  if (idx <= 0) return current;
  const next = [...current];
  [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
  persistFavorites(next);
  return next;
}

export function moveFavoriteBack(code: string): string[] {
  const current = getFavorites();
  const idx = current.indexOf(code);
  if (idx === -1 || idx >= current.length - 1) return current;
  const next = [...current];
  [next[idx], next[idx + 1]] = [next[idx + 1], next[idx]];
  persistFavorites(next);
  return next;
}

export function getDefaultTown(): string | null {
  return safeGetItem(STORAGE_KEYS.defaultTown);
}

export function setDefaultTown(code: string): void {
  safeSetItem(STORAGE_KEYS.defaultTown, code);
}

export function clearDefaultTown(): void {
  safeRemoveItem(STORAGE_KEYS.defaultTown);
}

export function getLastTown(): string | null {
  return safeGetItem(STORAGE_KEYS.lastTown);
}

export function setLastTown(code: string): void {
  safeSetItem(STORAGE_KEYS.lastTown, code);
}

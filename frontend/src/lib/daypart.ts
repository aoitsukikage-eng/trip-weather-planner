import type { SunriseSunset } from "./api";

const TAIPEI_TIME_ZONE = "Asia/Taipei";

// Used only when no sunrise/sunset data has loaded yet (e.g. first paint).
const DEFAULT_SUNRISE_MINUTES = 6 * 60;
const DEFAULT_SUNSET_MINUTES = 18 * 60;

export type Daypart = "day" | "night";

function parseMinutesSinceMidnight(value: string | null | undefined): number | null {
  if (!value) return null;
  const match = /^(\d{1,2}):(\d{2})/.exec(value);
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  return hours * 60 + minutes;
}

/** Minutes since midnight for `base`, evaluated in Asia/Taipei local time. */
export function taipeiMinutesOfDay(base: Date = new Date()): number {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TAIPEI_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(base);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return Number(value.hour) * 60 + Number(value.minute);
}

/**
 * Warm "day" theme between sunrise and sunset, cool "night" theme otherwise.
 * Falls back to a fixed 06:00–18:00 window when sunrise/sunset hasn't loaded yet.
 */
export function resolveDaypart(
  sunriseSunset: SunriseSunset | null | undefined,
  base: Date = new Date(),
): Daypart {
  const nowMinutes = taipeiMinutesOfDay(base);
  const sunriseMinutes = parseMinutesSinceMidnight(sunriseSunset?.sunrise_time) ?? DEFAULT_SUNRISE_MINUTES;
  const sunsetMinutes = parseMinutesSinceMidnight(sunriseSunset?.sunset_time) ?? DEFAULT_SUNSET_MINUTES;
  return nowMinutes >= sunriseMinutes && nowMinutes < sunsetMinutes ? "day" : "night";
}

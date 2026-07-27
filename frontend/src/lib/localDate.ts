export function startOfLocalDay(base: Date = new Date()): Date {
  const current = new Date(base);
  current.setHours(0, 0, 0, 0);
  return current;
}

const TAIPEI_TIME_ZONE = "Asia/Taipei";

/** Return the calendar date at Taiwan's product-facing timezone. */
export function taipeiIsoDate(base: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TAIPEI_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(base);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

/** Milliseconds remaining until the next Asia/Taipei calendar day. */
export function millisecondsUntilNextTaipeiDay(base: Date = new Date()): number {
  const current = taipeiIsoDate(base);
  const nextTaipeiMidnight = new Date(`${current}T00:00:00+08:00`).getTime() + 86_400_000;
  return Math.max(1_000, nextTaipeiMidnight - base.getTime());
}

export function formatLocalDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addLocalDays(base: Date, days: number): Date {
  const current = startOfLocalDay(base);
  current.setDate(current.getDate() + days);
  return current;
}

export function buildDateOptions(
  count = 7,
  base: Date = new Date(),
): Array<{ iso: string; date: Date }> {
  return Array.from({ length: count }, (_, index) => {
    const current = addLocalDays(base, index);
    return {
      iso: formatLocalDate(current),
      date: current,
    };
  });
}

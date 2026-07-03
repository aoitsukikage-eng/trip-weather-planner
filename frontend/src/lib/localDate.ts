export function startOfLocalDay(base: Date = new Date()): Date {
  const current = new Date(base);
  current.setHours(0, 0, 0, 0);
  return current;
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

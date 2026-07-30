const zone = "Asia/Taipei";
export const taipeiToday = (now = new Date()) => { const p = new Intl.DateTimeFormat("en-CA", { timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now); const v = Object.fromEntries(p.map(x => [x.type, x.value])); return `${v.year}-${v.month}-${v.day}`; };
export const untilNextTaipeiMidnight = (now = new Date()) => Math.max(1000, new Date(`${taipeiToday(now)}T00:00:00+08:00`).getTime() + 86400000 - now.getTime());
export const nextDays = (today = taipeiToday()) => Array.from({ length: 7 }, (_, i) => { const d = new Date(`${today}T00:00:00+08:00`); d.setUTCDate(d.getUTCDate() + i); return d.toISOString().slice(0, 10); });

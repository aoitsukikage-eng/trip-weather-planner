// API client for the Trip Weather Planner backend.
// Falls back to inline mock data when the backend is unreachable, so the
// frontend is demoable standalone (mirrors the backend's own mock mode).

export interface Town {
  code: string;
  name: string;
  city: string;
  lat: number;
  lon: number;
}

export interface DailyForecast {
  date: string;
  temp_high_c: number | null;
  temp_low_c: number | null;
  max_pop_percent: number | null;
  weather: string | null;
  advice_hint: string | null;
}

export interface SunriseSunset {
  county: string;
  target_date: string;
  source_date: string;
  sunrise_time: string | null;
  sunset_time: string | null;
  is_approximate: boolean;
}

export interface UVInfo {
  value: number | null;
  level: string | null;
  source_label: string;
  source_type: string;
  observed_at: string | null;
  station_id: string | null;
  station_name: string | null;
}

export interface ForecastResult {
  forecast: {
    town: Town;
    target_date: string;
    source_dataset: string;
    days: DailyForecast[];
    sunrise_sunset: SunriseSunset | null;
    uv: UVInfo | null;
    generated_at: string;
  };
  ai_summary: { text: string; mode: string };
}

interface Envelope<T> {
  success: boolean;
  data: T | null;
  error: { error_code: string; message: string } | null;
  meta: { request_id: string; cached: boolean; source: string | null };
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

const MOCK_TOWNS: Town[] = [
  { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  { code: "hualien-hualien", name: "花蓮市", city: "花蓮縣", lat: 23.98, lon: 121.6 },
  { code: "tainan-west-central", name: "中西區", city: "臺南市", lat: 22.99, lon: 120.2 },
];

function displayDate(isoDate: string): string {
  const [_, month, day] = isoDate.split("-");
  return `${Number(month)}/${Number(day)}`;
}

function mockForecast(town: Town, date: string): ForecastResult {
  const days = Array.from({ length: 7 }, (_, index) => {
    const current = new Date(date);
    current.setDate(current.getDate() + index);
    const isoDate = current.toISOString().slice(0, 10);
    return {
      date: isoDate,
      temp_high_c: 29 + (index % 3),
      temp_low_c: 23 + (index % 2),
      max_pop_percent: 20 + index * 8,
      weather: index % 2 === 0 ? "多雲時陰" : "晴時多雲",
      advice_hint: index >= 4 ? "午後對流機率升高,建議備妥雨具。" : "白天偏熱,記得補水與防曬。",
    };
  });
  return {
    forecast: {
      town,
      target_date: date,
      source_dataset: "mock:frontend-fallback",
      days,
      sunrise_sunset: {
        county: town.city,
        target_date: date,
        source_date: date,
        sunrise_time: "05:12",
        sunset_time: "18:46",
        is_approximate: false,
      },
      uv: {
        value: 8,
        level: "過量",
        source_label: "目前紫外線",
        source_type: "observation",
        observed_at: `${date}T12:00:00+08:00`,
        station_id: "mock-station",
        station_name: `${town.name} mock station`,
      },
      generated_at: new Date().toISOString(),
    },
    ai_summary: {
      text: `${town.city}${town.name}在 ${displayDate(date)} 預報為「多雲時陰」,氣溫約 23–29°C。建議攜帶輕便雨具並留意防曬。`,
      mode: "rule-based (frontend mock)",
    },
  };
}

export async function getTowns(): Promise<Town[]> {
  try {
    const res = await fetch(`${API_BASE}/api/towns`);
    const body: Envelope<Town[]> = await res.json();
    if (body.success && body.data) return body.data;
    throw new Error("bad response");
  } catch {
    return MOCK_TOWNS;
  }
}

export async function getForecast(town: Town, date: string): Promise<ForecastResult> {
  try {
    const res = await fetch(
      `${API_BASE}/api/forecast?town=${encodeURIComponent(town.code)}&date=${date}`,
    );
    const body: Envelope<ForecastResult> = await res.json();
    if (body.success && body.data) return body.data;
    throw new Error(body.error?.message ?? "request failed");
  } catch {
    return mockForecast(town, date);
  }
}

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

export interface ForecastResult {
  forecast: {
    town: Town;
    target_date: string;
    source_dataset: string;
    days: DailyForecast[];
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
  { code: "taipei-zhongzheng", name: "中正區", city: "臺北市", lat: 25.03, lon: 121.52 },
  { code: "hualien-hualien", name: "花蓮市", city: "花蓮縣", lat: 23.98, lon: 121.6 },
  { code: "tainan-west-central", name: "中西區", city: "臺南市", lat: 22.99, lon: 120.2 },
];

function mockForecast(town: Town, date: string): ForecastResult {
  return {
    forecast: {
      town,
      target_date: date,
      source_dataset: "mock:frontend-fallback",
      days: [
        {
          date,
          temp_high_c: 30,
          temp_low_c: 24,
          max_pop_percent: 60,
          weather: "多雲時陰",
          advice_hint: "天氣多變,建議攜帶輕便雨具。",
        },
      ],
      generated_at: new Date().toISOString(),
    },
    ai_summary: {
      text: `${town.city}${town.name}在 ${date} 預報為「多雲時陰」,氣溫約 24–30°C。建議攜帶輕便雨具。`,
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

// API client for the Trip Weather Planner backend.
// Falls back to inline mock data when the backend is unreachable, so the
// frontend is demoable standalone (mirrors the backend's own mock mode).
import { formatLocalDate } from "./localDate";

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

export interface HourlyForecast {
  time: string;
  temp_c: number | null;
  apparent_temp_c: number | null;
  pop_percent: number | null;
  weather: string | null;
  weather_code: string | null;
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
    hourly: HourlyForecast[] | null;
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

export class ApiError extends Error {
  readonly errorCode: string;
  readonly status: number;

  constructor(message: string, errorCode = "request_failed", status = 500) {
    super(message);
    this.name = "ApiError";
    this.errorCode = errorCode;
    this.status = status;
  }
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

function toLocalIso(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:00:00`;
}

function stableUnit(...parts: string[]): number {
  let hash = 2166136261;
  const text = parts.join("|");
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 10000) / 10000;
}

function mockHourlyForecast(town: Town, date: string): HourlyForecast[] {
  const start = new Date(`${date}T00:00:00`);
  return Array.from({ length: 24 }, (_, index) => {
    const slotTime = new Date(start);
    slotTime.setHours(slotTime.getHours() + index * 3);
    const slotIso = toLocalIso(slotTime);
    const hour = slotTime.getHours();
    const baseTemp = 30 - (town.lat - 22) * 1.1;
    const diurnal = hour < 9 ? -4 : hour < 18 ? 3.5 : -1;
    const noise = (stableUnit(town.code, slotIso) - 0.5) * 3;
    const temp = Number((baseTemp + diurnal + noise).toFixed(1));
    const apparentTemp = Number(
      (temp + (stableUnit("at", town.code, slotIso) - 0.5) * 2.4).toFixed(1),
    );
    const pop = Math.round(stableUnit("pop", town.code, date, String(hour)) * 100);
    const weatherCode = pop >= 70 ? "12" : pop >= 40 ? "07" : pop >= 20 ? "04" : "01";
    const weather = pop >= 70 ? "陰時多雲短暫雨" : pop >= 40 ? "多雲時陰" : pop >= 20 ? "多雲" : "晴時多雲";
    return {
      time: slotIso,
      temp_c: temp,
      apparent_temp_c: apparentTemp,
      pop_percent: pop,
      weather,
      weather_code: weatherCode,
    };
  });
}

function mockForecast(town: Town, date: string): ForecastResult {
  const days = Array.from({ length: 7 }, (_, index) => {
    const current = new Date(`${date}T00:00:00`);
    current.setDate(current.getDate() + index);
    const isoDate = formatLocalDate(current);
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
      hourly: mockHourlyForecast(town, date),
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
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/api/forecast?town=${encodeURIComponent(town.code)}&date=${date}`,
    );
  } catch (error) {
    if (!_isNetworkFailure(error)) {
      throw error;
    }
    return mockForecast(town, date);
  }

  const body = (await _readJsonSafely(res)) as Envelope<ForecastResult> | null;
  if (res.ok && body?.success && body.data) {
    return body.data;
  }

  throw new ApiError(
    body?.error?.message ?? `Request failed with status ${res.status}.`,
    body?.error?.error_code ?? "request_failed",
    res.status,
  );
}

function _isNetworkFailure(error: unknown): boolean {
  return error instanceof TypeError;
}

async function _readJsonSafely(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

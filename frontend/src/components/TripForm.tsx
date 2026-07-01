import { useState } from "react";
import type { Town } from "../lib/api";

interface Props {
  towns: Town[];
  loading: boolean;
  onSubmit: (town: Town, date: string) => void;
}

function todayPlus(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function TripForm({ towns, loading, onSubmit }: Props) {
  const [townCode, setTownCode] = useState(towns[0]?.code ?? "");
  const [date, setDate] = useState(todayPlus(1));

  const handle = (e: React.FormEvent) => {
    e.preventDefault();
    const town = towns.find((t) => t.code === townCode);
    if (town) onSubmit(town, date);
  };

  return (
    <form className="trip-form" onSubmit={handle}>
      <label>
        目的地
        <select value={townCode} onChange={(e) => setTownCode(e.target.value)}>
          {towns.map((t) => (
            <option key={t.code} value={t.code}>
              {t.city} {t.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        旅遊日期
        <input
          type="date"
          value={date}
          min={todayPlus(0)}
          max={todayPlus(6)}
          onChange={(e) => setDate(e.target.value)}
        />
      </label>
      <button type="submit" disabled={loading || !townCode}>
        {loading ? "查詢中…" : "查詢天氣"}
      </button>
    </form>
  );
}

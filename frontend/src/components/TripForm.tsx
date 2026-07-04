import { useEffect, useState } from "react";
import type { Town } from "../lib/api";

interface Props {
  towns: Town[];
  loading: boolean;
  onSubmit: (town: Town) => void;
}

export default function TripForm({ towns, loading, onSubmit }: Props) {
  const [city, setCity] = useState("");
  const [townCode, setTownCode] = useState("");

  const cities = Array.from(new Set(towns.map((town) => town.city))).sort((left, right) =>
    left.localeCompare(right, "zh-Hant"),
  );
  const filteredTowns = towns
    .filter((town) => town.city === city)
    .sort((left, right) => left.name.localeCompare(right.name, "zh-Hant"));

  useEffect(() => {
    if (!towns.length) {
      return;
    }
    setCity((current) => current || towns[0].city);
  }, [towns]);

  useEffect(() => {
    if (!city) {
      return;
    }
    const nextTown = filteredTowns.find((town) => town.code === townCode) ?? filteredTowns[0];
    setTownCode(nextTown?.code ?? "");
  }, [city, filteredTowns, townCode]);

  const handle = (event: React.FormEvent) => {
    event.preventDefault();
    const town = towns.find((item) => item.code === townCode);
    if (town) {
      onSubmit(town);
    }
  };

  return (
    <form className="trip-form" onSubmit={handle}>
      <label className="form-field">
        縣市
        <select value={city} onChange={(event) => setCity(event.target.value)}>
          {cities.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="form-field">
        鄉鎮市區
        <select value={townCode} onChange={(event) => setTownCode(event.target.value)}>
          {filteredTowns.map((town) => (
            <option key={town.code} value={town.code}>
              {town.name}
            </option>
          ))}
        </select>
      </label>

      <button className="submit-button" type="submit" disabled={loading || !townCode}>
        {loading ? "查詢中…" : "查詢天氣"}
      </button>
    </form>
  );
}

import { useEffect } from "react";
import type { Town } from "../lib/api";

interface Props {
  towns: Town[];
  loading: boolean;
  city: string;
  townCode: string;
  onCityChange: (city: string) => void;
  onTownCodeChange: (code: string) => void;
  onSubmit: (town: Town) => void;
}

export default function TripForm({
  towns,
  loading,
  city,
  townCode,
  onCityChange,
  onTownCodeChange,
  onSubmit,
}: Props) {
  const cities = Array.from(new Set(towns.map((town) => town.city))).sort((left, right) =>
    left.localeCompare(right, "zh-Hant"),
  );
  const filteredTowns = towns
    .filter((town) => town.city === city)
    .sort((left, right) => left.name.localeCompare(right.name, "zh-Hant"));

  // When city changes, auto-correct townCode to a valid town in the new city.
  useEffect(() => {
    if (!city || !filteredTowns.length) return;
    if (!filteredTowns.some((t) => t.code === townCode)) {
      onTownCodeChange(filteredTowns[0].code);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city]);

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
        <select value={city} onChange={(event) => onCityChange(event.target.value)}>
          {cities.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="form-field">
        鄉鎮市區
        <select value={townCode} onChange={(event) => onTownCodeChange(event.target.value)}>
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

import { useEffect } from "react";
import type { Town } from "../lib/api";
import { useLocale } from "../lib/locale";

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
  const { locale, t } = useLocale();
  const collation = locale === "en" ? "en" : "zh-Hant";

  const getCityLabel = (cityKey: string): string => {
    const sample = towns.find((town) => town.city === cityKey);
    if (locale === "en" && sample?.city_en) return sample.city_en;
    return sample?.city || cityKey;
  };

  const getTownLabel = (town: Town): string => {
    if (locale === "en" && town.name_en) return town.name_en;
    return town.name;
  };

  const cities = Array.from(new Set(towns.map((town) => town.city))).sort((left, right) =>
    getCityLabel(left).localeCompare(getCityLabel(right), collation),
  );
  const filteredTowns = towns
    .filter((town) => town.city === city)
    .sort((left, right) => getTownLabel(left).localeCompare(getTownLabel(right), collation));

  // When city changes, auto-correct townCode to a valid town in the new city.
  useEffect(() => {
    if (!city || !filteredTowns.length) return;
    if (!filteredTowns.some((item) => item.code === townCode)) {
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
        {t.labelCity}
        <select value={city} onChange={(event) => onCityChange(event.target.value)}>
          {cities.map((option) => (
            <option key={option} value={option}>
              {getCityLabel(option)}
            </option>
          ))}
        </select>
      </label>

      <label className="form-field">
        {t.labelTown}
        <select value={townCode} onChange={(event) => onTownCodeChange(event.target.value)}>
          {filteredTowns.map((town) => (
            <option key={town.code} value={town.code}>
              {getTownLabel(town)}
            </option>
          ))}
        </select>
      </label>

      <button className="submit-button" type="submit" disabled={loading || !townCode}>
        {loading ? t.btnQuerying : t.btnQuery}
      </button>
    </form>
  );
}

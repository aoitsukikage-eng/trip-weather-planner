import { useEffect, useState } from "react";
import TripForm from "./components/TripForm";
import ForecastView from "./components/ForecastView";
import { getForecast, getTowns, type ForecastResult, type Town } from "./lib/api";
import { formatLocalDate, startOfLocalDay } from "./lib/localDate";

function todayIsoDate(): string {
  return formatLocalDate(startOfLocalDay());
}

export default function App() {
  const [towns, setTowns] = useState<Town[]>([]);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTowns().then(setTowns);
  }, []);

  useEffect(() => {
    if (!towns.length || result) {
      return;
    }
    void handleSubmit(towns[0], todayIsoDate());
  }, [towns, result]);

  const handleSubmit = async (town: Town, date: string) => {
    setLoading(true);
    setError(null);
    try {
      setResult(await getForecast(town, date));
    } catch (caughtError) {
      setResult(null);
      setError(caughtError instanceof Error ? caughtError.message : "查詢失敗，請稍後再試。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app">
      <header>
        <h1>旅遊行前天氣規劃</h1>
        <p className="tagline">
          Trip Weather Planner — 選目的地與日期,取得天氣預報與行前建議
        </p>
      </header>

      {towns.length > 0 ? (
        <TripForm towns={towns} loading={loading} onSubmit={handleSubmit} />
      ) : (
        <p>載入鄉鎮清單中…</p>
      )}

      {error && (
        <section className="error-panel" role="alert">
          <strong>查詢失敗</strong>
          <p>{error}</p>
        </section>
      )}

      {result && <ForecastView result={result} />}

      <footer>
        <small>
          天氣資料:中央氣象署開放資料(未設 key 時為 mock)。景點與交通為後續階段。
        </small>
      </footer>
    </main>
  );
}

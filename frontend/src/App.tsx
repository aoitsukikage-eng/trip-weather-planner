import { useEffect, useState } from "react";
import TripForm from "./components/TripForm";
import ForecastView from "./components/ForecastView";
import { getForecast, getTowns, type ForecastResult, type Town } from "./lib/api";

function todayIsoDate(): string {
  const current = new Date();
  current.setHours(0, 0, 0, 0);
  return current.toISOString().slice(0, 10);
}

export default function App() {
  const [towns, setTowns] = useState<Town[]>([]);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);

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
    try {
      setResult(await getForecast(town, date));
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

      {result && <ForecastView result={result} />}

      <footer>
        <small>
          天氣資料:中央氣象署開放資料(未設 key 時為 mock)。景點與交通為後續階段。
        </small>
      </footer>
    </main>
  );
}

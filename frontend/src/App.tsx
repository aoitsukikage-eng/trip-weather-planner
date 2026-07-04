import { useEffect, useRef, useState } from "react";
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
  const [selectedTown, setSelectedTown] = useState<Town | null>(null);
  const activeRequestRef = useRef(0);

  useEffect(() => {
    getTowns().then(setTowns);
  }, []);

  useEffect(() => {
    if (!towns.length || result) {
      return;
    }
    void runForecastQuery(towns[0], todayIsoDate());
  }, [towns, result]);

  const runForecastQuery = async (town: Town, date: string) => {
    const requestId = activeRequestRef.current + 1;
    activeRequestRef.current = requestId;
    setSelectedTown(town);
    setLoading(true);
    setError(null);
    try {
      const nextResult = await getForecast(town, date);
      if (requestId !== activeRequestRef.current) {
        return;
      }
      setResult(nextResult);
    } catch (caughtError) {
      if (requestId !== activeRequestRef.current) {
        return;
      }
      setResult(null);
      setError(caughtError instanceof Error ? caughtError.message : "查詢失敗，請稍後再試。");
    } finally {
      if (requestId === activeRequestRef.current) {
        setLoading(false);
      }
    }
  };

  const handleSubmit = async (town: Town) => {
    await runForecastQuery(town, todayIsoDate());
  };

  const handleSelectDate = async (date: string) => {
    const town = result?.forecast.town ?? selectedTown;
    if (!town) {
      return;
    }
    await runForecastQuery(town, date);
  };

  return (
    <main className="app">
      <header>
        <h1>旅遊行前天氣規劃</h1>
        <p className="tagline">選擇目的地後即可查看一週天氣、未來 72 小時趨勢與行前提醒。</p>
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

      {result && <ForecastView result={result} loading={loading} onSelectDate={handleSelectDate} />}

      <footer>
        <small>出發前先看一眼天氣與日照資訊，行程安排更從容。</small>
      </footer>
    </main>
  );
}

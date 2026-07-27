import { useEffect, useRef, useState } from "react";
import TripForm from "./components/TripForm";
import ForecastView from "./components/ForecastView";
import FavoriteTowns from "./components/FavoriteTowns";
import { getForecast, getTowns, type ForecastResult, type Town } from "./lib/api";
import { millisecondsUntilNextTaipeiDay, taipeiIsoDate } from "./lib/localDate";
import {
  getFavorites,
  getDefaultTown,
  getLastTown,
  setLastTown,
  addFavorite as libAddFavorite,
  removeFavorite as libRemoveFavorite,
  moveFavoriteForward as libMoveForward,
  moveFavoriteBack as libMoveBack,
  setDefaultTown as libSetDefault,
  clearDefaultTown as libClearDefault,
} from "./lib/favoriteTowns";

function todayIsoDate(): string {
  return taipeiIsoDate();
}

export default function App() {
  const [towns, setTowns] = useState<Town[]>([]);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [chartResult, setChartResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [daySelectionError, setDaySelectionError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState("");
  const [selectedTownCode, setSelectedTownCode] = useState("");
  const [favorites, setFavorites] = useState<string[]>(() => getFavorites());
  const [defaultTownCode, setDefaultTownCode] = useState<string | null>(() => getDefaultTown());
  const activeRequestRef = useRef(0);
  const latestSuccessfulTownRef = useRef<Town | null>(null);
  const todayAnchorRef = useRef(todayIsoDate());
  const autoRefreshDateRef = useRef<string | null>(null);
  const inFlightRef = useRef(false);

  useEffect(() => {
    getTowns().then(setTowns);
  }, []);

  useEffect(() => {
    if (!towns.length || result) {
      return;
    }
    // Initialization priority: custom default > last successful > taipei-xinyi > towns[0]
    const defCode = getDefaultTown();
    const lastCode = getLastTown();
    const initialTown =
      (defCode ? towns.find((t) => t.code === defCode) : null) ??
      (lastCode ? towns.find((t) => t.code === lastCode) : null) ??
      towns.find((t) => t.code === "taipei-xinyi") ??
      towns[0];

    setSelectedCity(initialTown.city);
    setSelectedTownCode(initialTown.code);
    void runForecastQuery(initialTown, todayIsoDate());
  }, [towns, result]);

  const runForecastQuery = async (
    town: Town,
    date: string,
    options?: { preserveCurrentViewOnError?: boolean; updateChart?: boolean },
  ) => {
    const requestId = activeRequestRef.current + 1;
    activeRequestRef.current = requestId;
    setSelectedCity(town.city);
    setSelectedTownCode(town.code);
    setLoading(true);
    inFlightRef.current = true;
    setError(null);
    setDaySelectionError(null);
    try {
      const nextResult = await getForecast(town, date);
      if (requestId !== activeRequestRef.current) {
        return;
      }
      setResult(nextResult);
      latestSuccessfulTownRef.current = town;
      setLastTown(town.code);
      if (options?.updateChart ?? true) {
        setChartResult(nextResult);
      }
    } catch (caughtError) {
      if (requestId !== activeRequestRef.current) {
        return;
      }
      const message =
        caughtError instanceof Error ? caughtError.message : "查詢失敗，請稍後再試。";
      if (options?.preserveCurrentViewOnError) {
        setDaySelectionError(message);
      } else {
        setResult(null);
        if (options?.updateChart ?? true) {
          setChartResult(null);
        }
        setError(message);
      }
    } finally {
      if (requestId === activeRequestRef.current) {
        setLoading(false);
        inFlightRef.current = false;
      }
    }
  };

  const handleSubmit = async (town: Town) => {
    await runForecastQuery(town, todayIsoDate(), { updateChart: true });
  };

  const handleSelectDate = async (date: string) => {
    if (!result) {
      return;
    }
    await runForecastQuery(result.forecast.town, date, {
      preserveCurrentViewOnError: true,
      updateChart: false,
    });
  };

  const handleFavoriteSelect = async (town: Town) => {
    await runForecastQuery(town, todayIsoDate(), { updateChart: true });
  };

  useEffect(() => {
    let rolloverTimer: ReturnType<typeof window.setTimeout> | undefined;

    const checkForDateRollover = () => {
      const today = todayIsoDate();
      if (today === todayAnchorRef.current || inFlightRef.current) {
        return;
      }

      const town = latestSuccessfulTownRef.current;
      if (!town || autoRefreshDateRef.current === today) {
        return;
      }

      todayAnchorRef.current = today;
      autoRefreshDateRef.current = today;
      void runForecastQuery(town, today, { updateChart: true });
    };

    const scheduleRolloverCheck = () => {
      rolloverTimer = window.setTimeout(() => {
        checkForDateRollover();
        scheduleRolloverCheck();
      }, millisecondsUntilNextTaipeiDay());
    };

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        checkForDateRollover();
      }
    };

    checkForDateRollover();
    scheduleRolloverCheck();
    window.addEventListener("focus", checkForDateRollover);
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      if (rolloverTimer !== undefined) window.clearTimeout(rolloverTimer);
      window.removeEventListener("focus", checkForDateRollover);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [result]);

  const handleFavoriteAdd = (code: string) => {
    setFavorites(libAddFavorite(code));
  };

  const handleFavoriteRemove = (code: string) => {
    setFavorites(libRemoveFavorite(code));
    if (defaultTownCode === code) setDefaultTownCode(null);
  };

  const handleFavoriteMoveForward = (code: string) => {
    setFavorites(libMoveForward(code));
  };

  const handleFavoriteMoveBack = (code: string) => {
    setFavorites(libMoveBack(code));
  };

  const handleFavoriteToggleDefault = (code: string) => {
    if (defaultTownCode === code) {
      libClearDefault();
      setDefaultTownCode(null);
    } else {
      libSetDefault(code);
      setDefaultTownCode(code);
    }
  };

  return (
    <main className="app">
      <header>
        <h1>旅遊行前天氣規劃</h1>
        <p className="tagline">選擇目的地後即可查看一週天氣、未來 72 小時趨勢與行前提醒。</p>
      </header>

      {towns.length > 0 ? (
        <>
          <FavoriteTowns
            towns={towns}
            favorites={favorites}
            defaultTown={defaultTownCode}
            currentTownCode={selectedTownCode}
            loading={loading}
            onSelect={handleFavoriteSelect}
            onAdd={handleFavoriteAdd}
            onRemove={handleFavoriteRemove}
            onMoveForward={handleFavoriteMoveForward}
            onMoveBack={handleFavoriteMoveBack}
            onToggleDefault={handleFavoriteToggleDefault}
          />
          <TripForm
            towns={towns}
            loading={loading}
            city={selectedCity}
            townCode={selectedTownCode}
            onCityChange={setSelectedCity}
            onTownCodeChange={setSelectedTownCode}
            onSubmit={handleSubmit}
          />
        </>
      ) : (
        <p>載入鄉鎮清單中…</p>
      )}

      {error && (
        <section className="error-panel" role="alert">
          <strong>查詢失敗</strong>
          <p>{error}</p>
        </section>
      )}

      {result && (
        <ForecastView
          chartResult={chartResult ?? result}
          daySelectionError={daySelectionError}
          result={result}
          loading={loading}
          onSelectDate={handleSelectDate}
        />
      )}

      <footer>
        <small>出發前先看一眼天氣與日照資訊，行程安排更從容。</small>
      </footer>
    </main>
  );
}

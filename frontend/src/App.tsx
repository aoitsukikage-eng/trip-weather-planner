import { useEffect, useRef, useState } from "react";
import TripForm from "./components/TripForm";
import ForecastView from "./components/ForecastView";
import FavoriteTowns from "./components/FavoriteTowns";
import { getForecast, getTowns, type ForecastResult, type Town } from "./lib/api";
import { millisecondsUntilNextTaipeiDay, taipeiIsoDate } from "./lib/localDate";
import { resolveDaypart } from "./lib/daypart";
import { LocaleProvider, useLocale } from "./lib/locale";
import { SUPPORTED_LOCALES } from "./i18n";
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
  return (
    <LocaleProvider>
      <AppMain />
    </LocaleProvider>
  );
}

function AppMain() {
  const { locale, setLocale, t } = useLocale();
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

  const handleToggleLocale = () => {
    const currentIndex = SUPPORTED_LOCALES.indexOf(locale);
    const nextIndex = (currentIndex + 1) % SUPPORTED_LOCALES.length;
    setLocale(SUPPORTED_LOCALES[nextIndex]);
  };

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
        caughtError instanceof Error ? caughtError.message : t.queryFailedDefault;
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

  useEffect(() => {
    const sunriseSunset = (chartResult ?? result)?.forecast.sunrise_sunset ?? null;

    const applyDaypart = () => {
      document.documentElement.dataset.daypart = resolveDaypart(sunriseSunset);
    };

    applyDaypart();
    const timer = window.setInterval(applyDaypart, 60_000);
    return () => window.clearInterval(timer);
  }, [chartResult, result]);

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
      <header style={{ position: "relative" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
          <div>
            <h1>{t.appTitle}</h1>
            <p className="tagline">{t.appTagline}</p>
          </div>
          <button
            type="button"
            className="lang-switch-btn"
            onClick={handleToggleLocale}
            style={{
              padding: "0.4rem 0.85rem",
              borderRadius: "999px",
              border: "1px solid var(--twp-paper-border, #d6c9b4)",
              background: "var(--twp-paper, #fffdf8)",
              color: "var(--twp-ocean-700, #0a5975)",
              fontWeight: 650,
              fontSize: "0.88rem",
              cursor: "pointer",
              flexShrink: 0,
            }}
            aria-label={t.switchLangAriaLabel}
          >
            {t.switchLangLabel}
          </button>
        </div>
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
        <p>{t.loadingTowns}</p>
      )}

      {error && (
        <section className="error-panel" role="alert">
          <strong>{t.queryFailed}</strong>
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
        <small>{t.footerNote}</small>
      </footer>
    </main>
  );
}

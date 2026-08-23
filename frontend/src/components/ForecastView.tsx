import { memo, useEffect, useRef } from "react";
import { isMockForecast, type DailyForecast, type ForecastResult, type HourlyForecast } from "../lib/api";
import CelestialArc from "./CelestialArc";
import StatusGauge from "./StatusGauge";
import { useLocale } from "../lib/locale";
import type { Dictionary } from "../i18n";

function popColor(pop: number | null): string {
  if (pop === null) return "#cbd5e1";
  if (pop >= 70) return "#2563eb";
  if (pop >= 40) return "#60a5fa";
  return "#bae6fd";
}

function formatDateLabel(isoDate: string, t: Dictionary): string {
  const current = new Date(`${isoDate}T00:00:00`);
  const weekday = t.weekdaysShort[current.getDay()];
  return t.formatDate(current.getMonth() + 1, current.getDate(), weekday);
}

function formatWeekdayLabel(isoDate: string, t: Dictionary): string {
  const current = new Date(`${isoDate}T00:00:00`);
  return t.formatWeekday(t.weekdaysShort[current.getDay()]);
}

function formatDayLabel(isoDateTime: string): string {
  const current = new Date(isoDateTime);
  return `${current.getMonth() + 1}/${current.getDate()}`;
}

function formatHourLabel(isoDateTime: string): string {
  const current = new Date(isoDateTime);
  return `${String(current.getHours()).padStart(2, "0")}:00`;
}

export function resolveWeatherIcon(
  code: string | null | undefined,
  weatherText: string | null | undefined,
): string {
  const c = code ? code.padStart(2, "0") : "";
  if (c.startsWith("01")) return "☀️";
  if (c.startsWith("02") || c.startsWith("03")) return "🌤️";
  if (c.startsWith("04") || c.startsWith("05") || c.startsWith("06") || c.startsWith("07")) {
    return "☁️";
  }
  if (c.startsWith("08") || c.startsWith("09") || c.startsWith("10")) return "🌦️";
  if (c.startsWith("11") || c.startsWith("12") || c.startsWith("13") || c.startsWith("14")) {
    return "🌧️";
  }
  if (
    c.startsWith("15") ||
    c.startsWith("16") ||
    c.startsWith("17") ||
    c.startsWith("18") ||
    c.startsWith("19") ||
    c.startsWith("20") ||
    c.startsWith("21") ||
    c.startsWith("22")
  ) {
    return "⛈️";
  }

  const weather = weatherText ?? "";
  if (weather.includes("雷") || weather.toLowerCase().includes("thunder")) return "⛈️";
  if (
    weather.includes("雨") ||
    weather.toLowerCase().includes("rain") ||
    weather.toLowerCase().includes("shower")
  ) {
    return "🌧️";
  }
  if (
    weather.includes("晴") ||
    weather.toLowerCase().includes("clear") ||
    weather.toLowerCase().includes("sun")
  ) {
    return "☀️";
  }
  if (
    weather.includes("雲") ||
    weather.includes("陰") ||
    weather.toLowerCase().includes("cloud") ||
    weather.toLowerCase().includes("overcast")
  ) {
    return "☁️";
  }

  return "·";
}

function slotIcon(slot: HourlyForecast): string {
  return resolveWeatherIcon(slot.weather_code, slot.weather);
}

function dailyWeatherIcon(
  code: string | null | undefined,
  weatherText: string | null | undefined,
): string {
  return resolveWeatherIcon(code, weatherText);
}

function buildLinePath(points: Array<{ x: number; y: number }>): string {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

export function getHourlyAnnotationStep(hourlyCount: number, plotWidth: number): number {
  if (hourlyCount <= 1) return 1;
  const slotGap = plotWidth / (hourlyCount - 1);
  const minAnnotationGap = 56;
  return Math.max(1, Math.ceil(minAnnotationGap / Math.max(slotGap, 1)));
}

function shouldShowHourlyAnnotation(index: number, total: number, step: number): boolean {
  return index === 0 || index === total - 1 || index % step === 0;
}

const HourlyForecastChart = memo(function HourlyForecastChart({
  hourly,
  placeLabel,
}: {
  hourly: HourlyForecast[];
  placeLabel: string;
}) {
  const { t } = useLocale();
  const width = 960;
  const height = 360;
  const padding = { top: 118, right: 18, bottom: 62, left: 52 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = 136;
  const popBaseY = 310;
  const popHeight = 42;
  const slotGap = hourly.length > 1 ? plotWidth / (hourly.length - 1) : 0;
  const annotationStep = getHourlyAnnotationStep(hourly.length, plotWidth);
  const allTemps = hourly.flatMap((slot) =>
    [slot.temp_c, slot.apparent_temp_c].filter((value): value is number => value !== null),
  );
  const minTemp = allTemps.length > 0 ? Math.floor(Math.min(...allTemps) - 2) : 20;
  const maxTemp = allTemps.length > 0 ? Math.ceil(Math.max(...allTemps) + 2) : minTemp + 8;
  const tempRange = Math.max(maxTemp - minTemp, 4);
  const tempToY = (value: number) =>
    padding.top + ((maxTemp - value) / tempRange) * plotHeight;

  const tempPoints = hourly
    .map((slot, index) =>
      slot.temp_c === null
        ? null
        : {
            x: padding.left + slotGap * index,
            y: tempToY(slot.temp_c),
          },
    )
    .filter((point): point is { x: number; y: number } => point !== null);
  const apparentPoints = hourly
    .map((slot, index) =>
      slot.apparent_temp_c === null
        ? null
        : {
            x: padding.left + slotGap * index,
            y: tempToY(slot.apparent_temp_c),
          },
    )
    .filter((point): point is { x: number; y: number } => point !== null);
  const gridValues = Array.from({ length: 4 }, (_, index) => {
    const ratio = index / 3;
    return Math.round((maxTemp - tempRange * ratio) * 10) / 10;
  });
  const dayBoundaries = hourly
    .map((slot, index) => ({
      date: slot.time.slice(0, 10),
      index,
      label: formatDayLabel(slot.time),
    }))
    .filter((entry, index, list) => index === 0 || entry.date !== list[index - 1].date);
  const barWidth = Math.max(14, Math.min(26, slotGap * 0.68 || 18));

  return (
    <section className="hourly-chart">
      <div className="hourly-chart-header">
        <div className="chart-copy">
          <h3>{t.hourlyChartTitle}</h3>
          <p>{t.hourlyChartSubtitle}</p>
        </div>
        <div className="chart-place-wrap">
          <p className="chart-place" data-testid="chart-place">
            {placeLabel}
          </p>
        </div>
        <div className="chart-legend">
          <span className="legend-item">
            <i className="legend-swatch legend-swatch-temp" />
            {t.legendTemp}
          </span>
          <span className="legend-item">
            <i className="legend-swatch legend-swatch-apparent" />
            {t.legendApparentTemp}
          </span>
        </div>
      </div>

      <div className="chart-shell">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={t.hourlyChartAriaLabel}
        >
          {gridValues.map((value) => (
            <g key={`grid-${value}`}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={tempToY(value)}
                y2={tempToY(value)}
                stroke="#d8e4ef"
                strokeDasharray="4 6"
              />
              <text
                x={padding.left - 10}
                y={tempToY(value) + 4}
                textAnchor="end"
                fontSize="11"
                fill="#5b7287"
              >
                {value}°
              </text>
            </g>
          ))}

          {dayBoundaries.map((boundary) => {
            const x = padding.left + slotGap * boundary.index;
            return (
              <g key={`day-${boundary.date}`}>
                <line
                  x1={x}
                  x2={x}
                  y1={48}
                  y2={popBaseY + 12}
                  stroke="#b8ccdd"
                  strokeDasharray="3 5"
                />
                <text x={x + 6} y={36} fontSize="12" fill="#33516b" fontWeight="700">
                  {boundary.label}
                </text>
              </g>
            );
          })}

          {hourly.map((slot, index) => {
            const x = padding.left + slotGap * index;
            const pop = slot.pop_percent ?? 0;
            const barHeight = (pop / 100) * popHeight;
            const showAnnotation = shouldShowHourlyAnnotation(index, hourly.length, annotationStep);
            return (
              <g key={slot.time}>
                {showAnnotation && (
                  <text x={x} y={64} textAnchor="middle" fontSize="18">
                    {slotIcon(slot)}
                  </text>
                )}
                {showAnnotation && (
                  <text
                    x={x}
                    y={90}
                    textAnchor="middle"
                    fontSize="11"
                    fill="#3d556d"
                    data-testid="hourly-time-label"
                  >
                    {formatHourLabel(slot.time)}
                  </text>
                )}
                <line
                  x1={x}
                  x2={x}
                  y1={popBaseY + 4}
                  y2={popBaseY + 10}
                  stroke="#8ca4b9"
                />
                <rect
                  x={x - barWidth / 2}
                  y={popBaseY - barHeight}
                  width={barWidth}
                  height={barHeight}
                  rx="6"
                  fill={popColor(slot.pop_percent)}
                />
                {showAnnotation && (
                  <text
                    x={x}
                    y={popBaseY - barHeight - 6}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#32526e"
                  >
                    {slot.pop_percent ?? "—"}%
                  </text>
                )}
              </g>
            );
          })}

          {tempPoints.length > 1 && (
            <path
              d={buildLinePath(tempPoints)}
              fill="none"
              stroke="#ef6c3b"
              strokeWidth="3"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}
          {apparentPoints.length > 1 && (
            <path
              d={buildLinePath(apparentPoints)}
              fill="none"
              stroke="#7c3aed"
              strokeWidth="3"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}

          {tempPoints.map((point, index) => (
            <circle key={`temp-${index}`} cx={point.x} cy={point.y} r="4" fill="#ef6c3b" />
          ))}
          {apparentPoints.map((point, index) => (
            <circle key={`apparent-${index}`} cx={point.x} cy={point.y} r="4" fill="#7c3aed" />
          ))}
        </svg>
      </div>

      {apparentPoints.length === 0 && (
        <p className="chart-note">{t.hourlyChartNote}</p>
      )}
    </section>
  );
});

function formatSunriseSourceLabel(sourceDate: string, t: Dictionary): string {
  return t.sunAstroRef(sourceDate);
}

function formatUvSourceLabel(sourceType: string, t: Dictionary): string {
  return sourceType === "observation" ? t.uvObserved : t.uvForecasted;
}

function hasDailyPop(pop: number | null): pop is number {
  return pop !== null;
}

function buildDayAriaLabel(day: DailyForecast, t: Dictionary): string {
  const parts = [
    formatDateLabel(day.date, t),
    day.weather ?? t.weatherDataUnavailable,
    t.tempHigh(day.temp_high_c ?? "—"),
    t.tempLow(day.temp_low_c ?? "—"),
  ];
  if (hasDailyPop(day.max_pop_percent)) {
    parts.push(t.precipPop(day.max_pop_percent));
  }
  if (day.aqi_forecast?.value != null) parts.push(t.aqiLabel(day.aqi_forecast.value));
  return parts.join(" ");
}

export default function ForecastView({
  chartResult,
  daySelectionError,
  result,
  loading = false,
  onSelectDate,
}: {
  chartResult?: ForecastResult;
  daySelectionError?: string | null;
  result: ForecastResult;
  loading?: boolean;
  onSelectDate?: (date: string) => void;
}) {
  const { t } = useLocale();
  const { forecast, ai_summary } = result;
  const displayedDays = forecast.days.slice(0, 7);
  const chartForecast = chartResult?.forecast ?? forecast;
  const sunrise = forecast.sunrise_sunset;
  const uv = forecast.uv;
  const aqi = forecast.aqi;
  const moon = forecast.moon;
  const warnings = forecast.warnings ?? [];
  const placeLabel = `${forecast.town.city} ${forecast.town.name}`;
  const chartPlaceLabel = `${chartForecast.town.city} ${chartForecast.town.name}`;
  const showMockBadge = isMockForecast(result);
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const pendingFocusDateRef = useRef<string | null>(null);

  useEffect(() => {
    if (loading || pendingFocusDateRef.current !== forecast.target_date) {
      return;
    }
    buttonRefs.current[forecast.target_date]?.focus({ preventScroll: true });
    pendingFocusDateRef.current = null;
  }, [forecast.target_date, loading]);

  return (
    <section className="result" data-source-dataset={forecast.source_dataset} data-summary-mode={ai_summary.mode}>
      <h2>
        {placeLabel} · {formatDateLabel(forecast.target_date, t)}
      </h2>

      {forecast.date_adjusted && forecast.requested_date && (
        <p className="section-hint" data-testid="adjusted-focus-notice" role="status">
          {t.adjustedNotice(formatDateLabel(forecast.requested_date, t), formatDateLabel(forecast.target_date, t))}
        </p>
      )}

      {warnings.length > 0 && (
        <section className="warning-banner" data-testid="warning-banner" data-severity={warnings[0].severity} aria-label={t.warningBannerAriaLabel}>
          {warnings.slice(0, 2).map((warning) => <p key={warning.title}><strong>{warning.title}</strong>{warning.description ? `：${warning.description}` : ""}</p>)}
          {warnings.length > 2 && <details><summary>{t.moreWarnings(warnings.length - 2)}</summary>{warnings.slice(2).map((warning) => <p key={warning.title}>{warning.title}</p>)}</details>}
        </section>
      )}

      <section className="day-strip-section" aria-label={t.dayStripAriaLabel}>
        <div className="day-strip-header">
          <h3 className="section-title">{t.weeklyForecastTitle}</h3>
          <p className="section-hint">{t.weeklyForecastHint}</p>
        </div>
        {daySelectionError && (
          <p aria-live="polite" className="section-hint" role="status">
            {t.dateChangeFailed(daySelectionError)}
          </p>
        )}
        <div className="day-strip-scroll" data-testid="day-strip-scroll">
          <div
            className="day-strip"
            data-layout="single-row"
            data-testid="day-strip"
            style={{ ["--day-count" as string]: displayedDays.length }}
          >
            {displayedDays.map((day) => {
              const isSelected = day.date === forecast.target_date;
              return (
                <button
                  aria-current={isSelected ? "date" : undefined}
                  aria-pressed={isSelected}
                  aria-label={buildDayAriaLabel(day, t)}
                  className={`day-strip-card${isSelected ? " day-strip-card-selected" : ""}`}
                  data-testid={`day-card-${day.date}`}
                  disabled={loading}
                  key={day.date}
                  onClick={() => {
                    pendingFocusDateRef.current = day.date;
                    onSelectDate?.(day.date);
                  }}
                  ref={(node) => {
                    buttonRefs.current[day.date] = node;
                  }}
                  type="button"
                >
                  <span className="day-strip-head">
                    <span aria-hidden="true" className="day-strip-icon">
                      {dailyWeatherIcon(day.weather_code, day.weather)}
                    </span>
                    <span className="day-strip-date">
                      <span className="day-strip-date-main">{formatDayLabel(`${day.date}T00:00:00`)}</span>
                      <span className="day-strip-weekday">{formatWeekdayLabel(day.date, t)}</span>
                    </span>
                  </span>
                  <span className="day-strip-weather">{day.weather ?? t.weatherDataUnavailable}</span>
                  {day.aqi_forecast?.value != null && <span className={`aqi-dot aqi-${day.aqi_forecast.level}`} title={`${t.aqiLabel(day.aqi_forecast.value)} ${day.aqi_forecast.level ?? ""}`} aria-label={t.aqiLabel(day.aqi_forecast.value)} />}
                  <span className="day-strip-temp">
                    <strong>{t.highPrefix}{day.temp_high_c ?? "—"}°</strong>
                    <span>{t.lowPrefix}{day.temp_low_c ?? "—"}°</span>
                  </span>
                  {hasDailyPop(day.max_pop_percent) && (
                    <span className="day-strip-pop">{t.rainPrefix}{day.max_pop_percent}%</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <div
        aria-live="polite"
        className="summary-panel"
        data-source-dataset={forecast.source_dataset}
        data-summary-mode={ai_summary.mode}
      >
        <div className="summary-badges">
          <span className="badge">{t.badgeAdvice}</span>
          {showMockBadge && <span className="badge badge-muted">{t.badgeMock}</span>}
        </div>
        <p>{ai_summary.text}</p>
      </div>

      <div className="fact-grid">
        {sunrise && (
          <article className="fact-card sun-card atmosphere-card" data-testid="sun-atmosphere-card">
            <p className="fact-kicker">{t.kickerSun}</p>
            <CelestialArc
              label="sun"
              riseTime={sunrise.sunrise_time}
              setTime={sunrise.sunset_time}
              targetDate={forecast.target_date}
            />
            <small className="celestial-context">
              {sunrise.county} · {formatDateLabel(sunrise.target_date, t)}
              {sunrise.is_approximate ? ` · ${formatSunriseSourceLabel(sunrise.source_date, t)}` : ""}
            </small>
          </article>
        )}
        {uv && (
          <StatusGauge
            kind="uv"
            label={uv.source_label}
            value={uv.value}
            level={uv.level}
            levelCode={uv.level_code}
            maximum={14}
            detail={`${formatUvSourceLabel(uv.source_type, t)}${!showMockBadge && uv.station_name ? ` · ${t.stationPrefix}${uv.station_name}` : ""}`}
          />
        )}
        {aqi && (
          <StatusGauge
            kind="aqi"
            label={aqi.source_label}
            value={aqi.value}
            level={aqi.level}
            levelCode={aqi.level_code}
            maximum={300}
            detail={!showMockBadge && aqi.station_name ? `${t.stationPrefix}${aqi.station_name}` : ""}
          />
        )}
        {moon && (
          <article className="fact-card moon-card atmosphere-card" data-testid="moon-atmosphere-card">
            <p className="fact-kicker">
              {t.kickerMoon} <span>{moon.phase}</span>
            </p>
            <CelestialArc
              label="moon"
              riseTime={moon.moonrise_time}
              setTime={moon.moonset_time}
              targetDate={moon.source_date ?? moon.target_date}
              illuminationFraction={moon.illumination_fraction}
              waxing={moon.waxing}
              phaseName={moon.phase}
              phaseIcon={moon.icon}
            />
            <small className="celestial-context">{moon.county} · {formatDateLabel(moon.target_date, t)}</small>
          </article>
        )}
      </div>

      {chartForecast.hourly && chartForecast.hourly.length > 0 && (
        <HourlyForecastChart hourly={chartForecast.hourly} placeLabel={chartPlaceLabel} />
      )}
    </section>
  );
}

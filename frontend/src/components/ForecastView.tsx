import { memo, useEffect, useRef } from "react";
import { isMockForecast, type DailyForecast, type ForecastResult, type HourlyForecast } from "../lib/api";

function popColor(pop: number | null): string {
  if (pop === null) return "#cbd5e1";
  if (pop >= 70) return "#2563eb";
  if (pop >= 40) return "#60a5fa";
  return "#bae6fd";
}

function formatDateLabel(isoDate: string): string {
  const current = new Date(`${isoDate}T00:00:00`);
  const weekday = ["日", "一", "二", "三", "四", "五", "六"][current.getDay()];
  return `${current.getMonth() + 1}/${current.getDate()}（${weekday}）`;
}

function formatWeekdayLabel(isoDate: string): string {
  const current = new Date(`${isoDate}T00:00:00`);
  return `週${["日", "一", "二", "三", "四", "五", "六"][current.getDay()]}`;
}

function formatDayLabel(isoDateTime: string): string {
  const current = new Date(isoDateTime);
  return `${current.getMonth() + 1}/${current.getDate()}`;
}

function formatHourLabel(isoDateTime: string): string {
  const current = new Date(isoDateTime);
  return `${String(current.getHours()).padStart(2, "0")}:00`;
}

function slotIcon(slot: HourlyForecast): string {
  const code = slot.weather_code ?? "";
  if (code.startsWith("01")) return "☀️";
  if (code.startsWith("02") || code.startsWith("03")) return "🌤️";
  if (code.startsWith("04") || code.startsWith("05") || code.startsWith("06") || code.startsWith("07")) {
    return "☁️";
  }
  if (code.startsWith("08") || code.startsWith("09") || code.startsWith("10")) return "🌦️";
  if (code.startsWith("11") || code.startsWith("12") || code.startsWith("13") || code.startsWith("14")) {
    return "🌧️";
  }

  const weather = slot.weather ?? "";
  if (weather.includes("雷")) return "⛈️";
  if (weather.includes("雨")) return "🌧️";
  if (weather.includes("晴")) return "☀️";
  if (weather.includes("雲") || weather.includes("陰")) return "☁️";
  return "·";
}

function dailyWeatherIcon(weather: string | null): string {
  if (!weather) return "·";
  if (weather.includes("雷")) return "⛈️";
  if (weather.includes("雨")) return "🌧️";
  if (weather.includes("晴")) return "☀️";
  if (weather.includes("雲") || weather.includes("陰")) return "☁️";
  return "·";
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
          <h3>72 小時逐 3 小時預報</h3>
          <p>雙曲線為氣溫與體感溫度，底部藍柱為各時段降雨機率。</p>
        </div>
        <div className="chart-place-wrap">
          <p className="chart-place" data-testid="chart-place">
            {placeLabel}
          </p>
        </div>
        <div className="chart-legend">
          <span className="legend-item">
            <i className="legend-swatch legend-swatch-temp" />
            氣溫
          </span>
          <span className="legend-item">
            <i className="legend-swatch legend-swatch-apparent" />
            體感溫度
          </span>
        </div>
      </div>

      <div className="chart-shell">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="72 小時逐 3 小時溫度與降雨機率圖"
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
        <p className="chart-note">體感溫度資料不足時會略過紫色曲線，不影響其他時段資訊。</p>
      )}
    </section>
  );
});

function formatSunriseSourceLabel(sourceDate: string): string {
  return `參考 ${sourceDate} 天文資料`;
}

function formatUvSourceLabel(sourceType: string): string {
  return sourceType === "observation" ? "觀測值" : "預報值";
}

function hasDailyPop(pop: number | null): pop is number {
  return pop !== null;
}

function buildDayAriaLabel(day: DailyForecast): string {
  const parts = [
    formatDateLabel(day.date),
    day.weather ?? "天氣資料不足",
    `高溫 ${day.temp_high_c ?? "—"} 度`,
    `低溫 ${day.temp_low_c ?? "—"} 度`,
  ];
  if (hasDailyPop(day.max_pop_percent)) {
    parts.push(`降雨 ${day.max_pop_percent}%`);
  }
  return parts.join(" ");
}

export default function ForecastView({
  chartResult,
  result,
  loading = false,
  onSelectDate,
}: {
  chartResult?: ForecastResult;
  result: ForecastResult;
  loading?: boolean;
  onSelectDate?: (date: string) => void;
}) {
  const { forecast, ai_summary } = result;
  const chartForecast = chartResult?.forecast ?? forecast;
  const sunrise = forecast.sunrise_sunset;
  const uv = forecast.uv;
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
        {placeLabel} · {formatDateLabel(forecast.target_date)}
      </h2>

      <section className="day-strip-section" aria-label="七天預報選擇列">
        <div className="day-strip-header">
          <h3 className="section-title">
            本週預報
            {forecast.days.length > 1 ? `（共 ${forecast.days.length} 天）` : ""}
          </h3>
          <p className="section-hint">點選任一天，即可查看該日的行前建議與日出日落</p>
        </div>
        <div className="day-strip-scroll" data-testid="day-strip-scroll">
          <div
            className="day-strip"
            data-layout="single-row"
            data-testid="day-strip"
            style={{ ["--day-count" as string]: forecast.days.length }}
          >
            {forecast.days.map((day) => {
              const isSelected = day.date === forecast.target_date;
              return (
                <button
                  aria-current={isSelected ? "date" : undefined}
                  aria-pressed={isSelected}
                  aria-label={buildDayAriaLabel(day)}
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
                      {dailyWeatherIcon(day.weather)}
                    </span>
                    <span className="day-strip-date">
                      <span className="day-strip-date-main">{formatDayLabel(`${day.date}T00:00:00`)}</span>
                      <span className="day-strip-weekday">{formatWeekdayLabel(day.date)}</span>
                    </span>
                  </span>
                  <span className="day-strip-weather">{day.weather ?? "天氣資料不足"}</span>
                  <span className="day-strip-temp">
                    <strong>高 {day.temp_high_c ?? "—"}°</strong>
                    <span>低 {day.temp_low_c ?? "—"}°</span>
                  </span>
                  {hasDailyPop(day.max_pop_percent) && (
                    <span className="day-strip-pop">降雨 {day.max_pop_percent}%</span>
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
          <span className="badge">行前建議</span>
          {showMockBadge && <span className="badge badge-muted">示範資料</span>}
        </div>
        <p>{ai_summary.text}</p>
      </div>

      <div className="fact-grid">
        {sunrise && (
          <article className="fact-card">
            <h3>日出日落</h3>
            <p>
              {formatDateLabel(forecast.target_date)} 日出 {sunrise.sunrise_time ?? "—"} · 日落{" "}
              {sunrise.sunset_time ?? "—"}
            </p>
            <small>
              {sunrise.county}
              {sunrise.is_approximate ? ` · ${formatSunriseSourceLabel(sunrise.source_date)}` : ""}
            </small>
          </article>
        )}
        {uv && (
          <article className="fact-card">
            <h3>{uv.source_label}</h3>
            <p>
              指數 {uv.value ?? "—"} · {uv.level ?? "資料不足"}
            </p>
            <small>
              {formatUvSourceLabel(uv.source_type)}
              {!showMockBadge && uv.station_name ? ` · 測站 ${uv.station_name}` : ""}
            </small>
          </article>
        )}
      </div>

      {chartForecast.hourly && chartForecast.hourly.length > 0 && (
        <HourlyForecastChart hourly={chartForecast.hourly} placeLabel={chartPlaceLabel} />
      )}
    </section>
  );
}

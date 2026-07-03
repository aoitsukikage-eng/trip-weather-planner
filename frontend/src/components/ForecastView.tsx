import type { ForecastResult } from "../lib/api";

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

export default function ForecastView({ result }: { result: ForecastResult }) {
  const { forecast, ai_summary } = result;
  const sunrise = forecast.sunrise_sunset;
  const uv = forecast.uv;

  return (
    <section className="result">
      <h2>
        {forecast.town.city} {forecast.town.name} · {formatDateLabel(forecast.target_date)}
      </h2>

      <div className="summary-panel">
        <span className="badge">行前建議</span>
        <p>{ai_summary.text}</p>
        <small>模式:{ai_summary.mode} · 資料來源:{forecast.source_dataset}</small>
      </div>

      <div className="fact-grid">
        {sunrise && (
          <article className="fact-card">
            <h3>日出日落</h3>
            <p>
              日出 {sunrise.sunrise_time ?? "—"} · 日落 {sunrise.sunset_time ?? "—"}
            </p>
            <small>
              {sunrise.county}
              {sunrise.is_approximate ? ` · 對應資料日 ${sunrise.source_date}` : ""}
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
              {uv.source_type === "observation" ? "觀測值" : "預報值"}
              {uv.station_name ? ` · 測站 ${uv.station_name}` : ""}
            </small>
          </article>
        )}
      </div>

      <h3 className="section-title">
        本週預報
        {forecast.days.length > 1
          ? `（共 ${forecast.days.length} 天,已標示旅遊日 ${formatDateLabel(forecast.target_date)}）`
          : ""}
      </h3>
      <div className="cards">
        {forecast.days.map((day) => (
          <div
            className={`card${day.date === forecast.target_date ? " card-target" : ""}`}
            key={day.date}
          >
            <div className="card-date">
              {formatDateLabel(day.date)}
              {day.date === forecast.target_date ? " ★" : ""}
            </div>
            <div className="card-weather">{day.weather ?? "—"}</div>
            <div className="card-temp">
              {day.temp_low_c ?? "—"}° / <strong>{day.temp_high_c ?? "—"}°</strong>
            </div>
            <div className="pop-bar">
              <div
                className="pop-fill"
                style={{
                  width: `${day.max_pop_percent ?? 0}%`,
                  background: popColor(day.max_pop_percent),
                }}
              />
            </div>
            <div className="card-pop">降雨機率 {day.max_pop_percent ?? "—"}%</div>
            <div className="card-advice">{day.advice_hint}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

import type { ForecastResult } from "../lib/api";

function popColor(pop: number | null): string {
  if (pop === null) return "#cbd5e1";
  if (pop >= 70) return "#2563eb";
  if (pop >= 40) return "#60a5fa";
  return "#bae6fd";
}

export default function ForecastView({ result }: { result: ForecastResult }) {
  const { forecast, ai_summary } = result;
  return (
    <section className="result">
      <h2>
        {forecast.town.city} {forecast.town.name} · {forecast.target_date}
      </h2>

      <div className="ai-summary">
        <span className="badge">AI 行前建議</span>
        <p>{ai_summary.text}</p>
        <small>模式:{ai_summary.mode} · 資料來源:{forecast.source_dataset}</small>
      </div>

      <div className="cards">
        {forecast.days.map((d) => (
          <div className="card" key={d.date}>
            <div className="card-date">{d.date}</div>
            <div className="card-weather">{d.weather ?? "—"}</div>
            <div className="card-temp">
              {d.temp_low_c ?? "—"}° / <strong>{d.temp_high_c ?? "—"}°</strong>
            </div>
            <div className="pop-bar">
              <div
                className="pop-fill"
                style={{
                  width: `${d.max_pop_percent ?? 0}%`,
                  background: popColor(d.max_pop_percent),
                }}
              />
            </div>
            <div className="card-pop">降雨機率 {d.max_pop_percent ?? "—"}%</div>
            <div className="card-advice">{d.advice_hint}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

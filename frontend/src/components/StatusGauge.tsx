import { useLocale } from "../lib/locale";

export type SeverityTier = "good" | "moderate" | "poor" | "severe" | "hazard";

const UV_SEVERITY: Record<string, SeverityTier> = {
  低: "good",
  中: "moderate",
  高: "poor",
  過量: "severe",
  危險: "hazard",
};

const AQI_SEVERITY: Record<string, SeverityTier> = {
  良好: "good",
  普通: "moderate",
  對敏感族群不健康: "poor",
  對所有族群不健康: "severe",
  非常不健康: "hazard",
  危害: "hazard",
};

export function getSeverityTier(kind: "uv" | "aqi", level: string | null): SeverityTier {
  if (!level) return "good";
  return (kind === "uv" ? UV_SEVERITY : AQI_SEVERITY)[level] ?? "good";
}

export function getGaugeProgress(value: number | null, maximum: number): number {
  if (value === null || !Number.isFinite(value)) return 0;
  return Math.min(Math.max(value / maximum, 0), 1);
}

export default function StatusGauge({
  kind,
  label,
  value,
  level,
  maximum,
  detail,
}: {
  kind: "uv" | "aqi";
  label: string;
  value: number | null;
  level: string | null;
  maximum: number;
  detail: string;
}) {
  const { t } = useLocale();
  const severity = getSeverityTier(kind, level);
  const progress = getGaugeProgress(value, maximum);
  const valueLabel = kind === "uv" ? t.uvIndexLabel(value ?? "—") : t.aqiIndexLabel(value ?? "—");

  return (
    <article className={`fact-card status-gauge-card severity-${severity}`} data-severity={severity}>
      <p className="fact-kicker">{label}</p>
      <div
        className="status-gauge"
        data-testid={`${kind}-gauge`}
        data-progress={progress.toFixed(4)}
        aria-label={`${label} ${valueLabel} ${level ?? t.gaugeDataUnavailable}`}
      >
        <span className="status-gauge-fill" style={{ width: `${progress * 100}%` }} />
        <span className="status-gauge-handle" style={{ left: `${progress * 100}%` }} />
      </div>
      <p className="status-gauge-value">
        {valueLabel} · <span>{level ?? t.gaugeDataUnavailable}</span>
      </p>
      <small>{detail}</small>
    </article>
  );
}

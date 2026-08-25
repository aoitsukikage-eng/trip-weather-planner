import { useLocale } from "../lib/locale";

export type SeverityTier = "good" | "moderate" | "poor" | "severe" | "hazard" | "unknown";

const UV_CODE_SEVERITY: Record<string, SeverityTier> = {
  low: "good",
  moderate: "moderate",
  high: "poor",
  very_high: "severe",
  extreme: "hazard",
};

const AQI_CODE_SEVERITY: Record<string, SeverityTier> = {
  good: "good",
  moderate: "moderate",
  unhealthy_sensitive: "poor",
  unhealthy: "severe",
  very_unhealthy: "hazard",
  hazardous: "hazard",
};

export function getSeverityTier(
  kind: "uv" | "aqi",
  levelCode: string | null | undefined,
  value?: number | null,
): SeverityTier {
  let code = levelCode;
  if (!code && value != null && Number.isFinite(value)) {
    if (kind === "uv") {
      if (value <= 2) code = "low";
      else if (value <= 5) code = "moderate";
      else if (value <= 7) code = "high";
      else if (value <= 10) code = "very_high";
      else code = "extreme";
    } else {
      if (value <= 50) code = "good";
      else if (value <= 100) code = "moderate";
      else if (value <= 150) code = "unhealthy_sensitive";
      else if (value <= 200) code = "unhealthy";
      else if (value <= 300) code = "very_unhealthy";
      else code = "hazardous";
    }
  }

  if (!code) return "unknown";
  return (kind === "uv" ? UV_CODE_SEVERITY : AQI_CODE_SEVERITY)[code] ?? "unknown";
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
  levelCode,
  maximum,
  detail,
}: {
  kind: "uv" | "aqi";
  label: string;
  value: number | null;
  level: string | null;
  levelCode?: string | null;
  maximum: number;
  detail: string;
}) {
  const { t } = useLocale();
  const severity = getSeverityTier(kind, levelCode ?? null, value);
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

export interface CelestialArcProps {
  riseTime: string | null;
  setTime: string | null;
  targetDate: string;
  now?: Date;
  label: string;
  illuminationFraction?: number;
  waxing?: boolean;
  phaseName?: string;
  phaseIcon?: string;
}

function clockMinutes(value: string | null): number | null {
  if (!value || !/^\d{1,2}:\d{2}$/.test(value)) return null;
  const [hours, minutes] = value.split(":").map(Number);
  if (hours > 23 || minutes > 59) return null;
  return hours * 60 + minutes;
}

function localIsoDate(now: Date): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getArcProgress(
  riseTime: string | null,
  setTime: string | null,
  targetDate: string,
  now = new Date(),
): number | null {
  const rise = clockMinutes(riseTime);
  let set = clockMinutes(setTime);
  if (rise === null || set === null || targetDate !== localIsoDate(now)) return null;
  const current = now.getHours() * 60 + now.getMinutes();
  if (set < rise) set += 24 * 60;
  if (current < rise || current > set) return null;
  return (current - rise) / (set - rise);
}

export default function CelestialArc({
  riseTime,
  setTime,
  targetDate,
  now,
  label,
  illuminationFraction,
  waxing,
  phaseName,
  phaseIcon,
}: CelestialArcProps) {
  const progress = getArcProgress(riseTime, setTime, targetDate, now);
  const markerX = progress === null ? null : 10 + 180 * progress;
  const markerY = progress === null ? null : 84 - 144 * progress * (1 - progress);
  const hasPhaseMarker = illuminationFraction !== undefined && waxing !== undefined;
  const illumination = Math.min(1, Math.max(0, illuminationFraction ?? 0));
  const terminatorRadius = Math.abs(2 * illumination - 1) * 12;
  const sweep = waxing ? 1 : 0;
  const gradientId = `moon-terminator-${waxing ? "waxing" : "waning"}-${Math.round(illumination * 1000)}`;
  const gradientStart = waxing ? "0%" : "100%";
  const gradientEnd = waxing ? "100%" : "0%";
  const phasePath = markerX === null || markerY === null
    ? ""
    : `M ${markerX} ${markerY - 12} A 12 12 0 0 ${sweep} ${markerX} ${markerY + 12} A ${terminatorRadius} 12 0 0 ${sweep} ${markerX} ${markerY - 12} Z`;

  return (
    <svg className={`celestial-arc celestial-arc-${label}`} data-testid={`${label}-arc`} viewBox="0 0 200 108" role="img" aria-label={`${label}升落弧線`}>
      {hasPhaseMarker && (
        <defs>
          <linearGradient data-testid="moon-phase-gradient" id={gradientId} x1={gradientStart} x2={gradientEnd} y1="50%" y2="50%">
            <stop offset="0%" stopColor="#28435c" />
            <stop offset="45%" stopColor="#5f7890" />
            <stop offset="70%" stopColor="#d8d5b4" />
            <stop offset="100%" stopColor="#fff1b8" />
          </linearGradient>
        </defs>
      )}
      <path className="celestial-arc-path celestial-arc-track" data-testid={`${label}-arc-track`} d="M 10 84 Q 100 12 190 84" pathLength="1" />
      {progress !== null && (
        <path
          className="celestial-arc-path celestial-arc-traveled"
          data-testid={`${label}-arc-traveled`}
          d="M 10 84 Q 100 12 190 84"
          pathLength="1"
          strokeDasharray={`${progress} 1`}
        />
      )}
      <path className="celestial-horizon" d="M 4 84 H 196" />
      {markerX !== null && markerY !== null && (
        hasPhaseMarker ? (
          <g
            data-testid={`${label}-arc-marker`}
            data-illumination={illumination.toFixed(3)}
            data-waxing={String(waxing)}
            aria-label={`${phaseName ?? "月相"}${phaseIcon ? ` ${phaseIcon}` : ""}`}
          >
            <circle className="celestial-moon-shadow" cx={markerX} cy={markerY} r="12" />
            <path className="celestial-moon-terminator" data-testid="moon-phase-terminator" d={phasePath} fill={`url(#${gradientId})`} />
            <circle className="celestial-moon-surface-ring" cx={markerX} cy={markerY} r="12" />
          </g>
        ) : (
          <circle className="celestial-position" data-testid={`${label}-arc-marker`} cx={markerX} cy={markerY} r="4.5" />
        )
      )}
      <text className="celestial-arc-end-label celestial-arc-start-label" x="10" y="103">{riseTime ?? "—"}</text>
      <text className="celestial-arc-end-label celestial-arc-end-label-right" x="190" y="103">{setTime ?? "—"}</text>
    </svg>
  );
}

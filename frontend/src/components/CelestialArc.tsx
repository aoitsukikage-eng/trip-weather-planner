export interface CelestialArcProps {
  riseTime: string | null;
  setTime: string | null;
  targetDate: string;
  now?: Date;
  label: string;
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

export default function CelestialArc({ riseTime, setTime, targetDate, now, label }: CelestialArcProps) {
  const progress = getArcProgress(riseTime, setTime, targetDate, now);
  const markerX = progress === null ? null : 10 + 180 * progress;
  const markerY = progress === null ? null : 84 - 144 * progress * (1 - progress);

  return (
    <svg className={`celestial-arc celestial-arc-${label}`} data-testid={`${label}-arc`} viewBox="0 0 200 108" role="img" aria-label={`${label}升落弧線`}>
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
        <circle className="celestial-position" data-testid={`${label}-arc-marker`} cx={markerX} cy={markerY} r="4.5" />
      )}
      <text className="celestial-arc-end-label celestial-arc-start-label" x="10" y="103">{riseTime ?? "—"}</text>
      <text className="celestial-arc-end-label celestial-arc-end-label-right" x="190" y="103">{setTime ?? "—"}</text>
    </svg>
  );
}

export interface MoonPhaseDiscProps {
  illuminationFraction: number;
  waxing: boolean;
  phase: string;
  icon?: string;
}

export default function MoonPhaseDisc({ illuminationFraction, waxing, phase, icon }: MoonPhaseDiscProps) {
  const illumination = Math.min(1, Math.max(0, illuminationFraction));
  const terminatorRadius = Math.abs(2 * illumination - 1) * 40;
  const sweep = waxing ? 1 : 0;
  const path = `M 50 10 A 40 40 0 0 ${sweep} 50 90 A ${terminatorRadius} 40 0 0 ${sweep} 50 10 Z`;
  const gradientId = `moon-terminator-${waxing ? "waxing" : "waning"}-${Math.round(illumination * 1000)}`;
  const gradientStart = waxing ? "0%" : "100%";
  const gradientEnd = waxing ? "100%" : "0%";

  return (
    <svg className="moon-phase-disc" data-testid="moon-phase-disc" data-illumination={illumination.toFixed(3)} data-waxing={String(waxing)} viewBox="0 0 100 100" role="img" aria-label={`${phase}${icon ? ` ${icon}` : ""}`}>
      <defs>
        <linearGradient data-testid="moon-phase-gradient" id={gradientId} x1={gradientStart} x2={gradientEnd} y1="50%" y2="50%">
          <stop offset="0%" stopColor="#28435c" />
          <stop offset="45%" stopColor="#5f7890" />
          <stop offset="70%" stopColor="#d8d5b4" />
          <stop offset="100%" stopColor="#fff1b8" />
        </linearGradient>
      </defs>
      <circle className="moon-phase-shadow" cx="50" cy="50" r="40" />
      <path className="moon-phase-terminator" data-testid="moon-phase-terminator" d={path} fill={`url(#${gradientId})`} />
      <circle className="moon-phase-surface-ring" cx="50" cy="50" r="40" />
    </svg>
  );
}

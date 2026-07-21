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

  return (
    <svg className="moon-phase-disc" data-testid="moon-phase-disc" data-illumination={illumination.toFixed(3)} data-waxing={String(waxing)} viewBox="0 0 100 100" role="img" aria-label={`${phase}${icon ? ` ${icon}` : ""}`}>
      <circle className="moon-phase-shadow" cx="50" cy="50" r="40" />
      <path className="moon-phase-light" data-testid="moon-phase-light" d={path} />
      <circle className="moon-phase-outline" cx="50" cy="50" r="40" />
    </svg>
  );
}

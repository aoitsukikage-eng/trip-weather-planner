# Portfolio Home Mini Theme Bridge

Status: implemented and locally verified in `frontend-mini/`; not merged, integrated, pushed, or deployed.

The Portfolio iframe loads `?view=compact`; the deterministic review URL is `?view=compact&demo=1`.

```html
<iframe title="Trip Weather Planner" src="/labs/trip-weather/?view=compact" width="100%" height="420" loading="lazy"></iframe>
```

Desktop iframe: 1200 × 520 viewport; card target is 360–420px high (maximum 460px). Mobile iframe: 390 × 620 viewport; height may grow naturally. The in-card selector remains keyboard-operable and has a cyan `:focus-visible` outline; the card itself is not a link.

| Token | Value |
|---|---|
| panel | `linear-gradient(180deg, rgba(12,23,48,.94), rgba(8,18,38,.92))` |
| text / dim / muted | `#f4fbff` / `#b7ecff` / `rgba(183,236,255,.72)` |
| accent / focus | `#5be7ff` |
| border / strong | `rgba(91,231,255,.18)` / `rgba(91,231,255,.32)` |
| radius / shadow | `1.25rem` / `0 18px 44px rgba(91,231,255,.08)` |
| fonts | `Orbitron, Trebuchet MS, sans-serif` for Latin labels/numerals; `IBM Plex Sans, Noto Sans TC, Segoe UI, sans-serif` for body |
| warning | `rgba(255,107,122,.16/.46)`, `#ffd2d8` |
| AQI good | `rgba(95,214,148,.16/.42)`, `#c9ffe0` |
| UV attention | `rgba(255,177,87,.18/.46)`, `#ffd2a8` |

Spacing is 20px desktop / 18px mobile inner padding, 16px control gap, and 8px signal gap. The compact card deliberately has no seven-day rail; advice is visually clamped to two desktop lines while its full text remains in the `title` accessible description.

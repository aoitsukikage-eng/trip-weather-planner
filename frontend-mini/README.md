# Portfolio Trip Weather Mini

Independent React 18/Vite lab artifact for `/labs/trip-weather/`; it is implemented and locally verified on this feature branch, but is **not merged, pushed, integrated, or deployed**.

`npm test` runs the mini tests. `npm run build` writes the untracked artifact to `frontend-mini/dist/`. Set `VITE_TWP_API_BASE` to a public backend URL (or empty for same-origin) and optionally set `VITE_TWP_FULL_PLANNER_URL`. Before Portfolio production use, the backend must allow the exact Portfolio scheme/host/port in `CORS_ORIGINS` (never a wildcard); this task did not change runtime CORS.

The default CTA remains the Azure v1.0.0 Phase 1 legacy demo. `?demo=1` is deterministic and always labelled **Demo Data**; it is sample data, not live weather. The target backend must be schema-checked because the legacy deployment may not expose the audited newer fields. No provider keys belong in this app.

## Portfolio home card

Use `?view=compact` for the Portfolio embed card; `?view=compact&demo=1` is the deterministic capture/review mode. The compact card keeps the town selector inside its panel, renders today only, and exposes separate warning, AQI, and UV signals. Its `查看完整天氣預覽` link uses Vite `BASE_URL` and `target="_top"`, so an iframe exits to `/labs/trip-weather/`. Without `view=compact`, the standalone seven-day Mini and legacy Full Planner CTA remain unchanged.

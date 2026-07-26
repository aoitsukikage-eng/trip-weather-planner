# Trip Weather Planner — Developer Log

## 2026-07-02: P1 scaffold approved after Ubuntu takeover

### Summary

`Phase 1 mock scaffold` is now approved after the Ubuntu takeover and re-acceptance pass.

### What happened

- The project was first scaffolded as a no-credential Phase 1 mock build.
- The first acceptance round returned `changes_required` because Ubuntu linting hit `UP046` while the earlier Mac-side verification used an older `ruff` version.
- A follow-up takeover task moved the active development line to Ubuntu, aligned the lint toolchain, and re-ran the validation flow on Ubuntu.

### Accepted state

- Ubuntu is now the active development worktree.
- `ruff check` passes on Ubuntu.
- `pytest` passes on Ubuntu (`9 passed`).
- Frontend `npm run build` passes on Ubuntu.
- The existing `backend/`, `frontend/`, `docs/`, `infra/`, and `README.md` deliverables remain intact.

### Operational decision

- Ubuntu is the only active development mainline from this point onward.
- Mac SSD remains a git mirror / backup / management-document workspace only.

### Remaining follow-up

- The accepted Ubuntu fixes still need to be recorded as a new git commit.
- `VERIFICATION_REPORT.txt` should be kept consistent with the actual working-tree state after that commit.

### Reference artifacts

- Canonical plan: `docs/architecture_overview.md` and related design docs
- Acceptance: `cathay-cloud-intern-p1-ubuntu-takeover-and-reaccept-verification.md` (Ubuntu bridge)
- Management closure summary: `20260702-cathay-cloud-intern-phase1-closure-summary-codex-mac.md`

## 2026-07-02: Real-data execution handoff prepared

### Summary

External `CWA` and `TDX` credentials are now available, so the next execution
step is to move from mock-backed weather responses to real CWA-backed results.

### Decision

- The next Ubuntu coding task should focus on `Phase 1` real CWA integration.
- `TDX` is treated as credential-ready but still out of implementation scope for
  this immediate step.
- Mock mode must remain intact so the project stays demoable without secrets.

### Reference artifact

- Execution brief: `phase1_real_data_execution_brief.md` (not present in this repository snapshot)

## 2026-07-02: P1 live CWA integration approved

### Summary

`cathay-cloud-intern-p1-cwa-live-integration` is now approved.

### What happened

- The backend moved from mock-only weather responses to real `CWA`-backed
  responses while preserving the original no-credential fallback path.
- Live-mode validation confirmed non-mock upstream results across both the
  near-term and longer-range dataset families.
- The previous Ubuntu takeover fixes were folded into a real git commit on the
  Ubuntu mainline.

### Accepted state

- Ubuntu `ruff` passes.
- Ubuntu backend `pytest` passes (`14 passed`).
- Ubuntu frontend `npm run build` passes.
- Live queries return non-mock source metadata.
- Clearing `CWA_API_KEY` still returns deterministic mock data.
- Ubuntu repo head is now `5265d66 feat: integrate live CWA weather datasets`.

### Compatibility note

- The official `F-D0047-093` family endpoint returned `404 Resource not found`
  during live validation on 2026-07-02.
- The implementation therefore preserved the intended routing family while
  resolving transport calls to currently available county-level datasets.
- This was accepted as a compatibility fix rather than treated as a blocker.

### Reference artifact

- Acceptance: `cathay-cloud-intern-p1-cwa-live-integration-verification.md`

## 2026-07-02: Public demo readiness task launched

### Summary

The next Ubuntu task has been opened and launched as
`cathay-cloud-intern-p1-public-demo-readiness`.

### Decision

- The immediate next step is `deployment-readiness`, not fake deployment.
- `docker` is already available on Ubuntu, but `gcloud` is not yet installed.
- Therefore the current focus is to make Docker, Terraform, CI/CD, and the
  deployment runbook operationally ready so that a future cloud-auth card can
  execute a real public demo deployment with minimal design churn.

### Current direction

- Verify backend container build on Ubuntu.
- Tighten Terraform into deploy-ready shape.
- Add public demo deployment runbook and required input inventory.
- Keep `P1` live-data behavior stable while preparing the public-demo path.

## 2026-07-03: P1 public demo readiness approved

### Summary

`cathay-cloud-intern-p1-public-demo-readiness` is now approved.

### Accepted state

- Backend Docker build was verified on Ubuntu.
- Terraform was tightened into deploy-ready shape.
- A public demo runbook was added.
- A manual gated deploy workflow skeleton was added.
- README and deployment-related docs were updated to reflect a deployment-ready
  state without claiming a real cloud deployment.
- Containerized Terraform validation passed alongside backend/frontend quality
  checks.

### Boundary

- The project is now `deploy-ready, not actually deployed`.
- No real Cloud Run, GCS, Cloudflare, or public URL was claimed in this stage.
- External blockers remained platform auth and actual cloud deployment inputs.

### Reference artifact

- Acceptance: `cathay-cloud-intern-p1-public-demo-readiness-verification.md`

## 2026-07-03: Actual deploy card returned changes required

### Summary

`cathay-cloud-intern-p1-actual-deploy-and-public-url` returned
`changes_required`.

### Root cause

- The blocker was external rather than code-related.
- Ubuntu did not yet have a usable `gcloud` path.
- The repo remote still pointed at a local bundle rather than a real GitHub
  remote.
- Because of that, neither the Ubuntu manual deploy path nor the GitHub OIDC
  path could complete a real Artifact Registry push, Cloud Run deployment, or
  public smoke test.

### Decision

- Do not keep pushing on actual deploy under false assumptions.
- First unblock the deployment path itself, then relaunch actual deploy.

### Reference artifact

- Acceptance: `cathay-cloud-intern-p1-actual-deploy-and-public-url-verification.md`

## 2026-07-03: Deploy path unblock approved

### Summary

`cathay-cloud-intern-p1-deploy-path-unblock` is now approved.

### Accepted state

- `gcloud --version` is now available on Ubuntu.
- Repo `origin` is now a real GitHub remote:
  `https://github.com/aoitsukikage-eng/trip-weather-planner.git`
- `main` tracks `origin/main`.
- GitHub now exposes both the `CI` and `Deploy Demo` workflows for this repo.

### Remaining gap

- The blocker is no longer a missing deploy path.
- The remaining external prerequisite is now one of:
  - Ubuntu manual deploy: `gcloud auth login` + active target project
  - GitHub deploy: `GCP_WORKLOAD_IDENTITY_PROVIDER`,
    `GCP_SERVICE_ACCOUNT`, and `GCP_PROJECT_ID`

### Current project status

- `P1 scaffold`: approved
- `P1 live CWA integration`: approved
- `P1 public demo readiness`: approved
- `P1 deploy-path-unblock`: approved
- `P1 actual deploy and public URL`: ready to relaunch once one final deploy
  auth path is completed

## 2026-07-03: Actual deploy relaunch card prepared

### Summary

Management has prepared and dispatched a relaunched `actual deploy` card with a
stricter auth gate.

### Why this version is different

- The original `actual deploy` card had already proven that vague deploy-path
  assumptions were not enough.
- A fresh management-side recheck confirmed:
  - `origin` is already the real GitHub remote
  - `gcloud` exists on Ubuntu but is currently surfaced through login-shell
    pathing
  - no active `gcloud` account was detected
  - no target GCP project was detected

### Intent

- If a real GitHub OIDC or Ubuntu manual deploy path is now available, this
  relaunch should finish the real deployment.
- If not, it must stop quickly with a precise blocker report rather than
  producing another readiness-style answer.

## 2026-07-03: Actual deploy relaunch approved as precise blocker closure

### Summary

`cathay-cloud-intern-p1-actual-deploy-and-public-url-relaunch` is now
approved.

### Why it passed

- This approval does **not** mean the project is already deployed.
- It means the relaunched card correctly executed the deploy-path gate and
  stopped on the failure branch with precise, reproducible evidence.
- That behavior matched the relaunch card's intended acceptance path.

### Verified blocker facts

- `gcloud` is available in Ubuntu login-shell context.
- `gcloud auth list` still returns `No credentialed accounts.`
- `gcloud config get-value project` is still `(unset)`.
- GitHub `Deploy Demo` dry-run proved the workflow can start, but the deploy
  job did not proceed.
- GitHub repo deploy secrets are currently empty.

### Management conclusion

- The project is no longer in a vague "cannot deploy yet" state.
- The remaining deploy gap is now precisely narrowed to two external
  prerequisites:
  - Ubuntu manual path: active `gcloud` login plus target `GCP project`
  - GitHub OIDC path: required deploy secrets populated

### Reference artifact

- Acceptance:
  `cathay-cloud-intern-p1-actual-deploy-and-public-url-relaunch-verification.md`

## 2026-07-03: Ubuntu runtime smoke task opened

### Summary

Management opened a dedicated Ubuntu runtime smoke task to answer the
environment-level question that remained after deploy-path triage:

Can the current `Phase 1` app actually boot and serve basic flows on Ubuntu,
independent of cloud deployment?

### Decision

- Do not mix this question into Cloud Run / deploy auth work.
- Verify real service startup locally on Ubuntu first.
- Use the existing Ubuntu `backend/.env` if available, while still reporting
  whether runtime resolves to live mode or mock mode.

## 2026-07-03: Ubuntu runtime smoke approved

### Summary

`cathay-cloud-intern-p1-ubuntu-runtime-smoke` is now approved.

### Core answer

- The current `Phase 1` app really does run on Ubuntu.
- This is no longer just a build/test-ready project; runtime behavior has now
  been directly verified in the Ubuntu mainline environment.

### Verified runtime state

- Backend was actually started on Ubuntu and successfully served:
  - `root`
  - `/api/health`
  - `/api/towns`
  - `/api/forecast`
- The runtime path resolved to `live mode`.
- Response metadata confirmed live upstream sourcing, including:
  - `meta.source = F-D0047-093 via F-D0047-061`
  - `forecast.source_dataset = F-D0047-093 via F-D0047-061`
- Frontend was also actually started and rendered township data from the backend
  rather than relying on frontend-only fallback mock data.

### Runtime note

- A pre-existing port conflict was observed during the smoke process.
- The smoke run therefore used alternate ports `18082` and `5173`.
- Cleanup was confirmed afterward, and those smoke ports were left clear.

### Current management status

- `P1 scaffold`: approved
- `P1 live CWA integration`: approved
- `P1 public demo readiness`: approved
- `P1 deploy-path-unblock`: approved
- `P1 actual deploy relaunch`: approved as precise blocker closure
- `P1 ubuntu runtime smoke`: approved
- Remaining external gap: actual cloud deployment still waits on one deploy auth
  path being completed

### Reference artifact

- Acceptance:
  `cathay-cloud-intern-p1-ubuntu-runtime-smoke-verification.md`

## 2026-07-03: First user hands-on review; UX/data expansion card dispatched

### Summary

The user personally exercised the running app for the first time (Mac browser
through an SSH tunnel to the Ubuntu runtime, backend live on port 18082) and
returned product-level findings. Management triaged them against the code and
dispatched `cathay-cloud-intern-p1-ux-refresh-and-cwa-data-expansion`.

### User findings and triage

- Town dropdown covers only the curated 22-entry starter list. Code inspection
  confirmed the `towns.py` docstring promises full CWA-sourced coverage in live
  mode, but `/api/towns` unconditionally serves the static dict — the promise
  was never implemented.
- The date picker exposes a full calendar with year although the usable CWA
  horizon is ~7 days.
- The summary panel is branded `AI 行前建議` while actually running rule-based
  mode (no Gemini key on Ubuntu). User decision: ship a stable non-AI version
  first and rename the panel to `行前建議`; Gemini activation is deferred to a
  later phase.
- UV index and sunrise/sunset were expected but absent. Both are available from
  the same CWA platform and are now in scope.
- Management additionally found a real bug during triage: the summary always
  describes the first horizon day, not the user-selected travel date.

### Decisions

- In scope for the new card: full ~368-township live coverage with a
  county->township two-stage form, year-free 7-day date chips defaulting to the
  whole week, the target-date summary fix, honest panel labeling, CWA
  sunrise/sunset (A-B0062) and UV display, tolerant parsing hardened ahead of
  the announced 2026-07-06 CWA format change.
- Explicitly deferred by user decision: Gemini/AI summary activation and MOENV
  AQI integration. CWA weather warnings remain backlog.

### Reference artifact

- Task card: `bridge_task_cathay_cloud_intern_p1_ux_refresh_and_cwa_data_expansion.json`
  (also placed in the Mac bridge tasks folder for Ubuntu pickup)

## 2026-07-04: UX refresh and CWA data expansion approved

### Summary

`cathay-cloud-intern-p1-ux-refresh-and-cwa-data-expansion` is now approved.
The card was dispatched via the background-systemd pattern (unit
`twp-ux-refresh-20260703-235216`, gpt-5.4, fire-and-forget per user
instruction) and completed unattended with per-AC commits.

### Accepted state

- Live mode `/api/towns` returns 368 townships aggregated from the 22
  county-level `F-D0047-091` datasets; mock mode still returns the
  deterministic 22-town starter list.
- Frontend `TripForm` is now a county -> township two-stage form; date UI is
  year-free 7-day chips and the full week renders by default.
- The summary panel is renamed `行前建議` and now describes the selected
  target date (wrong-day bug fixed).
- Sunrise/sunset served from `A-B0062-001` and UV from `O-A0005-001` with
  nearest-station mapping via `O-A0001-001`; all new parsers are tolerant.
- `ruff`, backend `pytest` (21 passed), and frontend `npm run build` all pass;
  changes are committed per-AC and pushed to origin (`ebdcfdd`).

### Operational notes for future testing

- Live-mode town codes changed scheme: they are now CWA-sourced codes such as
  `cwa-65000260` (貢寮區), not the old starter slugs like
  `newtaipei-gongliao`. Always read codes from the live `/api/towns` response.
- Sunrise/sunset under the current key may return an approximate row
  (`is_approximate=true`, `source_date` shown honestly in the UI). Worth
  rechecking dataset coverage before the exam demo.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-ux-refresh-and-cwa-data-expansion-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-ux-refresh-and-cwa-data-expansion-verification.md`

## 2026-07-04: 72h hourly chart approved

### Summary

`cathay-cloud-intern-p1-72h-hourly-chart` is now approved. Dispatched via the
same background-systemd pattern (unit `twp-72h-chart-20260704-004206`,
gpt-5.4, fire-and-forget) and completed unattended with per-AC commits.

### Accepted state

- Backend exposes normalized 3-hourly slices (`hourly`) in the forecast
  payload when the window overlaps the next 72h; live tomorrow-query for
  貢寮區 returned 56 slices via `F-D0047-093 via F-D0047-069`.
- Frontend renders a CWA-website-style 72h chart (inline SVG, dual
  temperature curves, weather icons, PoP) with honest 逐3小時 labeling; no
  heavy chart dependency was added.
- Beyond-72h queries show daily cards only; mock mode renders the chart from
  24 deterministic slices.
- ruff / pytest / npm run build all pass; `main` aligned with `origin/main`,
  worktree clean.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-72h-hourly-chart-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-72h-hourly-chart-verification.md`

## 2026-07-04: Date timezone off-by-one and horizon stabilization approved

### Summary

`cathay-cloud-intern-p1-date-tz-and-horizon-fix` (P0) is now approved. Found
by the user testing at 01:17 local time: every clicked date chip submitted the
previous day.

### Root cause and fixes

- `toISOString().slice(0,10)` serialized local dates via UTC; before 08:00
  Asia/Taipei this shifted every date back one day. Replaced with
  local-calendar serialization (regression-tested).
- The failed validation was silently masked by the frontend inline-mock
  fallback; now 4xx surfaces a visible error and mock fallback triggers only
  on network failure.
- Backend `today..today+6` validation is now anchored to `Asia/Taipei`.
- Week view and 72h chart are stable across chip selections (weekly + near
  datasets merged); the chip drives advice focus and highlight only.
- Sunrise/sunset resolves the exact target-date row from `A-B0062` (full-year
  data); non-today UV is labeled 僅供參考.

### Accepted state

- backend ruff + pytest 27 passed; frontend 7 tests + build pass.
- HEAD `67c10ef`, `main` aligned with `origin/main`, worktree clean.

### Known remaining chart defect (next card)

- Live near-term feed mixes 1-hourly (~first 48h) and 3-hourly slices; the
  chart draws every point, so the hourly segment renders overlapping
  labels/icons. Queued as `cathay-cloud-intern-p1-72h-chart-polish` together
  with showing the queried county+township in the chart header.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-date-tz-and-horizon-fix-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-date-tz-and-horizon-fix-verification.md`

## 2026-07-04: 72h chart polish approved

### Summary

`cathay-cloud-intern-p1-72h-chart-polish` is now approved (unit
`twp-chart-polish-20260704-014610`, dispatched immediately after the tz-fix
acceptance).

### Accepted state

- Backend normalizes the mixed 1h/3h CWA near-term slices into uniform
  3-hour buckets (live spot check: 56 raw slices -> 32 normalized, adjacent
  slots verified at 3h).
- Chart section header shows the queried 縣市＋鄉鎮 and follows the query
  result, not the in-progress form selection.
- High-density annotations are thinned while curves/bars keep full
  resolution; mock chart stays deterministic.
- backend ruff + pytest 29 passed; frontend 10 tests + build pass.
- HEAD `058ba3d`, `main` aligned with `origin/main`, worktree clean.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-72h-chart-polish-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-72h-chart-polish-verification.md`

## 2026-07-05: UI simplification approved — frontend reaches final P1 form

### Summary

`cathay-cloud-intern-p1-ui-simplification` is now approved (unit
`twp-ui-simplify-20260705-004656`). This closes the third user hands-on
review round; the frontend is now in its converged P1 shape.

### Accepted state

- Date-chip row removed; the region-only form queries and the 7-day cards
  themselves are the date selector (click switches highlight, 行前建議 and
  日出日落 via cached re-query; keyboard-accessible, no scroll jump).
- All technical mode/source strings purged from the visible UI; mock data
  shows a single 示範資料 badge only.
- Sunrise/sunset card labels its travel date; approximate-source copy is
  friendlier while staying honest.
- 72h chart header shows the enlarged, centered 縣市＋鄉鎮 label.
- backend ruff + pytest 29 passed; frontend 12 tests + build pass.
- HEAD `ec4a13b`, `main` aligned with `origin/main`, worktree clean; scope
  confirmed frontend-only relative to `058ba3d`.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-ui-simplification-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-ui-simplification-verification.md`

## 2026-07-05: Day-strip layout approved — P1 frontend final form

### Summary

`cathay-cloud-intern-p1-day-strip-layout` is now approved (unit
`twp-day-strip-20260705-012725`). This is the last planned P1 frontend card.

### Accepted state

- Result layout is now: query form -> single-row 7-day strip -> 行前建議 +
  日出日落 + UV -> 72h chart, so the date selector and the content it drives
  share one viewport.
- Strip cells show date+weekday, weather icon, high/low, PoP%; per-cell
  advice hints removed; selection updates advice/sunrise in place with no
  scroll jump; narrow viewports scroll the strip inside its container.
- backend ruff + pytest 29 passed; frontend 13 tests + build pass.
- HEAD `40eaf1a`, `main` aligned with `origin/main`, worktree clean;
  frontend-only scope confirmed relative to `ec4a13b`.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-day-strip-layout-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-day-strip-layout-verification.md`

## 2026-07-05: Day-card refinement dispatched; blocked on Codex quota, auto-relaunch scheduled

### Review round findings (user hands-on, 02:20)

- 降雨 —% on days 4-7 was verified by management against the live API: CWA
  publishes PoP only for the first ~3 days of the weekly township forecast;
  `max_pop_percent` is null from day 4 onward. This is upstream data coverage,
  not a backend bug. Decision: hide the 降雨 row entirely when null.
- Horizontal scrollbar evaluation: at laptop width the scrollbar is NOT a
  necessary evil — current strip cells are ~280px wide (inherited spacious
  layout, icon floated far right). Compressed ~150-170px cells fit 7-in-a-row
  within ~1280px. Mobile (<~700px) keeps container-internal horizontal scroll
  as the industry-standard tradeoff.
- Design decision: the user prefers the pre-strip card visual language
  (commit `ec4a13b`) over the minimal strip. The new card is a slimmed
  single-row version of that design (icon moved left beside the date), not a
  new invention. Git history confirmed intact per-AC on origin, so `ec4a13b`
  serves as the design reference.

### Dispatch and quota incident

- `cathay-cloud-intern-p1-day-card-refinement` dispatched as unit
  `twp-day-card-refine-20260705-023122`; preflight passed but codex exec
  failed immediately: ChatGPT plan usage limit reached (six cards executed
  within ~24h), quota resets 04:56.
- Mitigation: a one-shot systemd user timer
  (`twp-day-card-refine-relaunch.timer`) re-runs the same launcher at 05:00
  unattended. No card content changed.

### Project status snapshot (as of this entry)

- Approved chain: scaffold -> live CWA -> demo readiness -> deploy-path
  unblock -> runtime smoke -> UX refresh (368 towns/UV/sunrise) -> 72h chart
  -> tz fix -> chart polish -> UI simplification -> day-strip layout.
- In flight: day-card refinement (auto-relaunch 05:00).
- Waiting on user: deploy auth (gcloud login + GCP project, or GitHub OIDC
  secrets) for the actual public-URL deployment; Gemini activation decision.
- Deferred by decision: Gemini summary activation, MOENV AQI. Backlog: CWA
  weather warnings.
- Submission deadline: 2026-07-06 12:00.

## 2026-07-05: Day-card refinement approved after account-swap relaunch

### Summary

`cathay-cloud-intern-p1-day-card-refinement` is now approved (unit
`twp-day-card-refine-20260705-024549`). The first launch failed on the Codex
ChatGPT quota; the user swapped accounts, management verified the new account
with a probe call, cancelled the 05:00 fallback timer, and relaunched
immediately — the relaunch completed normally.

### Accepted state

- Day cells rebuilt on the ec4a13b card visual language, compressed: icon
  beside the date group, ~single-row fit at 1280px desktop width with no
  horizontal scrollbar; narrow viewports keep container-internal scroll.
- Null-PoP days (CWA publishes PoP only for the first ~3 days) no longer
  render a 降雨 row at all — no dash placeholder.
- Click/keyboard day switching and in-place advice/sunrise updates intact.
- ruff / pytest / frontend tests / build all pass; `40eaf1a..3622a0a`
  touched only 3 frontend files; `main` aligned with `origin/main`.

### P1 frontend is now feature-complete and review-converged

Nine functional cards approved in total. Remaining project work is
non-frontend: deploy auth -> actual public-URL deployment, the Gemini
activation decision, and submission polish.

### Reference artifacts

- Task Report: Ubuntu bridge
  `reports/coding/task-cathay-cloud-intern-p1-day-card-refinement-codexcli-report.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-day-card-refinement-verification-20260705.md`

## 2026-07-05: Selected-state polish approved; two review findings queued

### Summary

`cathay-cloud-intern-p1-selected-state-polish` is approved (HEAD `0f45607`):
the 已選擇 text is gone, selection reads through deeper border/background/
shadow, and `aria-pressed` / `aria-current="date"` preserve assistive
semantics.

### Review findings from the same user session (queued as next card)

- 72h chart data shifted when clicking different day cards. Verified root
  cause: the per-date cache key triggers fresh upstream fetches whose CWA
  issuance snapshots differ, and the chart is bound to the latest clicked
  response. The chart's semantics are "72h from now" and must be pinned to
  the region query's first response, untouched by day clicks.
- While the demo backend was down, the frontend inline mock walked the week
  forward indefinitely (screenshot showed October): `mockForecast(town,
  date)` anchors the generated week at the REQUESTED date with no window
  clamp. Real backend validates today..today+6 (Asia/Taipei) so this is
  mock-path-only, but the mock must mirror backend semantics: anchor today,
  clamp to the 7-day window.
- Management verified there are no hardcoded dates anywhere: backend anchors
  to `datetime.now(ZoneInfo("Asia/Taipei")).date()`, frontend uses a
  `todayIsoDate()` helper, and a repo-wide grep for literal dates hit zero.
- Plus a UX copy addition: a short hint near 本週預報 telling users day
  cards are clickable.

## 2026-07-05: Chart-pin/hint/mock-fix and sunrise exact-date fix both approved

### Chart-pin / hint / mock-fix (approved)

- 72h chart is now pinned to the region query's first response — day-card
  clicks no longer re-render it; only a new region query refreshes it.
- Hint copy added beside 本週預報. Mock week now anchors at today with a
  today..today+6 clamp (the walk-to-October defect is gone). User confirmed
  the 72h chart behaves correctly in live testing.

### Sunrise exact-date fix (P0, approved)

- User caught that sunrise/sunset was identical for every selected day and
  always cited 參考 2025-06-29 天文資料 — the earlier exact-date promise had
  never worked in live mode. Root cause: `fetch_sunrise_sunset()` called
  A-B0062-001 with no query params and one shared cache key, so CWA returned
  a stale default slice and the approximate fallback fired every time. This
  was an acceptance gap in the tz-fix card: the behavior passed at test level
  but was never exercised live.
- Fix (management pre-verified the exact request against CWA): pass
  CountyName + Date, cache per county+date, exact rows carry
  is_approximate=false and the UI drops the caveat line; approximate fallback
  survives only for genuine upstream gaps.
- Post-fix spot check (新北市, live): 7/5 sunrise 05:09, 7/7 05:10, 7/10
  05:11 — per-day variation confirmed, all exact rows.

### Reference artifacts

- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-chart-pin-hint-mock-fix-verification-20260705.md`
- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-sunrise-exact-date-fix-verification-20260705.md`

## 2026-07-05: Horizon window alignment approved (P0)

### Summary

`cathay-cloud-intern-p1-horizon-window-alignment` is approved. User bug:
clicking the 7/12 card refreshed the page and reset to 7/5. Root cause:
CWA's evening issuance rolled the weekly horizon to 8 days (7/5..7/12), but
the backend window was hardcoded today..today+6 — it rejected a date present
in its own response (HTTP 400), and the frontend error path fell back to the
default view.

### Accepted state

- Backend now pre-screens with today..today+10 (Asia/Taipei) then validates
  against the ACTUAL forecast horizon — every rendered day card is clickable;
  past and far-future dates still return 400.
- Heading is dynamic (共 N 天). Day-click failures keep the current week
  view and show an inline 日期切換失敗 message instead of resetting.
- ruff / pytest / npm test / build all pass; per-AC commits pushed
  (`cc4d6b9..e644923`).
- No quota incident this run (user suspected one; event log showed 0 errors
  — the earlier swap to a fresh Codex account stands for future runs).

### Bookkeeping note (traceability)

- The acceptance report for THIS card was filed under the older card's name:
  `task-cathay-cloud-intern-p1-date-tz-and-horizon-fix-verification-20260705.md`,
  and the coding agent's final message cited a report filename differing from
  the landed one. Content verified correct; map these filenames to
  `horizon-window-alignment` when tracing history.

### Lesson

- The demo session straddled CWA's evening issuance, which changed the data
  shape (7 -> 8 days) and exposed the hardcoded window — boundary conditions
  tied to upstream publish cycles are worth testing deliberately.

## 2026-07-05: Seven-day trim and visual revert approved (P0) — horizon card outcome corrected

### Summary

User REJECTED the visible outcome of the horizon-alignment card: 8 squeezed
cards with added box/gridline emphasis. Product ruling (user, confirmed by
management): the week is exactly today + 6 following days = 7 cards; the 8th
entry in CWA's evening issuance is partial-day residue, not a forecast day —
the official CWA site also shows 7. The previous card's acceptance criterion
("every rendered day must be clickable") pointed the implementation the wrong
way (render 8 → make 8 clickable) — a management spec error, recorded here.

### Accepted state

- Backend trims the daily horizon strictly to Asia/Taipei today..today+6;
  the 8th-day residue no longer appears in API responses.
- Heading fixed back to 本週預報（共 7 天）; day-card visuals restored to
  the approved 3622a0a baseline; the added gridline emphasis is gone (the
  點選任一天 hint is sufficient affordance).
- Kept invisible defenses: inline day-click error resilience, loose backend
  pre-screen + horizon validation (dormant now), pinned 72h chart, exact
  sunrise, selected-state styling.
- ruff / pytest / npm test / build all pass; per-AC commits pushed
  (`b30eab7..ac4bfdc`); verified under live 8-day upstream conditions.

### Reference artifacts

- Acceptance: Ubuntu bridge
  `reports/acceptance/task-cathay-cloud-intern-p1-seven-day-trim-and-visual-revert-verification-20260705.md`

## 2026-07-05: Strip shadow-clip line removed — frontend converged

### Summary

`cathay-cloud-intern-p1-strip-shadow-clip-fix` approved. The hard horizontal
line under the 7-day strip was the day-card drop shadow being clipped flat by
a leftover `overflow-y: hidden` on `.day-strip-scroll` (a relic of the
horizontal-scroll-container era). Desktop no longer clips vertically; the
mobile scroll container keeps room for the shadow. CSS-only change
(`9a2c665..ee6d8ff`); all suites pass.

With this, the P1 frontend is visually and functionally converged across all
user review rounds (16 approved cards total). Remaining work is external:
deploy auth -> public URL, Gemini decision, submission polish. Deadline
2026-07-06 12:00.

## 2026-07-05: User confirmed convergence; management docs committed to mainline

### Summary

The user retested the running demo and confirmed all fixes are in place —
the P1 frontend is declared converged. Management synchronized the full
development log (this file) and all 16 task cards from the Mac management
workspace into the Ubuntu mainline repo so the submission carries the
complete, traceable development history.

### Branching decision

Management recommendation, agreed direction: `main` is frozen as the
submission baseline. Any further UI/UX or visual polish work goes to a
short-lived feature branch (e.g. `feat/ui-polish`) off `main`, merged via PR
with CI green — consistent with the project's trunk-based workflow
(docs/git_workflow.md). No speculative polish before the deadline; the only
remaining pre-submission work is deploy auth -> actual deploy -> public URL,
the Gemini activation decision, and README/docs finalization.

## 2026-07-05: Azure delivery platform locked

### Summary

Delivery Phase 2 moved from "deploy-ready" to a concrete Azure-for-Students
deployment plan. Management cross-reviewed the viable Azure surfaces before
the user made the final platform call.

### Decision

- Backend deployment would use Azure Container Apps, not App Service.
- Infrastructure would keep a pure Azure story; clouds that were not actually
  used would not appear in the final deliverables.
- Terraform would be rewritten around the AzureRM provider instead of carrying
  the earlier non-Azure deployment shape forward.
- Bicep remained a reasonable Azure-native alternative, but Terraform was kept
  because the repo already had Terraform conventions and CI entry points.
- Static Web Apps proxying was rejected after Free-tier constraints made it a
  poor fit for the required backend integration path.

### Trade-off

Container Apps was the more explicit operations choice: it required container
registry and revision thinking, but it also matched the backend's packaged
runtime and left a cleaner path for secrets, scaling, and public smoke checks.

## 2026-07-05: Azure deployment sprint completed with constrained fallbacks

### Summary

The backend reached a public Azure runtime through ACR Basic and Azure
Container Apps. The sprint also exposed two student-subscription constraints
that forced pragmatic fallback decisions.

### What changed

- The target subscription policy allowed `southeastasia`; an attempted
  `eastasia` path was rejected, so the deployment moved to the allowed region.
- `az acr build` was not usable under the student-subscription limits, so the
  image path switched to local build plus registry push.
- Container Apps was configured with scale-to-zero behavior and a small
  resource profile (`0.5 vCPU`, `1 GiB`) suitable for a demo workload.
- Static Web Apps was tested across all available regions for this account
  shape and was treated as structurally unavailable after policy rejections.
- The frontend fell back to Azure Storage static website hosting, which gave a
  working public static endpoint.
- CORS was tightened in a second pass after both frontend and backend URLs were
  known.

### Lesson

The fallback was not a downgrade in delivery quality. It narrowed the demo to
services the student subscription could actually provision, which is better
than presenting an elegant architecture that cannot be reproduced.

## 2026-07-06: Late-night incident proved the GitHub recovery path

### Summary

During the final delivery window, campus network access failed and the primary
development machine became unreachable. GitHub became the single source of
truth, and the work transferred cleanly to a backup workstation through a
fresh clone.

### Recovery

- No code or documentation state was lost because the active delivery state had
  already been pushed.
- The infrastructure card was re-dispatched and completed from the backup
  workstation.
- Terraform was rewritten into a pure AzureRM shape.
- A GitHub Actions OIDC deployment skeleton was added to preserve the intended
  future automation path without claiming a fully wired production workflow.
- Acceptance caught two workflow self-consistency issues, then the fixes landed
  immediately: storage commands needed login auth mode, and Container Apps
  secrets needed the correct update command path.

### Lesson

The incident validated the remote-first workflow but also exposed a process
rule: acceptance snapshots and active coding cards must not overlap on the
same moving target. The snapshot should wait until the coding card has landed
or explicitly state that it is reviewing an in-progress state.

## 2026-07-06: Public submission closed with sanitized delivery evidence

### Summary

Delivery closed with the repository made public, the live demo submitted, and
the internal development narrative retained in sanitized form under
`dev-process/`.

### Accepted state

- The frontend and backend demo URLs were both live for submission.
- The repository was converted to public visibility.
- `gitleaks` full-history scanning returned zero findings.
- Development records were kept because they explain the decision trail, but
  operationally sensitive details were removed or generalized.
- The final documentation tells the Azure deployment story that actually
  happened: Container Apps for the backend and Storage static website hosting
  for the frontend.

### Trade-off

The final submission favors reproducible truth over architectural symmetry.
Static Web Apps would have been a cleaner single-brand frontend story, but the
working Azure Storage fallback better represents the platform constraints and
keeps the demo honest.

## 2026-07-09: Phase 2 kickoff — destination suitability completion

### Summary

Phase 1 was submitted on 2026-07-06 and passed the Cathay review. The `main`
branch (`2f3ce32`) and the Azure public demo are now a frozen, stable baseline
kept intact for the interview period. Phase 2 development starts today on a
new branch `phase2-dev`, created from that baseline.

### Operating decisions

- All Phase 2 work happens on `phase2-dev`; `main` receives no direct commits.
- The branch is intentionally not pushed to origin and the Azure demo is not
  redeployed. Development and verification run on the Ubuntu workstation only,
  so the public Phase 1 demo stays exactly as reviewed.
- The management/coding/acceptance bridge workflow validated in Phase 1
  continues unchanged.

### Scope

Phase 2 resumes the original three-source plan
(`docs/dev-process/台灣公開API接入清單_旅行目的地評估.md`) by completing the
"is this destination worth going" storyline before moving to "what to do
there":

1. MOENV air quality: real-time AQI via nearest-station mapping (same pattern
   as the existing UV card) plus the official 3-day air-quality-zone forecast
   (`aqx_p_408`, issued 10:30/16:30/22:00 daily).
2. CWA weather warnings and typhoon advisories (`W-C0033` family), carried
   over from the Phase 1 backlog; zero new credentials required.
3. Astronomy extension: moonrise/moonset with moon phase, joining the existing
   sunrise/sunset fact card family.
4. TDX tourism (scenic spots / restaurants / activities) as a later card;
   OAuth2 client credentials are already provisioned in the Ubuntu `.env`.

### UI decisions agreed with the user

- Warnings render as a conditional full-width alert banner between the header
  and the 7-day strip: zero footprint on calm days, severity-colored, stacks
  naturally on mobile. Side columns were rejected because they do not survive
  the mobile single-column collapse.
- Current AQI and the moon card extend the existing auto-fit fact-card grid.
- The 3-day AQI forecast integrates into existing components: a small
  color-coded dot on the first three day-strip cards and AQI-aware wording in
  the selected-day advice panel. No new layout region is introduced.

### Pending

- MOENV open-data platform registration (instant email key) is the only
  missing credential; `GEMINI_API_KEY` stays empty until the AI-summary card
  is scheduled.

## 2026-07-15: P2-1 first pass rejected — changes_required

### Summary

The background unit for `task-20260715-twp-p2-suitability` completed and
delivered the MOENV/warnings/moon adapters plus the agreed UI integration in a
single commit (`ed64802`). Lint, both test suites, and the frontend build were
green and mock mode stayed intact. Acceptance (Codex VS) nevertheless returned
**changes_required** with four blockers, and management triage confirmed all
four — with one responsibility correction.

### Findings and triage

- MOENV live parsing is broken (card-introduced). The adapter only accepts a
  dict payload and reads `records`, but MOENV v2 returns a top-level JSON
  list for both `aqx_p_432` and `aqf_p_01`, so live AQI resolves to empty.
  The task card's dataset notes had documented the list shape; the agent
  tested only against its own dict-shaped mocks.
- `date_out_of_range` for "today" near 23:00 is NOT a card regression:
  the horizon logic (`trim_daily_to_window` + `_horizon_contains_date`)
  exists in the frozen Phase 1 baseline (`e7ae6a0`). Late at night the CWA
  live horizon starts tomorrow, so the frontend's default today query 400s.
  Pre-existing live E2E gap, surfaced by late-night verification; scheduled
  into the fix card because it breaks the default flow for real users.
- Required mock-based tests (S7) were not written at all; the green suites
  are pre-existing coverage only.
- AC10 (one commit per acceptance criterion) was violated: one squashed
  commit for the whole card.

### Decisions

- Keep `ed64802` as-is: rewriting history to fake per-AC commits after the
  fact records a process that did not happen. The deviation is logged here;
  per-AC commits are enforced as a hard acceptance item on the fix card.
- Dispatched `task-20260715-twp-p2-suitability-fix1` (background-systemd,
  gpt-5.6-terra/medium): F1 tolerant list/dict MOENV parsing with live-shape
  list fixtures in tests, F2 graceful handling when today is outside the live
  horizon (default query must never 400; focus the earliest available day
  with honest wording), F3 full S1-S6 mock-based test coverage including the
  two-state warning banner component test, F4 per-AC commit discipline.

### Lesson

Adapter tests must pin fixtures to the observed live payload shape, not to
the shape the implementer assumed. The card had the live shape documented;
the miss was in test discipline, which is exactly what F3 restores.

## 2026-07-20: P2-1 fix1 approved — destination suitability signals shipped

### Summary

`task-20260715-twp-p2-suitability-fix1` passed acceptance (Codex VS, Ubuntu):
編碼驗收 pass、執行驗收 pass、結論 approved, no required actions. This closes
out the P2-1 card (parent `task-20260715-twp-p2-suitability` is archived as
superseded; its changes_required findings were fully addressed by fix1).

### What shipped on phase2-dev

- MOENV adapter tolerates both top-level list and `records`-wrapper payload
  shapes (the live-shape bug that blocked AC4/AC5 on the first pass).
- Current AQI via nearest-station mapping (aqx_p_432) and 3-day zone AQI
  forecast (aqf_p_01, county->zone static mapping) both verified live:
  `aqi_forecast_days=3`, AQI value present with level label.
- Graceful handling when "today" falls outside the live CWA horizon: the
  backend shifts focus to the earliest available day and returns additive
  `requested_date` / `date_adjusted` fields instead of a 400; the frontend
  surfaces an honest adjustment notice. Explicit far-future dates still 400
  with `date_out_of_range`. Verified live 2026-07-20: request for today
  (2026-07-20) returned 200 with `date_adjusted=true`, focused on
  2026-07-21; a far-future date correctly 400'd.
- CWA weather-warning banner and moon (moonrise/moonset + phase) card, both
  covered by mock-based component tests (active/no-warning two-state banner,
  moon card render).
- Full mock-based test coverage for S1-S6 (backend 36 passed, frontend 24
  passed), zero-credential mode reverified green, ruff clean, frontend build
  clean.

### Process outcome

- Acceptance independently reran every check rather than trusting the coding
  agent's self-report (ruff, pytest, frontend tests/build, live smoke) — all
  matched the Task Report.
- Per-AC commit discipline (F4) held this round: 7 commits, one per AC
  (`67c78c4`..`e67e3b7`), verified against `a40da57..HEAD`.
- No red-line files touched (README.md, .github/workflows/**,
  infra/terraform/**, .env); no key material found in the diff; no git push
  to any remote — phase2-dev stays local-only per the Phase 2 operating
  decision, main and the Azure demo remain untouched.

### Task bookkeeping

- `task-20260715-twp-p2-suitability` -> archived (superseded by fix1)
- `task-20260715-twp-p2-suitability-fix1` -> completed

### Next

P2-2: TDX tourism (scenic spots / restaurants / activities) is next in the
Phase 2 queue; OAuth2 client credentials are already provisioned in the
Ubuntu backend/.env. After that, Gemini AI-summary activation once the
AQI/warning context enriches the advice material.

## 2026-07-22: P2-2 celestial visuals approved — redesign + moon county label

### Summary

Three cards shipped as one user-facing feature: `task-20260721-twp-p2-celestial-arc`
(sun/moon horizon arcs + moon phase disc, data plumbing), `task-20260721-twp-p2-celestial-redesign`
(visual overhaul after user feedback), and `task-20260721-twp-p2-moon-county-label`
(moon card location parity fix). All three passed acceptance (Codex VS) with
independently rerun checks; no required actions on either of the final two
reports.

### What changed since the first pass

User reviewed the initial celestial-arc implementation live and called it out
as visually poor: a single flat-color arc with no elapsed/remaining contrast,
a hard two-color moon-phase split with a dark outline ring, redundant card
titles duplicating information already carried by the arc, and a 58x58px
moon-phase disc that read smaller and less legible than the plain emoji it
replaced. Management diagnosed the implementation against the project's
dataviz design skill and confirmed two concrete anti-patterns: thick flat
color blocks with a border-as-separator (moon disc) and a progress arc with
no traveled-vs-remaining visual distinction (not actually readable as a
meter). User picked a 漸層量表風格 (gradient meter style) direction from two
options presented.

The redesign card (`task-20260721-twp-p2-celestial-redesign`) delivered:
- CelestialArc now splits into an elapsed segment (full accent hue) and a
  remaining segment (a lighter tint of the SAME hue) — sun uses a warm
  family, moon a distinct cool family, so the two cards read differently at
  a glance. No fabricated elapsed segment when there is no valid "now"
  position (regression-safe against the prior card's marker-visibility
  tests).
- Card headings (`日出日落` / `月出月沒`) removed; rise/set times moved to
  direct labels at the arc's own endpoints.
- MoonPhaseDisc rewritten with an SVG gradient terminator (soft lit/dark
  boundary) instead of a hard-edged two-path split, the dark outline ring
  removed, and the rendered footprint enlarged well past the old 58x58px.
- County label kept on the sunrise card (user explicitly decided information
  that's real signal, even if small, should not be deleted — see the
  2026-07-21 geography verification below).

### Geography fact-check that shaped this decision

Before finalizing the redesign, management fact-checked the user's question
"is the location display fake precision, since Taiwan is small" by pulling
live CWA data for Keelung (七堵, 25.10N) vs Hengchun/Pingtung (恆春,
22.01N) on 2026-07-21: sunrise differed by 9 minutes, sunset by 1 minute,
moonset by 10 minutes. The asymmetry (sunrise moves far more than sunset)
confirmed BOTH longitude (near-uniform shift) and latitude (day-length
effect, strongest near solstice) are real contributors — not just longitude
as the user suspected. Conclusion: county-level display is real signal, not
noise; keep it, only de-emphasize its visual weight. This same reasoning
surfaced a real product gap: the moon card had no county field anywhere
(unlike sunrise_sunset), even though moonrise/moonset varies by location for
the same reason. `task-20260721-twp-p2-moon-county-label` closed that gap by
threading `town.city` (already available inside `fetch_moon()`, same source
`fetch_warnings()` already uses) into an additive `MoonInfo.county` field and
displaying it in the same secondary `<small>` style as the sunrise card.

### Also resolved this round: cross-agent tunnel coordination

While reviewing the dev preview, a separate agent had stood up a Cloudflare
quick tunnel (`twp-tunnel.service`, frontend :5173) with a local, uncommitted
`frontend/vite.config.ts` `allowedHosts` addition to let the tunnel's host
header through Vite's dev-server check. Management initially misidentified
this as unrelated leftover cruft and stashed it; once the user clarified its
origin, management restored it, and additionally learned mid-session that
Vite auto-restarts on `vite.config.ts` changes (not just an in-memory
setting), so file-level stash/pop operations during an active dev session
have real, immediate effect on the running server, not just future starts.
Care was taken to keep this local-only tunnel config isolated from every
background coding task's working tree so it was never accidentally swept
into a scoped commit.

### Verification

- Acceptance independently reran ruff, backend pytest (42 passed), frontend
  build, and Vitest (31 passed) for the final stacked state across all three
  cards — all green, no scope violations, no remote pushes.
- Management redeployed the Ubuntu dev preview (backend :8080, frontend
  :5173) after acceptance to serve the finally-approved code for user
  review; confirmed live: moon payload now carries `county` (e.g. 基隆市),
  and the existing Cloudflare tunnel URL still resolves through the
  refreshed frontend process.

### Task bookkeeping

- `task-20260721-twp-p2-celestial-arc` -> completed
- `task-20260721-twp-p2-celestial-redesign` -> completed
- `task-20260721-twp-p2-moon-county-label` -> completed

### Next

P2-3: TDX tourism (scenic spots / restaurants / activities); OAuth2 client
credentials are already provisioned in the Ubuntu backend/.env.

## 2026-07-22: P2-2 fix3 — status-card slider gauges, symmetry fixes, grid-stretch bug

### Summary

User reviewed the shipped celestial redesign (task-20260721-twp-p2-celestial-redesign,
task-20260721-twp-p2-moon-county-label) live and raised three more issues:
every fact-card had become oversized, whether the standalone moon-phase disc
was still necessary now that the arc marker itself could carry the phase,
and whether the sun/moon arcs — and by extension UV/AQI — could get a more
"designed" treatment instead of a plain thin-line meter.

### Design exploration via live mockup

Rather than dispatch another blind coding round, management built a live
HTML/CSS mockup (Claude Artifact) using the user's own screenshot data
(Nantou county: sunrise 05:21/18:44, UV 11 危險, AQI 63 普通, moonrise/set
12:46/23:53 上弦月) and the app's actual approved CSS tokens and font stack,
then iterated it directly against user feedback across several rounds:

- Presented two celestial-arc directions (a conservative "refined meter" vs
  an "atmosphere card" with a gradient sky-wash background + horizon
  silhouette + glowing marker). User picked the atmosphere direction
  decisively.
- User then asked whether UV/AQI — both official ordinal severity scales,
  verified live against `backend/app/adapters/cwa.py::_uv_level` (5 levels:
  低/中/高/過量/危險) and `backend/app/adapters/moenv.py::aqi_level` (6
  levels: 良好/普通/對敏感族群不健康/對所有族群不健康/非常不健康/危害) —
  should reuse the same dome-arc language. Management extended the mockup
  with a "slider" alternative (flat bar + glowing handle) mapped to a shared
  5-step good/moderate/poor/severe/hazard severity ramp that reuses the
  color grouping already informally present in the app's existing AQI CSS
  (`.aqi-普通`, `.aqi-對敏感族群不健康`/`.aqi-對所有族群不健康`,
  `.aqi-非常不健康`/`.aqi-危害`).
- User compared both live in the mockup and made a final split decision:
  keep the dome arc for sun/moon (a time-of-day journey), adopt the slider
  for UV/AQI (a severity-in-range reading) — the two idioms staying visually
  distinct is correct because the underlying data is genuinely different in
  kind, not a consistency defect.
- While building the mockup, management independently found and confirmed
  two real regressions in the shipped code: the sunrise/sunset card lost its
  date entirely when an earlier redesign card removed the old `<h3>`/`<p>`
  heading (only county remained, while the moon card — which later gained a
  county field — kept its date, so the two cards silently went asymmetric);
  and `.fact-grid` used default CSS Grid `align-items: stretch`, so the
  taller moon card was stretching the entire row including the unrelated UV
  and AQI cards — the real cause of "every card became oversized," unrelated
  to any style choice.

### Dispatch and result

`task-20260722-twp-p2-status-cards-and-symmetry` (background-systemd,
gpt-5.6-terra/medium) shipped all of the above: `.fact-grid` fixed to
`align-items: start`; sunrise card's secondary text restored to
`county · date`; moon card's phase name relocated to the top kicker beside
`月出月沒`, mirroring the sunrise card's structure; a new
`frontend/src/components/StatusGauge.tsx` with a pure severity-mapping
function (UV 0-14 domain, AQI 0-300 domain, both clamped past their ceiling,
AQI's top two levels sharing the hazard tier) driving the new UV/AQI slider
cards. `CelestialArc.tsx`/`MoonPhaseDisc.tsx` were explicitly protected from
further changes per the finalized dome-arc decision.

- 9 commits, one per AC (`0eb1107`..`b705e80`), working tree clean, no push.
- ruff PASS; backend pytest 42 passed (unchanged, no backend touched);
  frontend `npm test` 43 passed (7 files, up from 31 — new StatusGauge and
  symmetry coverage); frontend build PASS; mock mode (no CWA/MOENV keys)
  verified deterministic for all four cards.

### Process note

The mockup-first approach (compare real rendered options before dispatching
code) resolved three rounds of "still looks wrong" feedback in one dispatch
instead of another blind round — worth defaulting to for future purely
aesthetic asks on this project, reserving direct dispatch for behavior/data
changes where the spec is unambiguous.

### Pending

Acceptance has not yet run on this card. Management will redeploy the
Ubuntu dev preview (restoring the tunnel's local `vite.config.ts` tweak,
stashed again before this dispatch to keep it out of the coding task's
working tree) once acceptance is complete.

## 2026-07-22: P2-2 fix4 approved — moon phase actually merged into the arc marker

### Summary

User reported the moon card was still visibly taller than its siblings after
task-20260722-twp-p2-status-cards-and-symmetry shipped, despite that card's
`.fact-grid` height fix. Management re-verified against live code and found
the real cause: the user's round-2 request ("is the standalone moon-phase
disc necessary, or can the phase just render on the enlarged arc marker
instead") had never actually been implemented across two prior cards
(celestial-redesign, status-cards-and-symmetry) — both only polished the
still-separate `MoonPhaseDisc` component (gradient terminator, size bump)
while it remained stacked above `CelestialArc` inside a `.moon-visuals`
wrapper. `align-items: start` on the grid stops row-stretch onto siblings;
it cannot shrink a card whose own content is intrinsically taller (a 90x90px
disc plus a full arc, two stacked graphics, versus one arc for every other
card). This was a management specification miss, not an execution miss — the
prior task cards never actually required the merge, only cosmetic polish of
the existing two-element structure.

### Fix

`task-20260722-twp-p2-moon-marker-merge` explicitly lifted the previous
card's "do not touch CelestialArc.tsx/MoonPhaseDisc.tsx" protection rule
(that rule was based on the mistaken premise that the merge was already
done) and required the actual merge: `CelestialArc` gained optional
`illuminationFraction`/`waxing` props; when present, its own position marker
renders the gradient-terminator phase shape at a visibly larger radius (12
vs the sun's unchanged 4.5); when absent, the sun's marker renders exactly
as before. `MoonPhaseDisc.tsx` and its test file were deleted as dead code
once zero references remained. The moon card's DOM structure is now
line-for-line parallel to the sun card: kicker / single arc / small text.

### Verification rigor this round

Acceptance (Codex VS) went beyond source reading: confirmed the sun marker's
JSX line was character-for-character unchanged in the diff (only relocated
into a ternary's else-branch, not edited), and confirmed the moon card's
structural parity via actual rendered-DOM assertions (`.moon-card` has
exactly 3 direct children, exactly 1 `svg`) rather than inferring from
source code. This is the standard worth holding for future "does it actually
look right" acceptance criteria — rendered-DOM checks catch what source
inspection alone can miss.

- 9 commits, one per AC (`a7855b4`..`b5af441`), working tree clean, no push.
- ruff PASS; backend pytest 42 passed (unchanged); frontend test 43 passed,
  build PASS; mock mode deterministic for all four cards.

### Lesson

When a user's structural request ("remove X, merge it into Y") gets
translated into a task card, the acceptance criteria must assert the
structural outcome directly (e.g., "exactly one graphic element in the
DOM"), not just "X looks nicer" — cosmetic-only acceptance criteria let a
card ship without the actual requested restructuring twice in a row before
the gap surfaced from live user feedback instead of from the task cards
themselves.

### Task bookkeeping

- `task-20260722-twp-p2-moon-marker-merge` -> completed

### Status

This closes the P2-2 celestial/status card visual feature — all four
fact-cards (sun, UV, AQI, moon) are now structurally and visually consistent.
Next: P2-3 TDX tourism (scenic spots/restaurants/activities); OAuth2
credentials already provisioned in the Ubuntu backend/.env.

## 2026-07-24: P2-2 fix5 approved — the actual atmosphere-card background finally shipped

### Summary

After task-20260722-twp-p2-moon-marker-merge shipped (moon phase genuinely
merged into the arc marker, verified via rendered-DOM assertions), the user
kept reporting the redeployed preview "still looked the same" across several
rounds. Management exhaustively ruled out deployment/caching causes: server
source verified current via direct curl of the dev server AND through the
public Cloudflare tunnel (`cf-cache-status: DYNAMIC`, `cache-control:
no-cache`), no competing systemd-managed frontend process found, browser
cache ruled out by the user across two browsers and hard refresh, and a full
process teardown/restart with `setsid` performed for good measure — none of
it changed anything, because none of it was the actual problem.

The user then clarified precisely: the "氛圍卡片" (atmosphere card) design
approved earlier via a live HTML/CSS mockup — a sky-gradient CARD
BACKGROUND wash plus a horizon-hill silhouette plus a glowing marker, which
the user called decisively better than the alternative ("方案B絕對優於方案
A") — had never actually been implemented in the real app at all. Root
cause, confirmed by direct code inspection: management's own task-card
context sections for two subsequent cards (status-cards-and-symmetry,
moon-marker-merge) asserted the atmosphere background was "already shipped"
and told the coding agent not to touch it further — an assumption that was
simply never true. What celestial-redesign actually shipped was a different,
narrower thing: a "gradient meter" effect on the ARC LINE's own stroke
(elapsed-vs-remaining coloring), never the CARD's background. Verified live:
`.fact-card`'s base background was a flat `rgba(255,255,255,0.88)` for every
card, with zero sky-gradient or horizon-hill CSS anywhere in the file. This
was a specification gap carried forward silently across two cards, not a
deployment or caching problem — the user was correctly describing what they
saw; management's premise was wrong.

### Fix

`task-20260723-twp-p2-atmosphere-cards` implemented the actual approved
mockup values: sun card day-sky gradient `#eaf6ff -> #fff3de`; moon card
night-sky gradient `#1c2c52 -> #3d4d84` with text switched to legible light
tones; horizon-hill silhouettes added to both arcs; soft glow halos added
behind both markers (additive only — the marker's own rendering logic from
the previous card, including the moon's gradient-terminator phase disc, was
left untouched). The task reused the exact `color-mix`/`linear-gradient`
technique already proven working for the UV/AQI `.status-gauge-card`
background as its implementation template, removing any remaining ambiguity
for the coding layer.

- 10 commits, one per AC (`1631de2`..`d7d6471`), working tree clean, no push.
- ruff PASS; backend pytest 42 passed (unchanged, no backend touched);
  frontend test 43 passed, build PASS; UV/AQI `StatusGauge.tsx` and
  `.status-gauge-card` confirmed byte-unchanged; mock mode deterministic.

### Lesson

When a task card's `context` section asserts "X is already shipped, do not
touch it," that assertion needs the same evidentiary bar as any acceptance
criterion — verify it against current code before writing it, don't carry
it forward from memory of an earlier planning conversation. This gap
survived two full task cards because nothing in either card's acceptance
criteria actually checked for the atmosphere background's presence; both
cards' ACs only covered what was newly in scope, never re-verified the
inherited assumption. Future cards that say "keep X as-is" should include a
cheap sanity check confirming X actually exists as described, not just a
prohibition on touching it.

### Status

The dev preview will be redeployed (backend/frontend restart, tunnel config
restored) for user review. Two open items remain before P2-2 fully closes:
(1) user confirmation that the atmosphere cards now match the approved
mockup, (2) the still-unresolved height difference between the dome-arc
cards (sun/moon) and the flat-slider cards (UV/AQI), deliberately deferred
out of this card's scope pending a direct design conversation with the user.

## 2026-07-25: P2-2 fix8 approved — moon cross-midnight marker fixed after three attempts

### Summary

User spotted at 2026-07-24 00:12 that the moon fact-card showed no position
marker even though a moon (risen 7/23 13:41, not yet set) was still up.
Resolving this took three dispatched cards, worth recording as a case study
in scope discipline and honest failure.

### Attempt 1 — task-20260724-twp-p2-moon-crossmidnight-window (changes_required)

Correctly added backend logic to `fetch_moon()` substituting the previous
day's moonrise/moonset pair when 'now' falls before today's own moonrise but
still inside yesterday's still-open window. Acceptance rejected it for a
real gap: `MoonInfo.target_date` stayed unchanged even when the substitution
happened, so the frontend had no way to know the returned rise/set pair
belonged to yesterday. The substitution logic itself was correct and its
commits were kept, not reverted.

### Attempt 2 — task-20260724-twp-p2-moon-source-date (failed, zero changes)

Management's fix: add `source_date` to `MoonInfo` (mirroring the existing
`sunrise_sunset.source_date` pattern) and have the frontend pass it to
`CelestialArc`. But the task card ALSO explicitly forbade modifying
`getArcProgress()` — a self-contradiction, because that function gates on
`targetDate !== localIsoDate(now)`, which rejects any date that isn't
literally today regardless of what the caller passes. The coding agent
correctly refused to fake a workaround and reported two precise blocking
facts instead of guessing: the date-equality gate, and a second, deeper
issue — even ignoring that gate, the function compares raw
minutes-since-midnight-of-today against the rise time's own minutes, which
cannot express "now is shortly before midnight relative to a rise that
happened yesterday afternoon." This is the correct failure mode: stop and
report rather than ship a broken half-fix. Management archived the card with
the coding agent's own analysis linked as the root-cause record.

### Attempt 3 — task-20260725-twp-p2-moon-arc-progress-rewrite (approved)

Management explicitly lifted the restriction on `getArcProgress()` this
time — there was no correct fix that avoided touching it — and specified the
actual algorithm: replace the same-day string-equality gate and
minutes-of-day arithmetic with absolute-instant comparison anchored on the
caller-supplied date (rise/set both resolved to full date+time instants,
set pushed +24h if it falls at or before rise, then `now` compared directly
against that instant range). This single change correctly subsumes every
prior case with no special-casing: a future 7-day-strip day naturally has
both instants in the future and still returns no marker; a same-day sun/moon
case is unaffected; the cross-midnight moon case now resolves correctly.

Independent second-layer review (Claude Code VS) went further than the
first acceptance pass: hand-verified the exact cross-midnight arithmetic
(rise 7/23 13:41 +24h-adjusted set 7/24 00:32, now 00:12, progress ≈
10h31m/10h51m ≈ 0.969) against the shipped test's own assertion bounds, and
confirmed the test performs a real `render()` with a DOM assertion that the
marker element exists, not just a pure-function return-value check.

- 8 commits, one per AC (`e2e6040`..`b975fce`), working tree clean, no push.
- ruff PASS; backend pytest 45 passed; frontend test 47 passed, build PASS;
  StatusGauge/moon-phase rendering/atmosphere styling all confirmed
  untouched.

### Lesson

When a fix keeps failing against the same restriction, the restriction
itself is usually the bug — not the third attempt at a workaround. The
correct move once a coding agent reports "this task card is internally
impossible" is to re-examine the constraint that made it impossible, not to
rephrase the same constraint a second time. Attempt 2's failure report was
the single most useful artifact in this whole thread: it named both blocking
facts precisely enough that attempt 3's task card could specify a complete
algorithm on the first try instead of guessing again.

### Status

This closes the moon cross-midnight bug. Two items remain open before P2-2
fully wraps: (1) dev preview redeploy for final user confirmation, (2) the
still-unresolved height difference between the dome-arc cards (sun/moon) and
the flat-slider cards (UV/AQI), deliberately deferred pending a direct
design conversation with the user. After that: P2-3 TDX tourism.

## 2026-07-26: Dev preview tunnel rotated; P2-2 status recap

### Summary

While redeploying the dev preview to verify task-20260725-twp-p2-moon-arc-progress-rewrite,
management found the existing Cloudflare quick tunnel (`twp-tunnel.service`)
had restarted independently (new process, PID 2172, started 2026-07-26
21:13:18 CST) and, as Cloudflare quick tunnels always do on restart, was
issued a brand-new random hostname. The old preview URL
(`cooper-albany-groundwater-characteristics.trycloudflare.com`) no longer
resolves at all (DNS lookup failure, not an app-level error). The current
URL, confirmed reachable (HTTP 200):

`https://structure-refuse-consolidated-jay.trycloudflare.com`

Backend/frontend dev servers were restarted clean (`setsid`-detached,
verified no stale PIDs) serving current `phase2-dev` HEAD; live API smoke
confirmed `moon.source_date` is present in the forecast payload.

### P2-2 status recap

All shipped and approved on `phase2-dev` (local only, never pushed,
`main`/Azure demo remain the frozen Phase 1 baseline):

- MOENV AQI (current + 3-day zone forecast), CWA weather warnings, moon
  astronomy — task-20260715-twp-p2-suitability + fix1
- Celestial arc redesign: gradient meter, atmosphere sky-wash card
  backgrounds, horizon silhouettes, marker glow — across
  celestial-arc / celestial-redesign / status-cards-and-symmetry /
  moon-marker-merge / atmosphere-cards
- Moon cross-midnight marker fix (source_date + absolute-instant
  getArcProgress rewrite) — moon-arc-progress-rewrite, approved after two
  prior attempts correctly failed rather than shipping a broken fix
- UV/AQI severity slider gauges, shared 5-tier color ramp

### Open items

1. Dome-arc (sun/moon) vs flat-slider (UV/AQI) card height mismatch —
   deliberately deferred pending a direct design conversation with the user,
   not yet scheduled.
2. P2-3 TDX tourism (scenic spots/restaurants/activities) — next feature in
   the Phase 2 queue; OAuth2 credentials already provisioned in the Ubuntu
   backend/.env, no new registration needed.

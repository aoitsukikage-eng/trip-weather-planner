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

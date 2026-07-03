# Trip Weather Planner — Developer Log

## 2026-07-02: P1 scaffold approved after Ubuntu takeover

### Summary

`Phase 1 mock scaffold` was approved after the Ubuntu takeover and
re-acceptance pass.

### Accepted state

- Ubuntu became the only active development mainline.
- `ruff check` passed on Ubuntu.
- `pytest` passed on Ubuntu (`9 passed`).
- Frontend `npm run build` passed on Ubuntu.

### Operational decision

- Ubuntu is the only active development worktree from this point onward.
- Mac SSD is only a git mirror / backup / management-document workspace.

## 2026-07-02: P1 live CWA integration approved

### Summary

`cathay-cloud-intern-p1-cwa-live-integration` was approved.

### Accepted state

- The backend now serves real `CWA` data when `CWA_API_KEY` is configured.
- Mock fallback still works when `CWA_API_KEY` is absent.
- Ubuntu `ruff` passed.
- Ubuntu backend `pytest` passed (`14 passed`).
- Ubuntu frontend `npm run build` passed.
- Ubuntu repo head advanced to `5265d66 feat: integrate live CWA weather datasets`.

### Compatibility note

- During live validation on 2026-07-02, the official `F-D0047-093` family
  endpoint returned `404 Resource not found`.
- The implementation therefore preserved the intended routing family while
  resolving transport calls to currently available county-level datasets.
- This was accepted as a compatibility fix rather than treated as a blocker.

## 2026-07-03: P1 public demo readiness approved

### Summary

`cathay-cloud-intern-p1-public-demo-readiness` was approved.

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
- External blockers remain platform auth and actual cloud deployment inputs.

## Current project status

- `P1 scaffold`: approved
- `P1 live CWA integration`: approved
- `P1 public demo readiness`: approved
- Next natural step: actual deploy / cloud auth / public URL

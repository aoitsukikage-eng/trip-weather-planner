# Public Demo Deployment Runbook

This document describes how to take the repo from "deployment-ready" to an
actual public demo once platform access exists. It does **not** claim that the
deployment has already happened.

## Target State

- Backend: FastAPI container on Cloud Run.
- Frontend: static Vite build hosted from GCS website bucket or a CDN/custom
  domain in front of that bucket.
- Secrets: injected from GCP Secret Manager into Cloud Run, never committed into
  the repo.
- CI/CD: GitHub Actions `ci.yml` for validation plus `deploy-demo.yml` as a
  gated manual deployment skeleton.

## External Prerequisites

- Docker available on the operator machine or in CI.
- Terraform 1.6+ available locally, or use the documented containerized
  Terraform commands.
- `gcloud` access or GitHub OIDC configured for the target GCP project.
- A GCP project with these APIs enabled:
  - `run.googleapis.com`
  - `artifactregistry.googleapis.com`
  - `secretmanager.googleapis.com`
  - `cloudbuild.googleapis.com`
  - `iamcredentials.googleapis.com`
  - `storage.googleapis.com`

## Required Inputs

| Input | Example | Why it is needed |
|---|---|---|
| `project_id` | `my-demo-project` | Terraform + gcloud target |
| `region` | `asia-east1` | Cloud Run + Artifact Registry region |
| `backend_service_name` | `twp-api-demo` | Public API service name |
| `backend_image` | `asia-east1-docker.pkg.dev/.../backend:demo` | Cloud Run container image |
| `frontend_bucket_name` | `trip-weather-planner-demo-frontend` | Static hosting bucket |
| `frontend_origin` | `https://demo.example.com` | Backend CORS allowlist |
| `cache_ttl_seconds` | `1800` | Runtime tuning |
| `upstream_timeout_seconds` | `10` | Runtime tuning |

Copy `infra/terraform/environments/dev/terraform.tfvars.example` to
`terraform.tfvars` and replace placeholders before `terraform plan/apply`.

## Secret Inventory

These values must come from Secret Manager or CI secrets, never tracked files:

| Env var | Required for public demo? | Notes |
|---|---|---|
| `CWA_API_KEY` | Yes for live weather | Without it the backend stays in mock mode |
| `GEMINI_API_KEY` | Optional | If absent the backend degrades to deterministic summary |
| `TDX_CLIENT_ID` | No for this card | Phase 2/3 only |
| `TDX_CLIENT_SECRET` | No for this card | Phase 2/3 only |

The Terraform variable `backend_secret_env` maps Cloud Run env names to Secret
Manager secret names and versions.

## Validation Before Any Real Deploy

```bash
source ~/venvs/python-env/bin/activate
docker build -t trip-weather-planner-backend:readiness ./backend
cd backend && ruff check . && pytest -q
cd ../frontend && npm run build
cd ..
docker run --rm -v "$PWD/infra/terraform:/work" -w /work hashicorp/terraform:1.11.4 \
  -chdir=environments/dev init -backend=false
docker run --rm -v "$PWD/infra/terraform:/work" -w /work hashicorp/terraform:1.11.4 \
  -chdir=environments/dev validate
docker run --rm -v "$PWD/infra/terraform:/work" -w /work hashicorp/terraform:1.11.4 \
  fmt -check -recursive
```

## Deployment Sequence

1. Build and push the backend image to Artifact Registry.
2. Prepare `infra/terraform/environments/dev/terraform.tfvars` from the example.
3. Create required Secret Manager secrets if they do not already exist.
4. Run `terraform plan`, review output, then `terraform apply`.
5. Capture the Cloud Run URL from Terraform output `backend_url`.
6. Build the frontend with `VITE_API_BASE=<backend_url>`.
7. Upload `frontend/dist/` to the target bucket, or front the bucket with your
   preferred CDN/custom domain and point `frontend_origin` at that URL.
8. Smoke-test the deployed API and frontend before calling it public.

## Manual Command Reference

### Backend image

```bash
gcloud auth configure-docker asia-east1-docker.pkg.dev --quiet
docker build -t asia-east1-docker.pkg.dev/PROJECT/REPO/backend:demo ./backend
docker push asia-east1-docker.pkg.dev/PROJECT/REPO/backend:demo
```

### Terraform

```bash
cd infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

### Frontend build and upload

```bash
cd frontend
VITE_API_BASE="https://your-cloud-run-url.run.app" npm run build
gcloud storage rsync dist "gs://your-frontend-bucket-name" \
  --recursive \
  --delete-unmatched-destination-objects
```

## Smoke Test Checklist

- `curl https://<cloud-run-url>/` returns JSON with `name`, `version`, and
  `docs`.
- `curl https://<cloud-run-url>/api/towns` returns `success: true`.
- `curl "https://<cloud-run-url>/api/forecast?town=taipei-xinyi&date=YYYY-MM-DD"`
  returns normalized forecast payload.
- Open the frontend URL and confirm:
  - Town list loads.
  - Submitting a date returns a forecast card.
  - Browser network tab shows requests going to the deployed backend URL.

## GitHub Actions Deployment Skeleton

Use `.github/workflows/deploy-demo.yml` when GitHub OIDC and repo secrets are
ready. It intentionally supports `dry_run=true` so the workflow can validate the
path without pretending to perform a real cloud deployment.

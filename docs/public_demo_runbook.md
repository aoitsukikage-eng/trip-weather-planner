# Public Demo Deployment Runbook

This runbook records the Azure public demo deployment path for the project. The
target region is `southeastasia`, matching the demo resource group and Container
Apps deployment.

## Target State

- Backend: FastAPI container on Azure Container Apps, external ingress on port
  `8080`.
- Image registry: Azure Container Registry `twpacr4316`.
- Frontend: Vite static build uploaded to the Azure Storage static website
  `$web` container.
- Secrets: `CWA_API_KEY` stored as a Container Apps secret named `cwa-api-key`,
  then referenced by the backend runtime.
- Scale profile: `0.5` vCPU, `1Gi` memory, `min_replicas=0`, `max_replicas=1`.

## Prerequisites

- Azure CLI logged into the target subscription.
- Docker available locally if the subscription cannot use remote ACR builds.
- Node.js 22+ for the frontend build.
- Resource group `rg-twp-demo` in `southeastasia`.
- Azure resources available or provisioned from Terraform:
  - Storage account `twpfe5ce0` with static website enabled.
  - Azure Container Registry `twpacr4316`.
  - Container Apps environment `twp-ca-env`.
  - Container App `twp-backend`.

## Required Inputs

| Input | Demo value | Why it is needed |
|---|---|---|
| `RESOURCE_GROUP_NAME` | `rg-twp-demo` | Azure resource group target |
| `REGION` | `southeastasia` | Demo resource location |
| `ACR_NAME` | `twpacr4316` | Backend image registry |
| `CONTAINER_APP_NAME` | `twp-backend` | Backend runtime |
| `BACKEND_IMAGE_NAME` | `twp-backend` | Repository name in ACR |
| `FRONTEND_STORAGE_ACCOUNT` | `twpfe5ce0` | Static website host |
| `FRONTEND_ORIGIN` | `https://twpfe5ce0.z23.web.core.windows.net` | Backend CORS allowlist |
| `BACKEND_URL` | Container Apps HTTPS URL | Frontend production API base |

## Secret Inventory

These values must come from operator input or CI secrets, never tracked files:

| Env var | Required for public demo? | Azure handling |
|---|---|---|
| `CWA_API_KEY` | Yes for live weather | Stored as Container Apps secret `cwa-api-key` |

## Validation Before Deploy

```bash
cd backend
ruff check .
pytest -q

cd ../frontend
npm ci
npm run build

cd ..
docker build -t local/trip-weather-planner-backend:readiness ./backend
```

## Backend Image Build

Preferred path when ACR remote build is available:

```bash
az acr build \
  --registry twpacr4316 \
  --image twp-backend:latest \
  ./backend
```

Fallback path used when subscription limits block remote ACR build:

```bash
az acr login --name twpacr4316
docker build --platform linux/amd64 -t twpacr4316.azurecr.io/twp-backend:latest ./backend
docker push twpacr4316.azurecr.io/twp-backend:latest
```

## Backend Deploy

For an existing Container App, update the secret and image:

```bash
az containerapp secret set \
  --name twp-backend \
  --resource-group rg-twp-demo \
  --secrets cwa-api-key="$CWA_API_KEY"

az containerapp update \
  --name twp-backend \
  --resource-group rg-twp-demo \
  --image twpacr4316.azurecr.io/twp-backend:latest \
  --set-env-vars \
    CACHE_TTL_SECONDS=1800 \
    CORS_ORIGINS="https://twpfe5ce0.z23.web.core.windows.net" \
    UPSTREAM_TIMEOUT_SECONDS=10 \
    CWA_API_KEY=secretref:cwa-api-key
```

If the app does not exist yet, create it with the same runtime contract:

```bash
az containerapp create \
  --name twp-backend \
  --resource-group rg-twp-demo \
  --environment twp-ca-env \
  --image twpacr4316.azurecr.io/twp-backend:latest \
  --target-port 8080 \
  --ingress external \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 0 \
  --max-replicas 1 \
  --secrets cwa-api-key="$CWA_API_KEY" \
  --env-vars \
    CACHE_TTL_SECONDS=1800 \
    CORS_ORIGINS="https://twpfe5ce0.z23.web.core.windows.net" \
    UPSTREAM_TIMEOUT_SECONDS=10 \
    CWA_API_KEY=secretref:cwa-api-key
```

Capture the backend URL:

```bash
BACKEND_FQDN="$(az containerapp show \
  --name twp-backend \
  --resource-group rg-twp-demo \
  --query properties.configuration.ingress.fqdn \
  --output tsv)"
BACKEND_URL="https://$BACKEND_FQDN"
```

## Frontend Build And Upload

Build the production bundle against the deployed backend, then upload to the
Storage static website container:

```bash
cd frontend
VITE_API_BASE="$BACKEND_URL" npm run build

az storage blob upload-batch \
  --account-name twpfe5ce0 \
  --destination '$web' \
  --source dist \
  --overwrite true \
  --auth-mode login
```

## Smoke Test Checklist

Run these checks before calling the demo public:

```bash
curl "$BACKEND_URL/"
curl "$BACKEND_URL/api/towns"
curl "$BACKEND_URL/api/forecast?town=taipei-xinyi&date=YYYY-MM-DD"
curl -i \
  -H "Origin: https://twpfe5ce0.z23.web.core.windows.net" \
  "$BACKEND_URL/api/towns"
```

- `/` returns service metadata with `name`, `version`, and `docs`.
- `/api/towns` returns `success: true`.
- `/api/forecast` returns a normalized forecast payload for the selected town and
  date.
- The CORS response allows the Azure Storage frontend origin.
- Opening `https://twpfe5ce0.z23.web.core.windows.net/` loads the town selector,
  submits a date, and sends browser network requests to the Container Apps URL.

## GitHub Actions Deployment Skeleton

`.github/workflows/deploy-demo.yml` mirrors this manual deployment path: validate,
authenticate to Azure with OIDC, build the backend image in ACR, update Container
Apps, build the frontend with `VITE_API_BASE`, and upload the static bundle to
`$web`.

# CI/CD 流程

驗證實作於 `.github/workflows/ci.yml`，部署骨架位於
`.github/workflows/deploy-demo.yml`。

```mermaid
flowchart LR
  DEV["Push / PR"] --> CI["GitHub Actions"]
  CI --> B["backend: ruff + pytest"]
  CI --> F["frontend: npm test + npm build"]
  CI --> I["infra: terraform fmt + validate"]
  B --> GATE["全綠才可 merge"]
  F --> GATE
  I --> GATE
  GATE --> AZLOGIN["OIDC federated credential 登入 Azure"]
  AZLOGIN --> ACRBUILD["az acr build 建置後端 image"]
  AZLOGIN --> FEBUILD["Build 前端產物"]
  ACRBUILD --> APPROVE["Production 手動核准"]
  FEBUILD --> APPROVE
  APPROVE --> DEPLOYAPI["deploy Azure Container Apps"]
  APPROVE --> DEPLOYFE["az storage blob upload-batch 到 $web"]
  DEPLOYAPI --> OBS["Azure Monitor / Log Analytics"]
  DEPLOYFE --> OBS
```

## CI 階段(已實作)

- **後端**:`ruff check`(lint)+ `pytest`(單元測試,mock 模式、免憑證、免網路)。
- **前端**:`npm ci` + `npm test` + `npm run build`(測試、TypeScript 型別檢查 + Vite 建置)。**Node 鎖 22 LTS**(避免非 LTS 版本在 CI 出意外)。
- **Infra**:`terraform fmt -check` + `terraform validate`。

## CD 階段(部署骨架已補)

- `deploy-demo.yml` 採 `workflow_dispatch` 手動觸發，並由 `environment` input 指定
  GitHub Environment；觸發時需提供 Azure resource group、ACR、Container App、
  frontend storage account 與 frontend origin 等部署目標。
- 真部署仍需人工觸發與環境核准，不會在這個 repo 內假裝「一 push 就已上雲」。
- GitHub Actions 透過 **OIDC federated credential** 登入 Azure，不保存長期雲端金鑰。
- 後端用 `az acr build` 建置並推送 image 到 Azure Container Registry，之後部署 Azure Container Apps。
- 前端走獨立路線 build 後以 `az storage blob upload-batch -d '$web' -s frontend/dist` 發布到 Azure Storage 靜態網站，與後端 release 可分開驗證。

## 加分細節

- 雲端認證用 **OIDC** 而非長期 access key。
- `main` 分支保護,CI 未過不能 merge。
- Terraform **plan 與 apply 分離**(plan 在 PR、apply 在核准後)。
- `verify` job 先跑 build / validate；通過後才依環境核准進入 Azure OIDC 登入與部署。

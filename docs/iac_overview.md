# Infra as Code

實作於 `infra/terraform/`,Terraform 管理。

## Single source of truth(部署三角色講死)

| 用途 | 採用 |
|---|---|
| 正式架構設計呈現 | Azure Storage 靜態網站 + Azure Container Apps + Azure Container Registry |
| 實際 demo 部署 | 與設計圖一致,採 Azure 單雲部署 |
| IaC(Terraform) | codify demo 實際用到的 Azure 資源:RG、Storage account static website、ACR、Container Apps |

避免「圖一套、跑一套、IaC 又一套」。

## Terraform provider 與模組敘事

- 採 **Terraform `azurerm` provider** 管理全部 Azure 資源,維持單一雲部署敘事。
- `infra/terraform/environments/dev` 建立 resource group,再串接 `backend_service` 與 `frontend_hosting` 兩個模組。
- 預設 region 為 `southeastasia`,對照 demo deployment 的 `rg-twp-demo` 資源群組。

## 涵蓋資源

- **Resource Group**:`azurerm_resource_group.demo`,預設 `rg-twp-demo` / `southeastasia`。
- **Azure Storage account static website**:`azurerm_storage_account.frontend`,預設 `twpfe5ce0`,`Standard_LRS`,`StorageV2`,`min_tls_version=TLS1_2`,以 `$web` container 承接 React build 輸出,`index.html` 同時作為 SPA 404 fallback。
- **Azure Container Registry**:`azurerm_container_registry.backend`,預設 `twpacr4316`,`Basic` SKU,提供 Container Apps image 來源。
- **Log Analytics workspace**:`azurerm_log_analytics_workspace.backend`,供 Container Apps environment 使用。
- **Azure Container Apps environment + app**:`azurerm_container_app_environment.backend` 預設 `twp-ca-env`;`azurerm_container_app.backend` 預設 `twp-backend`,external ingress port `8080`,`0.5` vCPU / `1Gi`,`min_replicas=0` / `max_replicas=1`,並以 `secretref:cwa-api-key` 注入 `CWA_API_KEY`。

## 驗證策略

- CI 的 `infra` job 持續執行 `terraform fmt -check` 與 `terraform validate`,先擋掉語法與 provider schema 問題。
- PR 階段以 validate 為最小門檻;真正 apply 留在手動核准後,避免 demo 訂閱在每次 push 都產生雲端成本。
- 變數檔只保留非敏感設定樣板;`cwa_api_key` 為 `sensitive` 且無預設值,驗證時用 `TF_VAR_cwa_api_key` placeholder,實際部署值交由 Azure 端 secret 機制或 deploy 流程注入。

## CI 驗證與部署前置

CI 的 `infra` job 跑 `terraform fmt -check` + `terraform validate`(見
`cicd_flow.md`)。`deploy-demo.yml` 則提供 Azure OIDC deployment skeleton,
使用 `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID`
作為 GitHub secrets 佔位符,backend job 透過 `az acr build` 與
`az containerapp update` 更新後端,frontend job 以 `VITE_API_BASE` build 後
上傳到 Storage account 的 `$web` container。`CWA_API_KEY` 以 GitHub Actions
secret 提供,workflow 於部署前寫入 Container Apps secret。

## 備註

本案 IaC 定位是把 Azure demo deployment 的關鍵資源模型講清楚,確保架構圖、CI/CD 與部署腳本都圍繞同一組 Azure 元件。實際落地順序與 smoke test 見 `public_demo_runbook.md`。

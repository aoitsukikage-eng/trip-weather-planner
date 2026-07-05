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

- 採 **Terraform `azurerm` provider** 管理 Azure 資源,不保留多雲或 `google` provider 分支敘事。
- 目前 `infra/terraform/` 可視為 Azure deployment blueprint,之後若補足模組細節,仍以同一組 provider 與資源模型延伸。

## 涵蓋資源

- **Resource Group**:作為 demo 資源邊界,集中管理 region、tag 與權限範圍。
- **Azure Storage account static website**:以 `$web` container 承接 React build 輸出,對外提供 HTTPS 與靜態資產發布。
- **Azure Container Registry**:保存後端 FastAPI image,提供 Container Apps 拉 image 的來源。
- **Azure Container Apps environment + app**:承接 consumption plan 執行環境、revision、ingress、`minReplicas=0` / `maxReplicas=1`、secret 綁定與 runtime env。

## 驗證策略

- CI 的 `infra` job 持續執行 `terraform fmt -check` 與 `terraform validate`,先擋掉語法與 provider schema 問題。
- PR 階段以 validate 為最小門檻;真正 apply 留在手動核准後,避免 demo 訂閱在每次 push 都產生雲端成本。
- 變數檔只保留非敏感設定樣板;`CWA_API_KEY` 這類秘密值交由 Azure 端 secret 機制或 deploy 流程注入。

## CI 驗證與部署前置

CI 的 `infra` job 跑 `terraform fmt -check` + `terraform validate`(見
`cicd_flow.md`)。`deploy-demo.yml` 則提供 gated deployment skeleton，只有
在 GitHub OIDC 與專案 secrets 就緒時才會真的進入 deploy 階段。

## 備註

本案 IaC 定位是把 Azure demo deployment 的關鍵資源模型講清楚,確保架構圖、CI/CD 與部署腳本都圍繞同一組 Azure 元件。實際落地順序與 smoke test 見 `public_demo_runbook.md`。

# Infra as Code

實作於 `infra/terraform/`,Terraform 管理。

## Single source of truth(部署三角色講死)

| 用途 | 採用 |
|---|---|
| 正式架構設計呈現 | 平台中立主圖 + AWS 映射附錄(`cloud_architecture.md`) |
| 實際 demo 部署 | 後端 Cloud Run + 前端 Cloudflare Pages / GCS bucket |
| IaC(Terraform) | codify demo 實際用到的資源:前端託管 + 後端服務 |

避免「圖一套、跑一套、IaC 又一套」。

## 模組切分

```
infra/terraform/
├── environments/dev/          # 組裝模組、輸出 URL
│   ├── versions.tf            # provider + 版本
│   ├── variables.tf
│   └── main.tf
└── modules/
    ├── frontend_hosting/      # 靜態前端託管(GCS website bucket + 公開讀取)
    └── backend_service/       # Cloud Run 服務(scale-to-zero + 公開 invoker)
```

`environments/dev/terraform.tfvars.example` 提供 deploy-ready 範本，包含
image、bucket、frontend origin 與 Secret Manager 綁定欄位。

## 涵蓋資源

- **前端**(題目明確要求「IaC 建置前端架構」):靜態託管 bucket + SPA fallback + 公開讀取。生產再前掛 CDN + TLS;若改 Cloudflare Pages,替換為 `cloudflare_pages_project` 即可。
- **後端**:Cloud Run 服務(容器映像、埠 8080、min/max instance、timeout、
  公開 invoker)。非敏感 env 直接由 Terraform 傳入;敏感值由 Secret
  Manager 注入,不寫進映像。

## CI 驗證與部署前置

CI 的 `infra` job 跑 `terraform fmt -check` + `terraform validate`(見
`cicd_flow.md`)。`deploy-demo.yml` 則提供 gated deployment skeleton，只有
在 GitHub OIDC 與專案 secrets 就緒時才會真的進入 deploy 階段。

## 備註

AWS 版 IaC(VPC / ECS / RDS / ElastiCache …)為設計附錄示意;demo 不落地 AWS(ALB/Fargate/RDS 對長期免費不友善)。實際落地順序與 smoke test 見 `public_demo_runbook.md`。

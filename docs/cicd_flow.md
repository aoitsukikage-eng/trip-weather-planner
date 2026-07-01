# CI/CD 流程

實作於 `.github/workflows/ci.yml`。

```mermaid
flowchart LR
  DEV["Push / PR"] --> CI["GitHub Actions"]
  CI --> B["backend: ruff + pytest"]
  CI --> F["frontend: npm build"]
  CI --> I["infra: terraform fmt + validate"]
  B --> GATE["全綠才可 merge"]
  F --> GATE
  I --> GATE
  GATE --> BUILD["Build Docker image + 前端產物"]
  BUILD --> APPROVE["Production 手動核准"]
  APPROVE --> DEPLOYAPI["部署 Cloud Run(後端)"]
  APPROVE --> DEPLOYFE["部署 Cloudflare/GCS(前端)"]
  DEPLOYAPI --> OBS["監控 / logs"]
  DEPLOYFE --> OBS
```

## CI 階段(已實作)

- **後端**:`ruff check`(lint)+ `pytest`(單元測試,mock 模式、免憑證、免網路)。
- **前端**:`npm ci` + `npm run build`(TypeScript 型別檢查 + Vite 建置)。**Node 鎖 22 LTS**(避免非 LTS 版本在 CI 出意外)。
- **Infra**:`terraform fmt -check` + `terraform validate`。

## CD 階段(設計)

- Staging 自動部署;Production 需人工核准。
- 前端 build 上傳靜態託管;後端部署 Cloud Run。

## 加分細節

- 雲端認證用 **OIDC** 而非長期 access key。
- `main` 分支保護,CI 未過不能 merge。
- Terraform **plan 與 apply 分離**(plan 在 PR、apply 在核准後)。

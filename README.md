# Trip Weather Planner · 旅遊行前天氣規劃雲端系統

以中央氣象署(CWA)天氣資料為核心的旅遊行前天氣規劃雲端系統。使用者選擇**縣市 / 鄉鎮市區**與**旅遊日期**,系統整合 7 天天氣預報、72 小時逐時趨勢、日出日落、紫外線資訊與規則式行前建議。

> 國泰金控雲端開發工程師實習筆試作品。設計原則、三方收斂與決策見 `docs/`。

## 亮點對應題目

| 題目要求 / 加分項 | 本專案落點 |
|---|---|
| 雲端後端放 Python 程式碼 | FastAPI 容器化,部署 Azure Container Apps |
| 雲端架構圖 | `docs/cloud_architecture.md`(Azure 架構圖 + 資料流) |
| 前端程式 | React + Vite + TypeScript 表單式查詢頁 |
| 串接第三方 REST API | CWA 天氣、日出日落、紫外線資料,全由後端代理 |
| CI/CD 流程圖 | `docs/cicd_flow.md` + `.github/workflows/ci.yml` |
| 多人協作 Git 流程圖 | `docs/git_workflow.md`(trunk-based) |
| IaC 建置前端架構 | `infra/terraform/`(Terraform azurerm 敘事: RG + Storage 靜態網站 + ACR + Container Apps) |
| AI Driven 系統 | 多 agent 分層協作的開發流程,見 `docs/ai_driven.md` |

## 架構一覽

```
前端 (React/Vite)  ──►  FastAPI 後端  ──►  第三方 API (CWA)
 Azure Storage 靜態網站   Azure Container Apps   後端代理,key 不進前端
                               │
                               ├─ Azure Container Registry (image)
                               ├─ Container Apps secrets (CWA_API_KEY)
                               └─ Azure Monitor / Log Analytics
```

後端輸出:368 鄉鎮市區、7 天預報、72h 逐時趨勢、日出日落、UV、行前建議（規則式產生）。

## 本機開發

**先決條件**:專案**零憑證即可跑**。未設 `CWA_API_KEY` 時後端自動進 mock 模式,回可重現的 22 筆鄉鎮與 7 天假資料;前端亦有 mock fallback。設有 `CWA_API_KEY` 時:

- `/api/towns` 會切到 CWA live catalog,從各縣市 `F-D0047-091` 族群彙整約 368 筆鄉鎮市區,並保留靜態 22 筆名單作 fallback。
- `GET /api/forecast` 會依目標日期切到 CWA live dataset family:近端走 `F-D0047-093` 邏輯族群(實際解析到各縣市 3 小時資料集),較遠日期走 `F-D0047-091` 邏輯族群(實際解析到各縣市 12 小時資料集)。
- 同一筆 forecast 會再補上 `A-B0062-001` 日出日落與 `O-A0005-001` 紫外線觀測值(搭配 `O-A0001-001` 測站座標做最近站映射)。

```bash
# 後端
cd backend
python -m venv .venv && source .venv/bin/activate   # 或用既有 venv
pip install -r requirements-dev.txt
cp .env.example .env            # 憑證到手再填,不填就是 mock 模式
uvicorn app.main:app --reload --port 8080
#   → http://localhost:8080/docs  (自動 OpenAPI 文件)

# 前端(另開終端)
cd frontend
npm install
npm run dev                     # → http://localhost:5173,dev 代理 /api 到 8080
```

測試與 lint:

```bash
cd backend && pytest -q && ruff check .
cd frontend && npm run build
```

## 雲端部署(Azure)

- **架構摘要**:前端部署到 Azure Storage 靜態網站(`$web` container),後端部署到 Azure Container Apps consumption plan,映像由 Azure Container Registry 保存,`CWA_API_KEY` 透過 Container Apps secrets 注入。
- **Demo URL**:前端 `https://twpfe5ce0.z23.web.core.windows.net/`、後端 `https://twp-backend.purplewave-91ee1594.southeastasia.azurecontainerapps.io`。
- **延伸文件**:
  - 架構圖:`docs/cloud_architecture.md`
  - CI/CD:`docs/cicd_flow.md`
  - IaC:`docs/iac_overview.md`
  - 架構原則:`docs/architecture_overview.md`

## 安全設計

- 金鑰管理:CWA 授權碼放在 Container Apps secret,由後端代理第三方 API,不進前端 bundle 或 repo。
- CORS:後端以已知前端網域作白名單,避免開放任意 origin。
- CI/CD 認證:`deploy-demo.yml`(部署骨架)設計採 GitHub OIDC 登入 Azure,不保存長期雲端金鑰。
- 傳輸安全:前後端公開入口皆使用 HTTPS,Storage account 設定最低 TLS 1.2。
- 憑證掃描:repo 內含 `.gitleaks.toml`,並已執行 gitleaks 全史掃描確認無 findings。

## 憑證(免費,實作到真資料時才需要)

- **CWA 授權碼**:https://opendata.cwa.gov.tw → 註冊氣象會員 → 取得授權碼 → 填入 `backend/.env` 的 `CWA_API_KEY`。

## 目錄

```
backend/    FastAPI(adapters / services / routers / schemas / tests)
frontend/   React + Vite + TypeScript
infra/      Terraform(前端託管 + 後端服務)
docs/       設計文件與流程圖
```

## 狀態

- ✅ 已交付的天氣規劃系統:
  - live mode 提供全臺約 368 筆鄉鎮市區,前端採縣市 → 鄉鎮兩階段選單。
  - 日期選擇為 today..today+6 的 7 天 chips,預設載入即顯示整週預報,畫面不顯示年份。
  - 行前建議固定聚焦使用者選取日,由後端規則式邏輯產生。
  - 72 小時逐時圖表呈現溫度、體感溫度、降雨機率與天氣圖示,並在點位過密時自動降低標註密度。
  - forecast payload 與 UI 會顯示 selected county 的日出日落,以及以最近 CWA 測站對應的目前紫外線等級。
- ✅ Mock mode 仍可零憑證 demo,保留既有 22 筆靜態鄉鎮與 deterministic fallback。
- ✅ Public-demo deployment readiness: Docker build、Terraform 範本、deploy workflow skeleton、runbook 已整理完成。
- ✅ Azure public demo deployed:前端 Azure Storage 靜態網站,後端 Azure Container Apps(依 `docs/public_demo_runbook.md` 手動部署)。

## Public Demo Readiness

- Deployment runbook:`docs/public_demo_runbook.md`
- Terraform example:`infra/terraform/environments/dev/terraform.tfvars.example`
- Deploy workflow skeleton:`.github/workflows/deploy-demo.yml`

目前 repo 狀態是 **public-demo deployed**。正式 demo URL 已回填於 README 與部署文件;公開 demo 由 `docs/public_demo_runbook.md` 的手動流程部署,`deploy-demo.yml` 為自動化路徑骨架(`workflow_dispatch` 手動觸發),尚未實際執行過。

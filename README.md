# Trip Weather Planner · 旅遊行前天氣規劃雲端系統

以中央氣象署(CWA)天氣資料為核心的旅遊行前天氣規劃雲端系統。使用者選擇**縣市 / 鄉鎮市區**與**旅遊日期**，系統整合 7 天天氣預報、72 小時逐時趨勢、日出日落、月相與月出月沒、紫外線資訊、即時空氣品質與 3 日 AQI 預報、CWA 天氣警特報，以及規則式行前建議。介面支援**繁體中文 / English / 日本語**三語切換。

> 國泰金控雲端開發工程師實習筆試作品。設計原則、三方收斂與決策見 `docs/`。

## 亮點對應題目

| 題目要求 / 加分項 | 本專案落點 |
|---|---|
| 雲端後端放 Python 程式碼 | FastAPI 容器化，部署 Azure Container Apps |
| 雲端架構圖 | `docs/cloud_architecture.md`（Azure 架構圖 + 資料流） |
| 前端程式 | React + Vite + TypeScript 表單式查詢頁 |
| 串接第三方 REST API | CWA 天氣、日出日落、月出月沒、紫外線、天氣警特報；MOENV 即時 AQI 與 3 日預報 |
| CI/CD 流程圖 | `docs/cicd_flow.md` + `.github/workflows/ci.yml` |
| 多人協作 Git 流程圖 | `docs/git_workflow.md`（trunk-based） |
| IaC 建置前端架構 | `infra/terraform/`（Terraform azurerm 敘事: RG + Storage 靜態網站 + ACR + Container Apps） |
| AI Driven 系統 | 多 agent 分層協作的開發流程，見 `docs/ai_driven.md` |

## 版本狀態

| 環境 | 版本 | 說明 |
|---|---|---|
| `main` branch | v1.1.0 之後（未再打 tag） | 已合併 Portfolio Mini 元件、Weather Postcard 主題／日夜切換、zh/en 雙語化、部署 workflow 修正；本次再加入日文（ja），成為三語 |
| Azure 公開 demo | 追隨 `main` | 合併至 `main` 後由 `.github/workflows/deploy-demo.yml` 自動部署 |
| Phase 3（計畫中） | 未排程 | TDX 旅遊資訊串接；與分支名稱 `phase3-tourism` 無關，尚未開始 |

## 架構一覽

```
前端 (React/Vite)  ──►  FastAPI 後端  ──►  CWA（天氣 / UV / 月相 / 警特報）
 Azure Storage 靜態網站   Azure Container Apps   ──►  MOENV（AQI 即時 + 3 日預報）
                               │
                               ├─ Azure Container Registry (image)
                               ├─ Container Apps secrets (CWA_API_KEY / MOENV_API_KEY)
                               └─ Azure Monitor / Log Analytics
```

後端輸出：368 鄉鎮市區、7 天預報、72h 逐時趨勢、日出日落、月出月沒與月相、UV 日最大值、CWA 天氣警特報、即時 AQI 與 3 日預報、行前建議（規則式產生）。

## Phase 2 新功能（v1.1.0）

以下功能已實作並整合至 `main`（v1.1.0）：

- **CWA 天氣警特報**：從 `W-C0033-001` 取得並顯示縣市有效特報；有特報時以 warning banner 呈現。
- **月相與月出月沒**：CWA `A-B0063-001` 月出月沒時刻；月相與照光比例由後端本地計算並顯示圖示。
- **MOENV 即時 AQI**：從 MOENV `aqx_p_432` 取得最近測站即時空氣品質指數（AQI）。
- **MOENV 3 日 AQI 預報**：從 MOENV `aqf_p_01` 取得所屬空氣品質區 3 日 AQI 預報，並顯示於每日天氣卡。
- **常用鄉鎮快捷**：以 `localStorage` 儲存常用鄉鎮，顯示為可點選 chips；支援新增／刪除、重新排序、設定預設鄉鎮，以及跨操作保留目前選取日期。

## 多語支援（zh / en / ja）

介面支援繁體中文、English、日本語三語，右上角 segmented control 一鍵切換，選擇以 `localStorage` 與 URL `?lang=` 保存。後端 `/api/towns` 與 `/api/forecast` 皆接受 `lang=zh|en|ja`。

- **地名處理兩語不同**：368 鄉鎮市區、22 縣市與 1109 個 UV／空品測站，英文採各機構官方英譯（MOI TOWNCODE、CWA `StationNameEN`、MOENV `siteengname`）；**日文則一律沿用繁體中文原文**，因為台灣地名幾乎全為漢字，日文讀者可直接辨識，翻譯反而失真。
- **日文用語錨定日本氣象庁**：翻譯路徑為 **中 → 英 → 日**。以中央氣象署官方英文為樞紐，對應日本氣象庁官方英文，再取其官方日文，兩端皆錨在各自機構的出版品上，不經翻譯判斷。來源為氣象庁多言語辞書（7,278 筆，日／英／繁中並列）。
- **查表一律 fallback**：所有語系查表以 `entry.get(lang) or entry["zh"]` 回退，因此「日文沿用繁中地名」不需任何特例程式碼。
- **`<html lang>` 隨語言切換**：影響 CJK 字型選擇（中日共用漢字的地區字形不同）、斷行規則與螢幕閱讀器發音。

完整的用語錨定過程、證據分級與逐條裁定見 `docs/dev-process/developer_log.md`（2026-08-31 條目）。

## 外部資料來源（Live Mode）

| 來源 | 資料集代碼 | 說明 |
|---|---|---|
| CWA | `F-D0047-093` | 近端（今明後）各縣市 3 小時天氣預報 |
| CWA | `F-D0047-091` | 中遠端（4–7 天）各縣市 12 小時天氣預報 |
| CWA | `A-B0062-001` | 各縣市日出日落時刻 |
| CWA | `O-A0005-001` | 測站每日最大紫外線指數（官方約 14:00 發布，每日一次） |
| CWA | `O-A0001-001` | 自動測站坐標，供 UV 最近站映射使用 |
| CWA | `W-C0033-001` | 縣市天氣警特報 |
| CWA | `A-B0063-001` | 各縣市月出月沒時刻 |
| MOENV | `aqx_p_432` | 全台測站即時 AQI |
| MOENV | `aqf_p_01` | 各空氣品質區 3 日 AQI 預報 |

### 關於 UV 資料（O-A0005-001）

`O-A0005-001` 為 CWA 官方每日最大紫外線指數資料集，由各測站每日量測並約於 14:00 發布一次。每筆資料附有觀測日期（`Date`）但不提供當日峰值的精確時刻。後端以測站座標（`O-A0001-001`）就近映射；同一測站覆蓋範圍內的多個鄉鎮可能共享相同數值。若在 14:00 發布前查詢，前一日的最大值仍為 API 目前最新回傳值，屬正常行為，不是資料異常。

## 本機開發

**先決條件**：專案**零憑證即可跑**。未設 `CWA_API_KEY` 時後端自動進 mock 模式，回可重現的 22 筆鄉鎮與 7 天假資料；前端亦有 mock fallback。設有 `CWA_API_KEY`（與選填的 `MOENV_API_KEY`）時進 live mode：

- `/api/towns` 切到 CWA live catalog，從各縣市 `F-D0047-091` 族群彙整約 368 筆鄉鎮市區，保留靜態 22 筆名單作 fallback。
- `GET /api/forecast` 依目標日期切換資料集：近端走 `F-D0047-093`（3 小時資料集），較遠日期走 `F-D0047-091`（12 小時資料集）。
- 同一筆 forecast 另補上 `A-B0062-001` 日出日落、`A-B0063-001` 月出月沒、`O-A0005-001` 每日最大 UV（搭配 `O-A0001-001` 最近站映射）、`W-C0033-001` 天氣警特報，以及 MOENV `aqx_p_432` 即時 AQI 與 `aqf_p_01` 3 日預報。

```bash
# 後端
cd backend
python -m venv .venv && source .venv/bin/activate   # 或用既有 venv
pip install -r requirements-dev.txt
cp .env.example .env            # 憑證到手再填，不填就是 mock 模式
uvicorn app.main:app --reload --port 8080
#   → http://localhost:8080/docs  (自動 OpenAPI 文件)

# 前端（另開終端）
cd frontend
npm install
npm run dev                     # → http://localhost:5173，dev 代理 /api 到 8080
```

測試與 lint：

```bash
cd backend && pytest -q && ruff check .
cd frontend && npm run build
```

## 雲端部署（Azure）

> **注意**：目前 Azure 公開 demo 為 **v1.0.0 Phase 1**。v1.1.0（Phase 2）尚未重新部署至 Azure。

- **架構摘要**：前端部署到 Azure Storage 靜態網站（`$web` container），後端部署到 Azure Container Apps consumption plan，映像由 Azure Container Registry 保存，API 金鑰透過 Container Apps secrets 注入。
- **Demo URL（v1.0.0 Phase 1）**：前端 `https://twpfe5ce0.z23.web.core.windows.net/`、後端 `https://twp-backend.purplewave-91ee1594.southeastasia.azurecontainerapps.io`
- **延伸文件**：
  - 架構圖：`docs/cloud_architecture.md`
  - CI/CD：`docs/cicd_flow.md`
  - IaC：`docs/iac_overview.md`
  - 架構原則：`docs/architecture_overview.md`

## 安全設計

- 金鑰管理：CWA 與 MOENV 授權碼放在 Container Apps secret，由後端代理第三方 API，不進前端 bundle 或 repo。
- CORS：後端以已知前端網域作白名單，避免開放任意 origin。
- CI/CD 認證：`deploy-demo.yml`（部署骨架）設計採 GitHub OIDC 登入 Azure，不保存長期雲端金鑰。
- 傳輸安全：前後端公開入口皆使用 HTTPS，Storage account 設定最低 TLS 1.2。
- 憑證掃描：repo 內含 `.gitleaks.toml`，並已執行 gitleaks 全史掃描確認無 findings。

## 憑證（免費，實作到真資料時才需要）

- **CWA 授權碼**：https://opendata.cwa.gov.tw → 註冊氣象會員 → 取得授權碼 → 填入 `backend/.env` 的 `CWA_API_KEY`。
- **MOENV 授權碼**：https://data.moenv.gov.tw → 註冊會員 → 取得授權碼 → 填入 `backend/.env` 的 `MOENV_API_KEY`（選填；未設定時即時 AQI 使用示範值降級，3 日 AQI 預報留空）。

## 目錄

```
backend/       FastAPI（adapters / services / routers / schemas / tests）
frontend/      React + Vite + TypeScript（主要規劃頁）
frontend-mini/ React + Vite + TypeScript（Portfolio 首頁嵌入用的精簡版天氣卡片，phase3-tourism）
infra/         Terraform（前端託管 + 後端服務）
docs/          設計文件與流程圖
```

## 狀態

- ✅ **三語支援 zh / en / ja**（`main`）：
  - 介面三語切換（segmented control），選擇以 `localStorage` + URL `?lang=` 保存。
  - 天氣代碼、空品／紫外線等級、月相、警特報標題、行前建議皆已日文化。
  - 地名（鄉鎮／縣市／測站）在日文語系下沿用繁體中文原文；日文天氣用語錨定日本氣象庁官方對照。
  - 行前建議摘要改為兩行：天氣數據／行動建議。
- ✅ **v1.1.0（main，已發布）**：
  - CWA 天氣警特報（`W-C0033-001`）：有效特報以 warning banner 呈現於預報頁。
  - 月相與月出月沒（`A-B0063-001`）：月出月沒時刻來自 CWA；月相、圖示與照光比例由後端計算。
  - MOENV 即時 AQI（`aqx_p_432`）：最近測站 AQI 顯示於預報主頁。
  - MOENV 3 日 AQI 預報（`aqf_p_01`）：各日天氣卡顯示所屬空氣品質區預報。
  - 常用鄉鎮快捷（`localStorage`）：compact chips、edit mode、可排序、可設預設，切換時保留日期。
  - live mode 提供全臺約 368 筆鄉鎮市區，前端採縣市 → 鄉鎮兩階段選單。
  - 日期選擇為 today..today+6 的 7 天 chips，預設載入即顯示整週預報。
  - 行前建議固定聚焦使用者選取日，由後端規則式邏輯產生。
  - 72 小時逐時圖表呈現溫度、體感溫度、降雨機率與天氣圖示，點位過密時自動降低標註密度。
- ✅ **Portfolio 首頁 Mini 元件**（`frontend-mini/`，`phase3-tourism`，尚未發布）：
  - 獨立子專案，供個人網站首頁嵌入的精簡版天氣卡片。
  - 支援 compact 模式、AQI／UV 並列訊號、Demo Data 降級顯示。
- ✅ **Weather Postcard 主題與日夜切換**（`frontend/`，`phase3-tourism`，尚未發布）：
  - 主要規劃頁改用米白／紙白／海洋藍色系（Weather Postcard 主題），取代原本的科技藍配色。
  - 依真實日出日落時間（後端已提供的 `sunrise_sunset` 資料）自動切換：白天為暖色主題，夜晚沿用原本的冷色系配色；資料未載入前 fallback 為固定 06:00–18:00。
- ✅ **兩項查詢正確性修正**（`phase3-tourism`）：
  - 「今天」判定改以 Asia/Taipei 時區計算，避免跨時區誤判日期。
  - 強制執行 600 秒天氣快取政策。
- ✅ **Mock mode** 仍可零憑證 demo，保留既有 22 筆靜態鄉鎮與 deterministic fallback。
- ✅ **Public-demo deployment readiness**：Docker build、Terraform 範本、deploy workflow skeleton、runbook 已整理完成。
- ✅ **Azure public demo（v1.0.0 Phase 1）**：前端 Azure Storage 靜態網站，後端 Azure Container Apps，依 `docs/public_demo_runbook.md` 手動部署；本次 Phase 2 功能尚未重新部署。
- 📋 **Phase 3（計畫中）**：TDX 旅遊資訊串接，不包含在 v1.1.0 發布範圍。

## Public Demo Readiness

- Deployment runbook：`docs/public_demo_runbook.md`
- Terraform example：`infra/terraform/environments/dev/terraform.tfvars.example`
- Deploy workflow skeleton：`.github/workflows/deploy-demo.yml`

`main` 為目前的正式分支（最後一個 tag 為 v1.1.0，其後的合併未再打 tag）。Portfolio 首頁 Mini 元件、Weather Postcard 主題／日夜切換、zh/en/ja 三語支援與部署 workflow 修正皆已合併至 `main`。Azure 公開 demo 由 `.github/workflows/deploy-demo.yml` 在 `main` 更新時自動部署。

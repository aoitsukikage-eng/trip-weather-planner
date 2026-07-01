# Trip Weather Planner · 旅遊行前天氣規劃雲端系統

以中央氣象署(CWA)天氣資料為核心的旅遊行前規劃雲端後端。使用者選擇**目的地鄉鎮**與**旅遊日期**,系統整合天氣預報(核心)、周邊景點(擴充)、交通建議(挑戰),最後由 AI 產出一段自然語言行前建議。

> 國泰金控雲端開發工程師實習筆試作品。設計原則、三方收斂與決策見 `docs/`。

## 亮點對應題目

| 題目要求 / 加分項 | 本專案落點 |
|---|---|
| 雲端後端放 Python 程式碼 | FastAPI 容器化,部署 Cloud Run |
| 雲端架構圖 | `docs/cloud_architecture.md`(平台中立主圖 + AWS 映射) |
| 前端程式 | React + Vite + TypeScript 表單式查詢頁 |
| 串接第三方 REST API | CWA 天氣(P1)、TDX 景點/交通(P2/P3),後端代理 |
| CI/CD 流程圖 | `docs/cicd_flow.md` + `.github/workflows/ci.yml` |
| 多人協作 Git 流程圖 | `docs/git_workflow.md`(trunk-based) |
| IaC 建置前端架構 | `infra/terraform/`(前端託管 + 後端服務) |
| AI Driven 系統 | AI 行前摘要(產品)+ AI 輔助開發流程,見 `docs/ai_driven.md` |

## 架構一覽

```
前端 (React/Vite)  ──►  FastAPI 後端  ──►  第三方 API (CWA / TDX)
   靜態託管              Cloud Run          後端代理,key 不進前端
                          │
                          ├─ 快取 (熱門查詢)
                          └─ AI 摘要 (Gemini SDK,可降級為規則式)
```

## 本機開發

**先決條件**:專案**零憑證即可跑**。未設 `CWA_API_KEY` 時後端自動進 mock 模式,回可重現的假資料;前端亦有 mock fallback。

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

## 憑證(免費,實作到真資料時才需要)

- **CWA 授權碼**:https://opendata.cwa.gov.tw → 註冊氣象會員 → 取得授權碼 → 填入 `backend/.env` 的 `CWA_API_KEY`。
- **TDX Client Id/Secret**(P2/P3):https://tdx.transportdata.tw/register。
- **Gemini API key**(AI 摘要,選用):未設時自動用規則式摘要。

## 目錄

```
backend/    FastAPI(adapters / services / routers / schemas / tests)
frontend/   React + Vite + TypeScript
infra/      Terraform(前端託管 + 後端服務)
docs/       設計文件與流程圖
```

## 狀態

- ✅ Phase 1 骨架:後端 mock 端到端跑通(健康檢查 / 鄉鎮清單 / 預報 / 快取 / 錯誤處理),單元測試通過;前端建置通過。
- ⏳ 待憑證:接 CWA 真資料、部署 Cloud Run 取得公開 URL。
- ⏳ Phase 2/3:景點、交通、聊天機器人 overlay。

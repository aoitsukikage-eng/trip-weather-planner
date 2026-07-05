# 架構總覽與設計原則

## 題目理解

題目表面是「設計雲端後端放 Python 程式碼 + 架構圖」,實際評分大概在看:能否把 Python 放進合理的雲端執行模型、是否理解前後端分離與資料流與安全邊界、是否知道如何把個人開發擴展成團隊流程、是否只堆雲服務名詞還是真懂 why。

因此本案不只畫一張抽象雲端圖,也不只做單純 API,而是提交一個**能說服評審「這是能落地的小型雲端產品」**的完整閉環:以天氣為核心的旅遊行前規劃系統。

## 設計原則

1. **模組化單體,不做微服務**:規模尚小,微服務徒增複雜度;後端內部以 adapter、service、router、schema 分層,維持清楚邊界。
2. **Adapter 邊界**:`external → adapter → normalized schema → service → API`。外部資料解析集中在 adapter,不讓前端直接打第三方。
3. **後端代理第三方**:金鑰不進前端;統一格式、可加快取限流監控。
4. **架構圖與部署一致**:架構文件描述目前已交付的 Azure Storage 靜態網站、Azure Container Apps、Azure Container Registry、CWA adapter 與快取。
5. **零憑證可跑**:未設 key 時 mock 模式,讓每個階段都可 demo。


## 技術選型理由

- **FastAPI**:切題(Python 雲端後端)、型別清楚、**自動 OpenAPI 直接產出 API 規格交付物**、async 適合本案「一次打多個外部 API」的 I/O-bound 特性。
  - trade-off:相對於重用既有 Flask 經驗,需適應 async 心智模型;但淨值為正(自動文件 + 並發 + 型別即文件)。
- **React + Vite + TS**:展示型前端開發快、前後端分離清楚。


## 已交付範圍

- 縣市/鄉鎮兩階段選擇,live mode 由 CWA catalog 彙整約 368 筆鄉鎮市區。
- today..today+6 的 7 天日期 chips,預設載入即顯示整週預報。
- 7 天 daily summary:代表天氣、高低溫、最大降雨機率與規則式行前建議。
- 72 小時逐時圖表:溫度、體感溫度、降雨機率與天氣圖示。
- CWA 日出日落與紫外線資料,由後端整合後提供給前端。
- Azure public demo:前端 Azure Storage 靜態網站,後端 Azure Container Apps,映像保存在 Azure Container Registry。

## 文件導覽

- `cloud_architecture.md` — Azure 架構圖 + 資料流
- `frontend_plan.md` — 前端架構與資料流
- `cicd_flow.md` — CI/CD
- `git_workflow.md` — Git 協作
- `iac_overview.md` — Terraform azurerm 部署概述
- `ai_driven.md` — 多 agent 開發流程

## 已出貨 API 行為

- `GET /api/towns`
  - mock mode:回傳靜態 22 筆鄉鎮名單,維持零憑證可 demo。
  - live mode:由 22 個 CWA `F-D0047-091` 縣市資料集彙整全臺約 368 筆鄉鎮市區,並以 process-local cache 保存。
- `GET /api/forecast`
  - weather forecast 仍維持 `adapter -> normalize -> service -> router` 契約。
  - summary service 會聚焦 `target_date`,避免多日 horizon 時誤描述第一天。
  - auxiliary data 追加 `A-B0062-001` 日出日落與 `O-A0005-001` UV,其中 UV 會再 join `O-A0001-001` 測站座標後,以 township centroid 選最近站。
- 前端
  - 表單拆成縣市 → 鄉鎮兩階段。
  - 日期 UI 只允許 today..today+6,並以 `M/D（週X）` 顯示。
  - 行前建議面板顯示規則式建議,不暴露內部模式標示。
- 雲端部署
  - 前端以 Azure Storage 靜態網站 `$web` container 承接 React build。
  - 後端以 Azure Container Apps 執行 FastAPI 容器,搭配 Azure Container Registry 發版。
  - secret 先放在 Container Apps secrets,監控訊號進 Azure Monitor / Log Analytics。

# 架構總覽與設計原則

## 題目理解

題目表面是「設計雲端後端放 Python 程式碼 + 架構圖」,實際評分大概在看:能否把 Python 放進合理的雲端執行模型、是否理解前後端分離與資料流與安全邊界、是否知道如何把個人開發擴展成團隊流程、是否只堆雲服務名詞還是真懂 why。

因此本案不只畫一張抽象雲端圖,也不只做單純 API,而是提交一個**能說服評審「這是能落地的小型雲端產品」**的完整閉環:天氣為核心的旅遊行前規劃系統。

## 設計原則

1. **模組化單體,不做微服務**:規模尚小,微服務徒增複雜度;評審更重視「知道何時不該 over-engineer」。後端內部拆 `weather / poi / route / ai_summary` service。
2. **Adapter 邊界**:`external → adapter → normalized schema → service → API`。換第三方只改 adapter,不動 schema 與前端。
3. **後端代理第三方**:金鑰不進前端;統一格式、可加快取限流監控。
4. **架構圖畫滿、部署精簡**:圖展示 production 系統理解,Phase 1 只部署脊椎(FastAPI + CWA adapter + 快取 + 靜態前端)。
5. **零憑證可跑**:未設 key 時 mock 模式,讓每個階段都可 demo。
6. **AI 定位在加值不失焦**:產品層做摘要(可降級),開發層輔助流程。

## 技術選型理由

- **FastAPI**:切題(Python 雲端後端)、型別清楚、**自動 OpenAPI 直接產出 API 規格交付物**、async 適合本案「一次打多個外部 API」的 I/O-bound 特性。
  - trade-off:相對於重用既有 Flask 經驗,需適應 async 心智模型;但淨值為正(自動文件 + 並發 + 型別即文件)。
- **React + Vite + TS**:展示型前端開發快、前後端分離清楚。
- **Gemini via 標準 SDK**:不使用任何本機私有 wrapper,作品自我完備。

## 分階段

- **Phase 1(基本盤,可交)**:選鄉鎮 + 日期 → 天氣預報 + AI 摘要;後端 + 前端 + 部署 + CI/CD + IaC。
- **Phase 2**:TDX 景點,行前規劃頁。
- **Phase 3**:TDX 交通建議(門到門需自組或搭 Google Directions)。
- **Overlay**:聊天機器人入口——把服務當 tool,LLM 以 tool-calling 編排;與表單前端共用後端,是加法不是重做。

## 文件導覽

- `cloud_architecture.md` — 架構圖 + AWS 映射 + 資料流
- `frontend_plan.md` — 前端頁面與邊界
- `cicd_flow.md` — CI/CD
- `git_workflow.md` — Git 協作
- `iac_overview.md` — Terraform
- `ai_driven.md` — AI 在產品與開發的角色 + 資料治理

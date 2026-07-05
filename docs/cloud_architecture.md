# 雲端架構

## 設計原則

- **交付物與實際部署一致**:本專案最終交付採純 Azure 敘事,避免文件說一套、部署又是另一套。
- **架構圖畫滿(展示 production 思維),Phase 1 部署精簡(必須真的能跑)**。標 `[P1]` 為第一版實際部署,`[設計]` 為圖上展示、後續才落地。
- **前端不直連第三方 API**:所有外部呼叫由後端代理,金鑰不進前端 bundle,並可統一加快取、限流、錯誤處理、監控;換資料源前端不動。

## 主架構圖(Azure)

```mermaid
flowchart TB
  U["使用者瀏覽器"] --> SWA["Azure Static Web Apps Free"]
  SWA --> API["Azure Container Apps FastAPI"]
  API --> CWA["CWA 天氣 API"]
  API --> ACR["Azure Container Registry Basic"]
  API --> SEC["Container Apps secrets CWA_API_KEY"]
  API --> MON["Azure Monitor"]
  MON --> LA["Log Analytics"]
  API --> POI["景點 API TDX P2"]
  API --> ROUTE["交通 API TDX P3"]
  API --> AI["AI 摘要 Gemini SDK P1 可降級"]
```

## 成本與資源規格

- **前端**:Azure Static Web Apps Free,承接 React 靜態站點與 HTTPS。
- **後端**:Azure Container Apps consumption plan,`minReplicas=0`,`maxReplicas=1`,單一 revision 跑 FastAPI 容器。
- **容器規格**:0.5 vCPU / 1 Gi 記憶體,符合學生作品 demo 與 scale-to-zero 的成本目標。
- **映像儲存**:Azure Container Registry Basic,由 GitHub Actions 透過 `az acr build` 建置與保存 image。
- **憑證管理**:先以 Container Apps secrets 保存 `CWA_API_KEY`,避免把 secret 寫入 repo 或 image。
- **訂閱假設**:以 Azure for Students 或學生可取得的低成本訂閱為基準,控制常駐成本接近零。

## 資料流:使用者查詢

```mermaid
sequenceDiagram
  participant User
  participant SWA as Static Web Apps
  participant API as Container Apps FastAPI
  participant WX as CWA API
  participant AI as Gemini SDK

  User->>SWA: 開啟查詢頁
  SWA->>API: GET /api/forecast?town=...&date=...
  API->>WX: 呼叫 CWA API 並設 timeout
  WX-->>API: 原始預報
  API->>API: 正規化為 daily summary
  API->>AI: 結構化天氣 → 摘要(可降級為規則式)
  AI-->>API: 自然語言行前建議
  API-->>SWA: 標準化資料 + AI 摘要
  SWA-->>User: 呈現結果
```

## 資料集粒度正規化規則(API 契約)

- 目標日 **≤ 48h**:`F-D0047-093`(3h)聚合為當日摘要。
- 目標日 **> 48h**:`F-D0047-091`(12h)產日級摘要。
- `/api/forecast` 對外回傳**系統整理後的 daily summary**(高低溫、代表天氣、最大降雨機率、建議),不暴露兩資料集差異。

# 前端架構說明

前端採 React + Vite + TypeScript,目前交付單一查詢頁。使用者先選縣市,再選鄉鎮市區,系統載入 today..today+6 的 7 天天氣摘要與 72 小時逐時圖表。

## 畫面結構

1. **TripForm**:縣市 → 鄉鎮兩階段選單,送出後查詢預設日期。
2. **ForecastView**:7 天日期卡、規則式行前建議、日出日落、紫外線、72 小時逐時圖表。
3. **Mock badge**:只有在前端 fallback 資料被使用時顯示「示範資料」,避免把內部模式暴露給一般使用者。

## 前後端邊界

- 前端只存 UI state,不持有資料正規化邏輯。
- 天氣資料彙整、日期裁切、日出日落、紫外線與行前建議都在後端完成。
- 第三方 API 僅由後端存取,金鑰不進前端 bundle。

## 已實作元件

- `src/App.tsx`:管理 towns、forecast、chart result、loading/error state,並避免過期 request 覆蓋新結果。
- `src/components/TripForm.tsx`:縣市與鄉鎮市區選擇。
- `src/components/ForecastView.tsx`:日期卡、行前建議、日出日落、紫外線與逐時圖表。
- `src/lib/api.ts`:呼叫 `/api/towns` 與 `/api/forecast`;網路失敗時才使用前端 mock fallback。
- `src/lib/localDate.ts`:產生本地時區日期與 7 天日期視窗。

## 串接方式

- Dev:Vite 代理 `/api` → `localhost:8080`,免 CORS 煩惱。
- Prod:`VITE_API_BASE` 指向 Azure Container Apps 後端 URL;後端 CORS 白名單放前端網域。

## 測試現況

- `npm test` 以 Vitest + Testing Library 驗證 App、TripForm、ForecastView、API fallback 與日期工具。
- `npm run build` 執行 TypeScript build 與 Vite production build。

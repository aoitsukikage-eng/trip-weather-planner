# Trip Weather Planner 專案分析 v2

> 本文以舊 Block B project analysis 的穩定概念為起點，只重寫 `2f3ce32..fc2e37d` 的增量事實。量化、hash 與狀態判準以 [00_delta_evidence.md](00_delta_evidence.md) 為唯一 ledger。

## 1. Executive summary

Trip Weather Planner 是 React/Vite SPA + FastAPI modular monolith。瀏覽器只呼叫自有 REST-style API；後端代理 CWA 與 MOENV，將第三方資料正規化成穩定 schema，再由前端渲染一週天氣、72 小時趨勢、日月資訊、UV/AQI、警特報與行前建議。

截至 audited source `fc2e37d`：

- Phase 2 product release tag `v1.1.0` 指向 `faa6baa`，包含 warning、moon、AQI、常用鄉鎮與 celestial/status UI；local `main` 與 local origin refs 均在該 release。（證據：E-GIT-06、E-STATE-01）
- release 後的 Asia/Taipei today、跨午夜刷新、forecast no-store 與 600 秒 tracked cache policy 已 implemented，且 implementation head `59b5057` 有 2026-07-28 approved Verification Report；但尚未 merge、push 或 deploy，runtime `.env` 未切換。（證據：E-GIT-03、E-STATE-02）
- Azure public URLs 仍代表 v1.0.0 Phase 1 舊 demo，不是 v1.1.0 或 `fc2e37d`。（證據：E-STATE-03）
- Phase 3/TDX tourism 與 Portfolio mini 仍是 planned/proposed，不在 current source。（證據：E-STATE-03）

版本敘述必須注意：Git product release tag 是 `v1.1.0`，但 `backend/app/__init__.py` package metadata 仍是 `0.1.0`；兩者不能混用。（證據：E-CAVEAT-04）

## 2. Delta 規模與演進形狀

完整 ancestry range 是 96 commits、35 files、`+3832/-138`；first-parent 只有 5 個整合步驟。96 包含 release merge 帶入的 per-AC implementation/test/chore 歷史，不能說成「96 個線性整合 commits」。（證據：E-GIT-01、E-GIT-02）

變更量集中在：

- frontend：18 files、`+2267/-56`，主因是 celestial UI、favorite UI/state 與測試；
- backend：10 files、`+777/-27`，主因是 CWA/MOENV adapters、schema/router 與測試；
- docs：2 files、`+691/-2`，記錄 Phase 2 與 release 後驗收；
- root、workflow、infra：README 與 cache/deploy contract 的小幅同步。

release 後只有 4 commits、19 files、`+275/-28`；前兩筆改 application/config，後兩筆只改 developer log。（證據：E-GIT-03～E-GIT-05）

## 3. 產品能力

### 3.1 地點與預報

使用者以縣市/鄉鎮選取目的地。初始來源優先序是 custom default → last successful → `taipei-xinyi` → first town。live town catalog 由 CWA weekly county datasets 彙整；production code 的靜態完整性門檻是至少 300 筆，README 的「約 368」只屬文件/runtime observation。（證據：`d2c8042`, `frontend/src/App.tsx`; E-CAVEAT-03）

`GET /api/forecast` 回傳：

- 七天 `days`；
- near-term `hourly`，供 72h chart；
- target date 的 sunrise/sunset、moon；
- UV observation、current AQI、逐日 AQI forecast；
- weather warnings；
- rule-based 或 optional Gemini summary。

重要修正是資料集語意：production 不是「依日期二選一 dataset」，而是每次同時以 weekly family 產生 daily、near-term family 產生 hourly，再合為一個 response。（證據：E-BEH-02）

### 3.2 Phase 2 suitability signals

Phase 2 在既有 weather-first 產品上增加：

- `W-C0033-001` warning banner；
- `A-B0063-001` moonrise/moonset，加上本地 phase、icon、illumination、waxing；
- MOENV `aqx_p_432` current AQI 與 `aqf_p_01` forecast；
- UV/AQI severity gauge 與 celestial arc；
- favorites、default town、last successful town preference。

對應證據：`ed64802`、`e77b33e`、`192dbe3`、`e2e6040`、`c5e2a18`、`b35992b`、`d2c8042`；paths 見 E-GIT-06、E-BEH-03～E-BEH-05。

### 3.3 release 後 freshness

`ab685c6` 將 initial/main/favorite query 統一錨定 Asia/Taipei today，並讓長時間開啟的頁面在台北午夜 timer、focus 或 visibility return 時刷新 last successful town。日卡仍可明確查 non-today date；72h chart 保持 pinned。（證據：E-BEH-06；`frontend/src/App.tsx`, `frontend/src/lib/localDate.ts`）

`17909e3` 加上雙 no-store：

- browser forecast fetch：`cache: "no-store"`；
- backend `/api/forecast` response：成功與錯誤都 `Cache-Control: no-store`。

目的不是關閉所有 cache，而是讓 backend 成為 weather freshness 的唯一 TTL owner。（證據：E-BEH-07）

## 4. 架構

### 4.1 部署單元與責任

| 層 | 技術 | 責任 | current evidence |
|---|---|---|---|
| Browser SPA | React + TypeScript + Vite | selection、loading/error state、render、preference persistence、API client | `frontend/src/App.tsx`, `frontend/src/lib/*` |
| API | FastAPI | CORS、request ID、error envelope、route orchestration、response no-store | `backend/app/main.py`, `backend/app/routers/forecast.py` |
| Normalization | Python service functions | daily/hourly normalized contract | `backend/app/services/weather.py` |
| External adapters | httpx async clients | CWA/MOENV mapping、cache、timeout、typed upstream failure | `backend/app/adapters/{cwa,moenv}.py` |
| Process-local cache | `TTLCache` | keyed in-memory cache、lazy eviction | `backend/app/core/cache.py` |
| Public legacy deployment | Azure Storage + Container Apps | v1.0.0 Phase 1 old demo only | `README.md`, `docs/public_demo_runbook.md` |

這是 modular monolith，不是 microservices。Router 直接編排 adapters 與 normalization functions；不要畫成 service 持有 adapter 的強制鏈。（證據：`backend/app/routers/forecast.py`）

### 4.2 資料來源

| provider | dataset | current 用途 |
|---|---|---|
| CWA | `F-D0047-091` logical weekly family | daily slices |
| CWA | `F-D0047-093` logical near family | hourly slices |
| CWA | `A-B0062-001` | sunrise/sunset |
| CWA | `O-A0005-001` + `O-A0001-001` | UV + nearest station |
| CWA | `W-C0033-001` | county warnings |
| CWA | `A-B0063-001` | moonrise/moonset |
| MOENV | `aqx_p_432` | nearest current AQI |
| MOENV | `aqf_p_01` | air-quality-zone forecast |

CWA logical family 會映射至 county transport dataset；這讓 API response 保留業務語意，又能處理 aggregate endpoint 的相容性問題。（證據：`backend/app/adapters/cwa.py`）

TDX client settings 雖仍存在於 `backend/app/core/config.py`，但沒有 Phase 3 tourism adapter/route/UI；它不是 current capability。

## 5. 一次 forecast 的資料流

1. React 取得 towns；若 backend towns 失敗，`getTowns` 回三筆 frontend fallback。（證據：`frontend/src/lib/api.ts`）
2. 一般入口以 Asia/Taipei today 呼叫 `GET /api/forecast?town=&date=`；日卡才使用明確選取日。（證據：`ab685c6`, `frontend/src/App.tsx`）
3. FastAPI middleware 產生 request ID；forecast path 最終 response 加 `Cache-Control: no-store`。（證據：`17909e3`, `backend/app/main.py`）
4. Router 驗證 town、ISO date 與 today..today+10 prefilter，再查 `forecast:<town>:<requested-date>`。（證據：`backend/app/routers/forecast.py`）
5. cache miss 時，CWA adapter 取得 weekly daily + near hourly；normalizer 建立七日與 hourly contract。（證據：E-BEH-02）
6. 若 requested today 不在上游 horizon，response 可用第一個 available day，並回 `requested_date` + `date_adjusted=true`；其他缺 horizon 日期回錯。（證據：`67c78c4`, schema/router）
7. Router 各自取得 sun/UV、moon/warnings、AQI；各 group 可 degrade。（證據：E-BEH-04）
8. 組成 `ForecastData` + `AiSummary`，寫入 backend cache，包 `ApiResponse` envelope 回前端。（證據：schema/router/common）
9. 前端更新 current result；只有一般/地點查詢更新 pinned chart。successful query 才寫 `lastTown` preference。（證據：`frontend/src/App.tsx`, `frontend/src/lib/favoriteTowns.ts`）

## 6. Schema 與 adapter 邊界

`backend/app/schemas/weather.py` 是對內/對前端的 normalized contract，不讓 CWA/MOENV raw payload 穿透。Phase 2 的核心 schema delta 是 `AQIInfo`、`AQIForecast`、`WeatherWarning`、`MoonInfo` 與 date-adjustment fields。（證據：E-BEH-03）

Adapter 主要治理：

- 外部 HTTP 使用 `upstream_timeout_seconds`，tracked default 10 秒；
- CWA timeout/HTTP/JSON failures 轉為具 error code 的 `UpstreamError`；
- MOENV 接受 list 與 records wrapper；
- raw payload 在 adapter cache，再轉成 schema；
- partial source failure 在 router 層降級為 null/empty，而不是讓所有 forecast 消失。

這個邊界讓 frontend 只需要知道 project schema；也讓 future provider substitution 有明確切點。但 CWA adapter 已達 872 行，是技術債候選。（證據：`backend/app/adapters/cwa.py`, `backend/app/adapters/moenv.py`）

## 7. 狀態與快取治理

### 7.1 三種不同狀態

| 類型 | owner | 內容 |
|---|---|---|
| UI view state | React memory | current result、pinned chart、loading/error、selection |
| user preference | browser localStorage | favorites、default town、last successful town code |
| weather freshness cache | FastAPI process | normalized result + upstream raw data、按 key/TTL |

favorite bug 的根因不是 localStorage 快取 weather，而是 view-state target date 被錯誤沿用；`59b5057` 的 devlog 已明確澄清。（證據：E-BEH-05、C-04）

### 7.2 TTL policy

tracked source at `fc2e37d`：

- dynamic forecast result/raw CWA/MOENV：setting，預設 600 秒；
- warning：600；
- UV：3600；
- towns/stations：86400；
- sunrise/moon：31536000，且日期納入 key。

browser 不擁有 forecast freshness。這是 source/config policy；runtime 尚未切換，不能宣稱 deployed TTL 已是 600 秒。（證據：E-BEH-07）

### 7.3 process-local 限制

`TTLCache` 是單 process memory。scale-to-zero 後資料消失，多 replicas 不共享 cache，也沒有 request coalescing。這是 MVP 簡化，不應描述成 distributed cache。（證據：`backend/app/core/cache.py`）

## 8. 錯誤與 fallback 成熟度

目前做得好的部分：

- schema 驗證與 typed application errors；
- 統一 JSON error envelope，不外洩 internal exception；
- request ID 同時在 header/envelope；
- forecast HTTP 4xx/5xx 不被 frontend mock 掩蓋；
- partial enrichment 可為 null/empty；
- localStorage security/quota/JSON error 都不使 SPA crash；
- upstream clients 有 10 秒 timeout。

限制：

- browser forecast fetch 沒有 AbortController/client timeout；只依賴 network stack 與 backend timeout；
- `getTowns` catch-all 後靜默回 fallback，來源異常對使用者不可見；
- 沒有獨立 forecast-empty/cold-start UX；
- frontend `activeRequestRef` 忽略 stale response，但沒有真的 abort 先前 request。

證據：`frontend/src/lib/api.ts`, `frontend/src/App.tsx`, `frontend/src/lib/favoriteTowns.ts`; mini gap 見未來的 `06_portfolio_mini_contract.md`。

## 9. 測試與部署成熟度

### 9.1 latest verification

本卡沒有重跑。2026-07-28 Verification Report 對 `59b5057` 記錄：

- backend ruff PASS；
- backend pytest 48 passed；
- frontend test 110 passed；
- frontend build PASS。

這些只能標示 observed-via-report。`fc2e37d` 是 docs-only acceptance-status commit。（證據：E-VER-01）

### 9.2 release/deployment

| artifact | maturity |
|---|---|
| v1.1.0 Phase 2 source | merged to local main、local origin refs at `faa6baa`、tag points release |
| post-release fixes through `fc2e37d` | implemented + acceptance/report evidence；not merged/pushed/deployed |
| Azure public demo | deployed v1.0.0 Phase 1 old demo |
| deploy workflow/runbook | readiness material，不是新版部署證據 |
| runtime 600s TTL | not switched |

完整判讀見 E-STATE-01～03。

## 10. 限制與技術債

1. **README stale facts**：RC label 與 dataset selection 已落後；應修，但不在本卡 writable scope。（E-CAVEAT-01、02）
2. **version metadata drift**：Git tag v1.1.0 vs backend `0.1.0`。（E-CAVEAT-04）
3. **runtime/config drift**：tracked 600 秒尚未切 runtime。（E-STATE-02）
4. **CWA adapter size**：weather、towns、sun、UV、warning、moon 集中 872 行，可按 data domain 再拆。
5. **cache topology**：process-local，無 shared cache、single-flight 或 explicit invalidation。
6. **client cancellation**：無 AbortController，切換地點只忽略 stale result。
7. **state taxonomy**：loading/error 已有，empty/cold-start 尚未分開。
8. **CORS gap for Portfolio**：current defaults/known deployment origin 沒有 Portfolio origin。
9. **subpath hosting gap**：tracked Vite config 沒有 GitHub Pages `/labs/trip-weather/` base。
10. **future mini 不存在**：無 `frontend-mini/` source，也無 artifact；不得把 contract 當 delivery。

## 11. 可用的專案敘事

可誠實主張：

> 專案在 v1.0 weather planner 基線上，以可追溯的 Phase 2 release 增加 CWA/MOENV suitability signals、celestial visualization 與 local preference；之後再修正 Asia/Taipei date freshness 與 browser/backend cache ownership。最新 source 的 application change 有驗收報告，但仍未 merge/push/deploy，公開 Azure URL 是 v1.0.0 Phase 1 舊 demo。

不可主張：

- `fc2e37d` 已部署；
- Azure demo 是 v1.1/latest；
- runtime TTL 已切 600；
- Phase 3/TDX tourism 已做；
- Portfolio mini 或 `frontend-mini/` 已存在；
- README 的日期二選一 dataset 是 current production behavior。

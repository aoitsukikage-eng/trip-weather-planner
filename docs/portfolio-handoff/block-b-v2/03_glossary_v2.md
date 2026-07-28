# Trip Weather Planner Glossary v2

> 格式：定義 → 本專案用途 → 證據 → 狀態。`implemented` 只表示存在於 `fc2e37d`；部署與驗收狀態另看 [00_delta_evidence.md](00_delta_evidence.md)。

## A. API 與架構

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| FastAPI | 將 Python functions 暴露為 typed HTTP API 的 framework。 | 建立 app、middleware、exception handlers 與 forecast router。 | `backend/app/main.py`, `backend/app/routers/forecast.py` | implemented |
| React SPA | 在單一頁面以 component/state 更新 UI 的前端。 | 管理 towns、forecast、chart、loading/error、favorites。 | `frontend/src/App.tsx` | implemented |
| Modular monolith | 單一部署單元，內部以模組邊界分工。 | backend 由 router、adapter、service、schema、core 組成，沒有拆 microservices。 | `backend/app/` | implemented |
| REST-style API | 以 HTTP method/path/query 表達資源查詢；不宣稱完整 REST constraint。 | 三個 `/api` GET routes：health、towns、forecast。 | `backend/app/routers/forecast.py`; E-BEH-01 | implemented |
| Endpoint | 一個可呼叫的 HTTP method + path。 | `GET /api/health`、`GET /api/towns`、`GET /api/forecast`。 | `backend/app/routers/forecast.py` | implemented；delta 無新增 |
| API Client Layer | 前端集中封裝後端呼叫的邊界。 | `getTowns`、`getForecast`、envelope/error/mock parsing。 | `frontend/src/lib/api.ts` | implemented |
| Orchestration | 將多個 operation 按序組合，但不等同 domain normalization。 | forecast router 驗證、查 cache、呼叫 adapters、normalizers、組 schema。 | `backend/app/routers/forecast.py` | implemented |
| Adapter | 隔離外部 provider protocol/payload 的防腐層。 | CWA/MOENV HTTP、parser、mapping、raw cache、typed upstream errors。 | `backend/app/adapters/{cwa,moenv}.py`, `ed64802` | implemented |
| Normalization | 把來源時間片轉為 project-defined daily/hourly shape。 | `normalize_to_daily`、`normalize_to_hourly`、七日 trim。 | `backend/app/services/weather.py` | implemented |
| Pydantic schema | 具 runtime validation 的 Python data model。 | 定義 normalized weather、AQI、warning、moon、response envelope。 | `backend/app/schemas/{weather,common}.py` | implemented |
| Response envelope | 成功/失敗共同外殼。 | `success/data/error/meta`，meta 有 request ID、cached、source。 | `backend/app/schemas/common.py`, `backend/app/core/errors.py` | implemented |
| BFF-like | 後端為前端聚合多來源；此處不宣稱完整 BFF pattern。 | FastAPI 代理 CWA/MOENV，回單一 frontend contract。 | router + adapters | implemented，建議措辭 `BFF-like` |

## B. Forecast 與 provider

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| CWA | 臺灣中央氣象署資料 provider。 | weather、sun、UV/stations、warning、moon。 | `backend/app/adapters/cwa.py` | implemented |
| MOENV | 環境部資料 provider。 | current AQI 與 air-quality-zone forecast。 | `backend/app/adapters/moenv.py`, `ed64802` | implemented |
| Dataset family | 表達資料產品語意的一組 CWA dataset。 | `F-D0047-091` weekly、`F-D0047-093` near。 | `backend/app/adapters/cwa.py` | implemented |
| Logical dataset | 程式想要的資料語意。 | weekly/near 保持穩定，不依 county 編號改變。 | `ResolvedDataset.logical_dataset` | implemented |
| Transport dataset | 實際 HTTP request 的 county dataset。 | 依 town.city 映射到可用 endpoint。 | `resolve_live_dataset()` | implemented |
| Weekly + near composition | 同一次 forecast 同時使用兩族資料。 | weekly 產 daily，near 產 hourly；不是依 target date 二選一。 | `fetch_forecast_slices()`; E-BEH-02 | implemented；README 二選一說法 stale |
| TimeSlice | adapter parse 後、normalization 前的中間 shape。 | 承載 start/end、temperature、PoP、weather。 | `backend/app/schemas/weather.py` | implemented |
| DailyForecast | 一個 calendar day 的 normalized summary。 | 七日卡，含 high/low/PoP/weather/advice/AQI forecast。 | 同上 | implemented |
| HourlyForecast | normalized near-term slot。 | 72h chart 的 time/temp/apparent temp/PoP/weather。 | 同上 | implemented |
| Suitability signals | 輔助出遊判斷的非基本溫雨資訊。 | warning、moon、UV、AQI 與 advice。 | `ed64802`, schema/router/components | implemented in Phase 2 |
| AQI | Air Quality Index。 | nearest current station + zone forecast，失敗可 degrade。 | `backend/app/adapters/moenv.py` | implemented |
| Weather warning | CWA county warning。 | 解析豪雨/大雨/強風並回 severity。 | `backend/app/adapters/cwa.py` | implemented |
| Moon window | moonrise 到 moonset 的可見時間區間，可能跨午夜。 | today moonrise 未到時，可檢查 previous-day pair。 | `backend/app/adapters/cwa.py`, `858615f` | implemented |
| Illumination fraction | 月面照光比例，範圍 0..1。 | schema + celestial UI 顯示。 | `backend/app/schemas/weather.py`, `e77b33e` | implemented |
| Town catalog completeness gate | 防止 live towns payload 異常過小的門檻。 | 少於 300 entries 時丟 `town_catalog_incomplete`。 | `CWAAdapter.fetch_all_towns` | implemented；「約 368」僅 observation |
| TDX | 交通部觀光/運輸資料服務品牌。 | config 留有 credentials fields，但無 tourism adapter/route/UI。 | `backend/app/core/config.py`, README planned label | **planned Phase 3；not implemented** |

## C. 日期語意

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| Product timezone | 產品用來定義 calendar day 的固定 timezone。 | 一般查詢與午夜換日採 `Asia/Taipei`。 | `frontend/src/lib/localDate.ts`, `ab685c6` | implemented、accepted-via-report |
| Taipei today | Asia/Taipei 當下的 `YYYY-MM-DD`。 | initial/main/favorite query 的 date。 | `taipeiIsoDate()`, `frontend/src/App.tsx` | implemented |
| Explicit day selection | 使用者點日卡後指定 non-today date。 | 只在 `handleSelectDate` 使用 card date。 | `frontend/src/App.tsx` | implemented |
| Midnight rollover | 頁面跨 calendar day 後更新 stale query。 | timer + focus + visibility，刷新 last successful town。 | `ab685c6`, `App.tsx` | implemented |
| In-flight guard | 避免相同 rollover 同時發多筆 request。 | request/date refs 抑制 duplicate refresh。 | `App.tsx` | implemented |
| Date adjustment | requested today 不在上游 horizon 時改聚焦第一可用日。 | 回 `requested_date`、`date_adjusted`，而非拒絕 today。 | `67c78c4`, router/schema | implemented |
| Target date | response 真正聚焦的日。 | summary、sun/UV/moon 使用它。 | `ForecastData.target_date` | implemented |
| Requested date | client 原始請求日；只在 adjusted 時回。 | 說明 target 為何和 request 不同。 | `ForecastData.requested_date` | implemented |

## D. Cache 與 freshness

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| Cache key | 定義哪些 request 可共用資料的 identity。 | result key 為 `forecast:<town>:<requested-date>`。 | `backend/app/routers/forecast.py` | implemented |
| TTL | Cache entry 可被重用的時間。 | dynamic setting 600s；其他資料按更新頻率分級。 | `backend/app/core/config.py`, adapters, `17909e3` | source implemented；runtime 未切換 |
| Process-local cache | 只存在單一 backend process memory 的 cache。 | `TTLCache` thread-safe get/set、lazy eviction。 | `backend/app/core/cache.py` | implemented；非 distributed |
| Lazy eviction | 讀到過期 entry 時才刪除。 | `TTLCache.get()` 比 monotonic expiry。 | 同上 | implemented |
| Browser no-store | 要求 browser 不保存 forecast response。 | forecast fetch 使用 `cache:"no-store"`。 | `frontend/src/lib/api.ts`, `ab685c6` | implemented、accepted-via-report |
| Response no-store | HTTP response 禁止 browser/intermediary 保存。 | `/api/forecast` 成功/錯誤均加 header。 | `backend/app/main.py`, `17909e3` | implemented、accepted-via-report |
| Cache ownership | 哪一層負責 weather freshness。 | browser 放棄 cache；backend keyed TTL 是唯一 owner。 | E-BEH-07 | implemented in source |
| Cached metadata | 告知此次 response 是否命中 backend result cache。 | `meta.cached`。 | common schema/router | implemented |
| Runtime TTL | 真正執行環境當下採用的 TTL。 | Ubuntu real `.env` 尚未切 tracked 600s。 | `fc2e37d`, devlog/report | **not switched / not deployed** |

## E. Frontend state 與 persistence

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| View state | 當前畫面記憶體狀態。 | current result、pinned chart、loading/error、selection。 | `frontend/src/App.tsx` | implemented |
| Pinned chart | 日卡切換時保留初次 72h chart。 | `chartResult` 只在 `updateChart=true` 更新。 | `App.tsx` | implemented |
| Preference boundary | 只保存使用者偏好，不保存 domain response。 | favorites/default/last town codes。 | `frontend/src/lib/favoriteTowns.ts`, `c5e2a18` | implemented |
| localStorage | Browser key/value persistence。 | 保存上述三種 town preference；所有讀寫有 error guard。 | 同上 | implemented |
| Initialization priority | 自動選起始 town 的順序。 | custom default → last successful → Taipei Xinyi → first。 | `d2c8042`, `App.tsx` | implemented |
| Stale-response guard | 忽略較舊 request 晚到的結果。 | `activeRequestRef` sequence。 | `App.tsx` | implemented；不等於 cancellation |
| AbortController | Browser cancellation API。 | current full planner/mini 均未使用。 | repo search 無命中 | **not implemented** |
| Loading state | 正在取資料的 UI。 | button disabled、查詢中、towns loading。 | `App.tsx`, `TripForm.tsx` | implemented |
| Forecast empty state | 成功但無 forecast rows 的獨立 UI。 | current SPA 未獨立建模。 | `App.tsx` | **not implemented** |
| Cold-start state | 對 scale-to-zero 首次喚醒的獨立 UI。 | current SPA 未獨立建模。 | repo search | **not implemented** |

## F. Error、fallback 與 observability

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| AppError | 可預期、可安全回 client 的 typed error。 | invalid date、unknown town 等。 | `backend/app/core/errors.py` | implemented |
| UpstreamError | Provider timeout/HTTP/parse failure。 | CWA/MOENV adapter 轉成統一 502 類別。 | adapters | implemented |
| Partial degradation | enrichment 失敗但 base forecast 仍回。 | sun/UV、moon/warning、AQI group 可 null/empty。 | router | implemented |
| Frontend network fallback | browser 根本連不上 backend 時使用 inline mock。 | forecast 只在 `TypeError` fallback。 | `frontend/src/lib/api.ts` | implemented |
| Visible HTTP error | backend 已回 4xx/5xx 時不使用假資料。 | 轉 `ApiError` 顯示 error panel。 | 同上 + `App.tsx` | implemented |
| Demo Data | 明確告知資料是 fallback/demo。 | full planner source label可判 mock；future mini 要有可見標示。 | `isMockForecast`, source labels | full planner有基礎；mini proposed |
| Request ID | 一次 HTTP request 的識別。 | response header + envelope meta/error。 | `backend/app/main.py`, errors/common | implemented |
| Upstream timeout | Backend 等 provider 的上限。 | tracked default 10s，CWA/MOENV httpx 使用。 | config + adapters | implemented |
| Client timeout | Browser 等自有 backend 的上限。 | current fetch 無 timeout/AbortController。 | `frontend/src/lib/api.ts` | **not implemented** |

## G. Release 與證據狀態

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| Implemented | code/docs 存在 audited tree。 | 不推導 acceptance/deployment。 | E-STATE 判準 | `fc2e37d` tree |
| Accepted | 有 verification/acceptance evidence。 | `59b5057` 有 2026-07-28 approved report。 | E-VER-01 | accepted |
| Merged | commit 已進 integration ref。 | `faa6baa` 在 main；post-release 不在。 | local refs | Phase 2 yes；post-release no |
| Pushed | local origin tracking ref 包含 commit。 | origin refs 在 `faa6baa`。 | E-SNAP-01 | Phase 2 yes；post-release no |
| Deployed | 有版本對應上線證據。 | Azure 只有 v1.0.0 Phase 1 old demo。 | README/runbook | latest no |
| Observed-via-report | 本卡沒有重跑，只引用既有驗收結果。 | 48 backend、110 frontend、build PASS。 | E-VER-01 | evidence qualifier |
| v1.1.0 | Git product release tag。 | annotated tag dereference 到 `faa6baa`。 | E-STATE-01 | released source；not deployed |
| Backend `0.1.0` | FastAPI package metadata。 | 尚未同步 product tag。 | `backend/app/__init__.py` | implemented metadata drift |
| Azure v1.0.0 demo | Phase 1 public deployment。 | frontend Storage、backend Container Apps URLs。 | README | deployed old demo only |

## H. Future Portfolio mini 專用詞

| 詞條 | 定義 | 本專案用途 | 證據 | 狀態 |
|---|---|---|---|---|
| `frontend-mini/` | Future mini source directory。 | 不存在於 `fc2e37d` tree。 | E-STATE-03 | **proposed / not implemented** |
| `frontend-mini/dist/` | Future mini build artifact。 | 本卡禁止建立。 | task contract | **proposed / absent** |
| `VITE_TWP_API_BASE` | Future mini backend-base env name。 | Current app 用 `VITE_API_BASE`。 | `frontend/src/lib/api.ts` | **proposed** |
| `/labs/trip-weather/` | Future GitHub Pages subpath base。 | Current `vite.config.ts` 無 base。 | `frontend/vite.config.ts` | **proposed** |
| Portfolio CORS origin | Future Portfolio site origin allowlist。 | Current defaults只有 localhost；tracked Azure path是 old demo origin。 | config/runbook | **proposed** |
| Open Full Planner CTA | Mini 導向完整 demo 的連結。 | Future contract；target 是 v1.0 old demo時要明示版本。 | future `06` | **proposed** |
| Phase 3 tourism | TDX 景點/餐廳/地圖能力。 | 不屬 mini 或 current backend。 | README planned label | **planned / not implemented** |

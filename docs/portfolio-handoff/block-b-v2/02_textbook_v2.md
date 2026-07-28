# Trip Weather Planner 教材 v2：從 request 到 freshness

> 讀者假設：會寫基本 Python/TypeScript，但希望真正理解這個 repo。所有「本專案裡」的敘述都對應 audited source `fc2e37d`；證據索引見 [00_delta_evidence.md](00_delta_evidence.md)。

## 第 0 章：先建立版本邊界

本教材談三個不同版本面：

1. **v1.0.0 Phase 1 Azure old demo**：現在有 public URLs 的舊部署。
2. **v1.1.0 Phase 2 release `faa6baa`**：已 merge/push，tag 指向 release，但沒有新版部署。
3. **audited source `fc2e37d`**：在 release 上再加日期/cache fixes 與 docs；有 acceptance/report evidence，但未 merge/push/deploy。

如果不先切開，最容易把「source 已有」誤講成「線上已有」。（證據：E-STATE-01～03）

## 第 1 章：整體心智模型

一次查詢可以想成：

```text
React selection
  → frontend API client
  → FastAPI route
  → backend keyed cache
  → CWA weekly + near adapters
  → weather normalization
  → sun / UV / moon / warning / AQI enrichments
  → Pydantic response schema
  → JSON envelope
  → React view state
```

控制流是 Router 編排 adapters 與 pure normalization functions；不是 Service 持有 Adapter 的固定三層鏈。（證據：`backend/app/routers/forecast.py`）

## 第 2 章：FastAPI 是 contract orchestrator

FastAPI 在本案做四件核心工作：

1. route 與 query validation；
2. middleware：request ID 與 forecast no-store；
3. Pydantic response models；
4. application/upstream error 的統一 envelope。

現有 `/api` routes 仍只有：

```text
GET /api/health
GET /api/towns
GET /api/forecast?town=<code>&date=<YYYY-MM-DD>
```

Phase 2 沒有新增 route；它擴充 `/api/forecast` 的 schema 與 orchestration。（證據：E-BEH-01）

### 2.1 Query 不是任意字串

`town` 先查 static/live town catalog；找不到回 `unknown_town`。`date` 需符合 ISO `YYYY-MM-DD`，再經：

- today..today+10 prefilter；
- normalized daily horizon contains target 的檢查。

若「requested date 就是 Taipei today」但上游第一天已 rollover，router 可把 focused date 調到第一個 available day，並回：

```json
{
  "target_date": "實際聚焦日",
  "requested_date": "原本今天",
  "date_adjusted": true
}
```

這是 upstream horizon 相容機制，不代表所有 out-of-range 日期都被自動修正；其他缺失日期仍回 error。（證據：`67c78c4`, `backend/app/routers/forecast.py`）

### 2.2 Envelope 為什麼重要

成功與失敗都維持：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "cached": false,
    "source": "..."
  }
}
```

錯誤時 `success=false`、`data=null`，`error` 有 code/message。前端只要學一種外殼；request ID 可關聯 header 與 error。（證據：`backend/app/schemas/common.py`, `backend/app/core/errors.py`）

## 第 3 章：React 管的是 view，不是 weather truth

`App.tsx` 的 state 分成：

- `towns`：選單資料；
- `result`：目前日卡/summary；
- `chartResult`：刻意 pin 住的 72h chart；
- `loading`、`error`、`daySelectionError`；
- `selectedCity`、`selectedTownCode`；
- `favorites`、`defaultTownCode`。

一般 query 會同時更新 `result` 與 `chartResult`；點日卡只更新 `result`，所以使用者換聚焦日時，72h chart 不跳動。（證據：`frontend/src/App.tsx`）

### 3.1 Stale response guard

每次 query 增加 `activeRequestRef`。較舊 request 晚回來時，因 ID 不等於 current，結果被忽略。這能避免 out-of-order UI，但不是 cancellation：網路 request 仍在跑，因為沒有 AbortController。

### 3.2 現有狀態與尚缺狀態

已 implemented：

- towns loading；
- query loading；
- fatal query error；
- day selection error 且保留原畫面；
- favorite empty。

尚未獨立 implemented：

- forecast data empty；
- backend cold-start；
- retry countdown；
- explicit Demo Data banner contract。

這些缺口若要放 mini，必須標 proposed。

## 第 4 章：Adapter normalization 是防腐層

第三方 API 的欄位、wrapper 與 dataset 會變；如果 raw payload 直通 React，前後端會一起被上游綁死。Adapter 的任務是：

1. 打外部 HTTP；
2. 設 timeout；
3. 解讀 provider payload；
4. 將錯誤轉成 project error；
5. 產生內部 `TimeSlice` 或 domain models；
6. 管 raw-data cache。

### 4.1 CWA forecast 不是二選一

Production `fetch_forecast_slices(town)` 做：

```text
weekly logical F-D0047-091
  → county transport dataset
  → daily source slices

near logical F-D0047-093
  → county transport dataset
  → hourly source slices

daily + hourly → ForecastSlices
```

日期沒有傳進這個 method。`select_dataset(target_date)` 是遺留 helper，live production route 沒呼叫。README 的「依日期切 near 或 weekly」因此不能當 current truth。（證據：E-BEH-02、E-CAVEAT-02）

### 4.2 Logical 與 transport dataset

logical dataset 表達「weekly/near」業務語意；transport dataset 是實際 county endpoint。例如同樣是 near logical family，不同縣市用不同編號。response source 可表達 `logical via transport`，讓相容 mapping 不被隱藏。（證據：`backend/app/adapters/cwa.py`）

### 4.3 MOENV normalization

MOENV 可能直接回 list，也可能回 `{records: [...]}`。`_rows_from_payload` 同時接受兩者，再：

- current AQI：以 town lat/lon 找最近 station；
- forecast AQI：county → air-quality zone，再按 ISO date 建 dict。

沒有 MOENV key 時，current 回明示 demo value，forecast 空 dict；不可把 demo value 稱成 live observation。（證據：`67c78c4`, `backend/app/adapters/moenv.py`）

## 第 5 章：Schema 是前後端共同語言

### 5.1 Weather 主體

`ForecastData` 主要欄位：

```text
town
target_date
requested_date?
date_adjusted
source_dataset
days[]
hourly?
sunrise_sunset?
uv?
aqi?
warnings[]
moon?
generated_at
```

外層 `ForecastResult` 再加 `ai_summary`。

### 5.2 Null、empty list、missing 的差別

- `hourly`, `sunrise_sunset`, `uv`, `aqi`, `moon` 可為 null；
- `warnings` default empty list；
- `DailyForecast.aqi_forecast` 可為 null；
- TypeScript 對後來新增的 `aqi/warnings/moon` 保留 optional，增加 client 對舊 payload 的相容性。

UI 應把 null 解讀成「該 enrichment 無資料」，不能把整筆 forecast 判成失敗。

### 5.3 Moon contract

Moon 不只有圖示：

- `target_date`：使用者看的日期；
- `source_date`：實際採用哪一個 CWA moon window；
- `moonrise_time`, `moonset_time`；
- `phase`, `icon`, `illumination_fraction`, `waxing`。

跨午夜時，today 的 moonrise 尚未發生，程式可檢查 previous-day rise/set window，避免 marker 負值或顯示錯誤 pair。（證據：`e2e6040`, `858615f`, `backend/app/adapters/cwa.py`, `frontend/src/components/CelestialArc.tsx`）

## 第 6 章：日期語意要同時解決 timezone 與 rollover

### 6.1 為什麼不能只用 browser local date

產品語意明定 Asia/Taipei；使用者 browser 可能在其他 timezone。`taipeiIsoDate()` 用：

```typescript
new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Taipei",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})
```

因此「今天」由產品 timezone 決定，不由使用者 OS timezone 偶然決定。（證據：`ab685c6`, `frontend/src/lib/localDate.ts`）

### 6.2 哪些 action 用 today

- initial load：today；
- main form submit：today；
- favorite shortcut：today；
- day card click：card date。

favorite/localStorage 不保存 viewed date。這個 boundary 防止「昨天看某張卡，今天換 favorite 還查昨天」。（證據：`ab685c6`, `59b5057`）

### 6.3 開著頁面跨午夜

只在初次 render 算 today 不夠。頁面可能開一整晚，所以 current code：

- 算距下一個 Taipei midnight 的毫秒；
- `setTimeout` 到點檢查；
- focus 時檢查；
- visibility 回到 visible 時檢查；
- in-flight 時不重複；
- 同一新日期只 auto-refresh 一次。

這叫 freshness lifecycle，而不只是 date formatting。（證據：E-BEH-06）

## 第 7 章：Cache key 與 TTL 要分開理解

### 7.1 Key 回答「哪一份資料」

完整 result key：

```text
forecast:<town-code>:<requested-date>
```

不同 town、不同 requested date 不共享。即使 today 被 date-adjusted，key 仍保留 requested date 的隔離語意。

Raw CWA key 則含 dataset + sorted query params；sunrise 明確含 county + date。MOENV key 含 dataset。

### 7.2 TTL 回答「多久可重用」

| data | source policy |
|---|---:|
| forecast result / CWA raw forecast / MOENV | 600 秒 tracked default |
| warning | 600 秒 |
| UV | 3600 秒 |
| towns / station metadata | 86400 秒 |
| sunrise / moon | 31536000 秒，日期納 key |

不同 TTL 反映資料更新頻率，不是越短越好。UV 是每日資料，town metadata 更慢；天文資料由日期 key 隔離，可以長存。（證據：E-BEH-07）

### 7.3 Browser no-store 不等於沒有 cache

`fetch(..., {cache: "no-store"})` 與 response `Cache-Control: no-store` 防止 browser/intermediary 用舊 forecast；backend 仍可依自己的 keyed TTL 回資料，並在 envelope `meta.cached` 說明命中。

正確架構：

```text
browser: 不主張 freshness
backend: 唯一 freshness owner
provider: 上游 truth
```

### 7.4 Source policy 不等於 runtime 已生效

tracked config 預設是 600，但 devlog/report 明說 Ubuntu real `.env`/runtime 未切換。文件只能說「implemented and accepted in source」，不能說「已部署為 600 秒」。（證據：E-STATE-02）

## 第 8 章：localStorage 是 preference boundary

`favoriteTowns.ts` 只有三組 keys：

```text
trip-weather-planner:favorites:v1
trip-weather-planner:default-town:v1
trip-weather-planner:last-town:v1
```

它保存的是 town codes，不保存：

- forecast JSON；
- selected target date；
- generated_at；
- TTL；
- request ID；
- provider data。

讀寫都包 try/catch；corrupt JSON、quota 或 security errors 會 degrade，不 crash。這是 preference persistence，不是 client-side cache。（證據：`c5e2a18`, `frontend/src/lib/favoriteTowns.ts`）

## 第 9 章：Error 與 fallback 的正確層級

### 9.1 Browser network failure

`getForecast` 只有 fetch 丟 `TypeError` 時才用 frontend mock。HTTP 400/500 已有 response，不是 network failure，會轉成 `ApiError` 顯示。（證據：`frontend/src/lib/api.ts`）

這避免「後端明確拒絕，前端卻用假資料假裝成功」。

### 9.2 Backend partial upstream failure

sun/UV、moon/warnings、AQI 被分組 try/except；個別 `UpstreamError` 讓對應欄位 null/empty，而 base weather 仍可回。這是 partial degradation。

但 base forecast slices 若無資料或外部失敗，整筆 forecast 仍應失敗；不能無條件假裝有 live weather。

### 9.3 Mock 標示

- backend CWA mock：source label 含 `mock`；
- frontend fallback：`mock:frontend-fallback`；
- MOENV demo current：source label 明示「示範」。

Portfolio mini 若 future 使用 Demo Data，也必須同樣可見，不得偷偷混成 live。

## 第 10 章：Timeout 與 cancellation

Backend CWA/MOENV 都使用 `httpx.AsyncClient(timeout=settings.upstream_timeout_seconds)`，tracked default 10 秒。（證據：`backend/app/core/config.py`, adapters）

Frontend current fetch 沒有：

- AbortController；
- 5–10 秒 client timeout；
- timeout-specific UI。

`activeRequestRef` 只是不採用 stale result。Future mini contract 可規定 8 秒 default（允許 5–10 秒），但那是 proposed，不可回填成 current behavior。

## 第 11 章：測試策略要按 boundary 分層

從 repo tests 與 acceptance report可看出幾個層次：

1. **normalization/parser tests**：外部 payload variants、moon/UV/AQI edge；
2. **API tests**：schema、cache keys、no-store、date adjustment；
3. **frontend API tests**：HTTP error 不被 mock 掩蓋、no-store；
4. **React tests**：loading/error、favorite priority、date semantics、rollover；
5. **component tests**：celestial cross-midnight、favorite accessibility；
6. **build**：TypeScript/Vite integration。

latest observed-via-report 是 ruff PASS、backend 48 passed、frontend 110 passed、build PASS；本文件生成任務沒有重跑。（證據：E-VER-01）

測試仍不能證明：

- current public Azure 部署就是 latest source；
- runtime `.env` 的 TTL；
- 真實 provider 在此刻可用；
- Portfolio origin CORS；
- mini subpath/cold-start behavior。

## 第 12 章：Implemented 與 Planned 明確分區

### 12.1 Implemented at `fc2e37d`

- 三個 `/api` GET routes；
- weekly + near forecast composition；
- normalized weather/sun/UV/moon/warning/AQI schema；
- React full planner；
- favorites/default/last town preference；
- Asia/Taipei today + midnight lifecycle；
- browser/response no-store；
- backend keyed TTL policy；
- loading/error 與 partial fallback；
- tests in repo；latest結果由 acceptance report觀察。

### 12.2 Proposed / not implemented

- `frontend-mini/`；
- `VITE_TWP_API_BASE`；
- GitHub Pages base `/labs/trip-weather/`；
- Portfolio CORS origin；
- browser AbortController + 8-second timeout；
- explicit cold-start state；
- mini-specific Demo Data mode；
- Open Full Planner mini CTA；
- Phase 3 TDX attractions/restaurants/maps。

不要用未來式設計文件去改寫 current architecture。

## 第 13 章：自測題

### Q1：為什麼 forecast 不是依日期選 091/093？

因為 current production method 每次把 weekly daily 與 near hourly 都抓回，日期只影響 focus/enrichment，不影響二者是否被取用。`select_dataset` 是遺留 helper。

### Q2：no-store 後為什麼還可能 `meta.cached=true`？

no-store 管 browser/intermediary；`meta.cached` 指 backend process-local cache。兩者層級不同。

### Q3：favorite 是否會保存昨天的 forecast？

不會。localStorage 只存 town codes；昨天 date 污染是 view-state 使用錯誤，已由 `ab685c6` 修正並由 `59b5057` 記錄。

### Q4：48/110 tests 是你這次跑的嗎？

不是。本卡禁止 application tests/build；數字來自 2026-07-28 Verification Report，標 observed-via-report。

### Q5：最新 source 是否已上 Azure？

沒有。Azure URLs 是 v1.0.0 Phase 1 old demo；v1.1 Phase 2 未部署，release 後 fixes 更未 merge/push/deploy。

### Q6：Portfolio mini 在哪？

目前不存在。`06_portfolio_mini_contract.md` 只定義 future delivery contract，所有條目都應標 proposed/not implemented。

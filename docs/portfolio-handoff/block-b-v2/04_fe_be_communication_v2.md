# Trip Weather Planner FE/BE Communication Contract v2

> Current contract 對應 audited source `fc2e37d`。凡標 `proposed` 的欄位或行為都不存在於 current API，不可據此實作假設 current backend 已支援。證據總表見 [00_delta_evidence.md](00_delta_evidence.md)。

## 1. Contract scope

### 1.1 Current

- Protocol：HTTP/HTTPS + JSON。
- API style：GET-only REST-style query API。
- Current frontend env：`VITE_API_BASE`。
- Current backend upstream timeout：tracked default 10 秒。
- Current API inventory：`/api/health`、`/api/towns`、`/api/forecast`。
- Response：Pydantic normalized schema + common envelope。

### 1.2 Not current

- `VITE_TWP_API_BASE`：future mini proposed env。
- Portfolio origin CORS：not configured。
- browser 5–10 秒 timeout/AbortController：not implemented。
- mini-only fields、Demo Data flags、cold-start fields：not in API。
- Phase 3/TDX tourism endpoints：not implemented。

## 2. Base URL 與環境

Current frontend：

```typescript
const API_BASE = import.meta.env.VITE_API_BASE ?? "";
```

- local development：空字串，呼叫 relative `/api/...`；Vite dev proxy 轉到 `http://localhost:8080`；
- deployed frontend：build 時注入 backend absolute URL。

證據：`frontend/src/lib/api.ts`, `frontend/vite.config.ts`。

Future mini 可以採 `VITE_TWP_API_BASE` 以避免和 Portfolio 其他 lab 混淆，但 backend 不會讀這個變數；它只是 future frontend build-time config。詳見 `06_portfolio_mini_contract.md`。

## 3. CORS

FastAPI：

```text
allow_origins = settings.cors_origin_list
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

Current tracked default origins：

```text
http://localhost:5173
http://127.0.0.1:5173
```

Tracked Azure runbook/config path使用 old demo frontend origin：

```text
https://twpfe5ce0.z23.web.core.windows.net
```

Portfolio origin 尚未加入；即使 endpoint 可公開 GET，browser 仍會受 CORS 限制。Portfolio mini delivery 前必須先確定 exact origin，再由 backend runtime allowlist 加入。不得以 `*` 代替明確 origin。（證據：`backend/app/main.py`, `backend/app/core/config.py`, `docs/public_demo_runbook.md`）

## 4. Common response envelope

### 4.1 Success

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "cached": false,
    "source": "provider/cache/mock label"
  }
}
```

### 4.2 Expected error

```json
{
  "success": false,
  "data": null,
  "error": {
    "error_code": "invalid_date",
    "message": "Invalid date; expected YYYY-MM-DD."
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

`meta.cached`/`meta.source` 在 backend error JSON 未顯式提供，但 Pydantic success meta 會有；frontend error parser只依 `error`。Client 不應假設 error meta 一定含完整 success fields。（證據：`backend/app/schemas/common.py`, `backend/app/core/errors.py`, `frontend/src/lib/api.ts`）

### 4.3 Headers

- 所有正常 middleware response：`X-Request-ID`；
- `/api/forecast` 成功與錯誤：`Cache-Control: no-store`；
- CORS response：依 origin/middleware 決定。

證據：`17909e3`, `backend/app/main.py`。

## 5. `GET /api/health`

### Request

```http
GET /api/health
```

無 query。

### `data`

```json
{
  "status": "ok",
  "mock_mode": false
}
```

### Notes

- 只代表 app health handler 可回應與 CWA mock-mode flag；
- 不保證 CWA/MOENV live provider、public deployment version或所有 enrichment 正常；
- response 沒有 forecast-specific no-store header。

證據：`backend/app/routers/forecast.py`。

## 6. `GET /api/towns`

### Request

```http
GET /api/towns
```

無 query。

### `data[]`

```json
[
  {
    "code": "taipei-xinyi",
    "name": "信義區",
    "city": "臺北市",
    "lat": 25.03,
    "lon": 121.57
  }
]
```

### Source behavior

- backend mock：static towns，`meta.source="mock"`；
- live：CWA catalog，`meta.source="cwa-live"`；
- CWA upstream error：static fallback，`meta.source="static-fallback"`；
- frontend 若 request/parsing/response 失敗：`getTowns()` catch-all 回三筆 `MOCK_TOWNS`。

Live backend 聚合 county weekly datasets，少於 300 筆視為 incomplete。README 的「約 368」是 observation，不是 contract minimum；client 不應 hardcode 368。（證據：`backend/app/adapters/cwa.py`, `frontend/src/lib/api.ts`; E-CAVEAT-03）

## 7. `GET /api/forecast`

### 7.1 Request

```http
GET /api/forecast?town=<url-encoded-town-code>&date=<YYYY-MM-DD>
```

| query | required | contract |
|---|---|---|
| `town` | yes | town code；unknown → `unknown_town` |
| `date` | yes | ISO calendar date；parse fail → `invalid_date` |

Date prefilter 是 Taipei today..today+10；最終仍需落在 normalized seven-day horizon，或符合 missing-today adjustment。（證據：router）

### 7.2 `data`

```json
{
  "forecast": {
    "town": {
      "code": "taipei-xinyi",
      "name": "信義區",
      "city": "臺北市",
      "lat": 25.03,
      "lon": 121.57
    },
    "target_date": "2026-07-28",
    "requested_date": null,
    "date_adjusted": false,
    "source_dataset": "F-D0047-091 via ... + F-D0047-093 via ...",
    "days": [],
    "hourly": [],
    "sunrise_sunset": null,
    "uv": null,
    "aqi": null,
    "warnings": [],
    "moon": null,
    "generated_at": "ISO datetime"
  },
  "ai_summary": {
    "text": "行前建議",
    "mode": "rule-based"
  }
}
```

### 7.3 Town

| field | type |
|---|---|
| `code` | string |
| `name` | string |
| `city` | string |
| `lat` | number |
| `lon` | number |

### 7.4 DailyForecast

| field | type | nullable |
|---|---|---|
| `date` | `YYYY-MM-DD` string | no |
| `temp_high_c` | number | yes |
| `temp_low_c` | number | yes |
| `max_pop_percent` | integer | yes |
| `weather` | string | yes |
| `advice_hint` | string | yes |
| `aqi_forecast` | AQIForecast | yes |

`aqi_forecast`：

```json
{
  "date": "2026-07-28",
  "value": 42,
  "level": "良好"
}
```

### 7.5 HourlyForecast

| field | type | nullable |
|---|---|---|
| `time` | ISO datetime string | no |
| `temp_c` | number | yes |
| `apparent_temp_c` | number | yes |
| `pop_percent` | integer | yes |
| `weather` | string | yes |
| `weather_code` | string | yes |

整個 `hourly` 可為 null。

### 7.6 SunriseSunset

```json
{
  "county": "臺北市",
  "target_date": "2026-07-28",
  "source_date": "2026-07-28",
  "sunrise_time": "05:20",
  "sunset_time": "18:40",
  "is_approximate": false
}
```

整個 object、sunrise/sunset clock均可 null。`source_date != target_date` 時 `is_approximate=true`；UI 應顯示近似語意。

### 7.7 UVInfo

```json
{
  "value": 8,
  "level": "過量",
  "source_label": "目前紫外線",
  "source_type": "observation",
  "observed_at": "provider timestamp or null",
  "station_id": "id or null",
  "station_name": "name or null"
}
```

整個 object 可 null。non-today target 的 source label會明示「目前紫外線僅供參考」；這是 observation，不是 future UV forecast。

### 7.8 AQIInfo

```json
{
  "value": 42,
  "level": "良好",
  "station_name": "測站",
  "observed_at": "provider timestamp or null",
  "source_label": "目前空氣品質"
}
```

整個 object 可 null。沒有 MOENV key 的 backend demo current會標示「示範」；3-day forecast 留空。

### 7.9 WeatherWarning

```json
{
  "title": "大雨特報",
  "severity": "warning",
  "description": "..."
}
```

`warnings` 是 list，無資料時 `[]`，不是 null。

### 7.10 MoonInfo

```json
{
  "county": "臺北市",
  "target_date": "2026-07-28",
  "source_date": "2026-07-27",
  "moonrise_time": "18:42",
  "moonset_time": "05:11",
  "phase": "眉月",
  "icon": "🌒",
  "illumination_fraction": 0.18,
  "waxing": true
}
```

整個 object可 null；rise/set clocks可 null。`source_date` 可能為 previous day，以表達跨午夜 window；client 不可強制它等於 target。

### 7.11 AiSummary

`mode` current可能是：

- `rule-based`；
- `gemini`；
- `rule-based-fallback`；
- frontend fallback另使用自述 mock mode string。

Portfolio 文案應稱「行前建議」，除非 response mode確實為 Gemini；current public demo不應無證據宣稱 AI runtime active。

## 8. Forecast dataset semantics

Current production contract的 `days` 與 `hourly` 來自同一次組合：

```text
weekly F-D0047-091 logical family → daily
near F-D0047-093 logical family → hourly
```

不是：

```text
date <= 2 days ? near : weekly
```

`source_dataset` 因此可同時含 weekly + near labels。（證據：`ed64802`, `backend/app/adapters/cwa.py`; E-BEH-02）

## 9. Date contract

### 9.1 FE responsibility

- initial/main/favorite：送 Asia/Taipei today；
- day card：送 card date；
- open page跨 Taipei midnight：refresh last successful town once；
- 不從 localStorage取得 forecast date。

證據：`ab685c6`, `frontend/src/App.tsx`, `frontend/src/lib/localDate.ts`。

### 9.2 BE responsibility

- parse ISO date；
- Taipei today..today+10 prefilter；
- normalized horizon check；
- requested today missing時可 date-adjust；
- cache key仍以 requested town/date隔離。

證據：router/schema。

### 9.3 Client rendering

若 `date_adjusted=true`：

- 顯示 `target_date` 的資料；
- 可告知 requested today 被上游 horizon調整；
- 後續一般 query仍重新算 today，不沿用 adjusted target。

## 10. Cache contract

### 10.1 Browser

Current full frontend：

```typescript
fetch(url, { cache: "no-store" })
```

只有 forecast 明確設此 option；不要擴張成所有 endpoint contract。

### 10.2 HTTP response

FastAPI middleware對 `/api/forecast` success/error 設：

```http
Cache-Control: no-store
```

### 10.3 Backend

| cache | key idea | TTL source |
|---|---|---|
| final forecast | town + requested date | dynamic setting |
| raw CWA forecast | dataset + sorted params | dynamic setting |
| MOENV | dataset | dynamic setting |
| warning | dataset + county | 600 |
| UV | provider dataset | 3600 |
| town/station | metadata key | 86400 |
| sun/moon | county/date params | 31536000 |

Tracked dynamic default是 600 秒；runtime未切換，故這不是 deployed guarantee。（證據：E-BEH-07）

## 11. Timeout 與 errors

### 11.1 Backend upstream timeout

Tracked default：

```text
UPSTREAM_TIMEOUT_SECONDS=10
```

CWA/MOENV 都以 httpx AsyncClient使用。CWA區分 timeout、HTTP、invalid JSON error codes；MOENV目前統一 `moenv_upstream_error`。

### 11.2 Current frontend gap

Browser fetch沒有 AbortController或 explicit timeout。Future mini的 8 秒 default是 proposed contract，不是 current implementation。

### 11.3 Frontend fallback rules

Forecast：

- fetch network `TypeError` → inline mock；
- HTTP error → parse envelope、throw `ApiError`；
- invalid JSON/error response → visible request failure；
- 不因 4xx/5xx 偷換 Demo Data。

Towns：

- current client catch-all回 `MOCK_TOWNS`；此 behavior較寬鬆。

## 12. Current versus proposed fields

| concept | current API | proposed mini handling |
|---|---|---|
| `days`, `hourly`, sun/UV/AQI/warning/moon | yes | mini選擇 subset，不要求 backend新增 |
| `requested_date`, `date_adjusted` | yes | 可顯示 adjustment note |
| `meta.cached`, `meta.source` | yes | 可作 debug/label，不一定顯示全部 |
| `demo_data` boolean | no | client自行根據 source/fallback建模；若要 backend field需另開 API change |
| `cold_start` boolean | no | client loading copy/timer推測，不得偽裝 backend field |
| attraction/restaurant/map | no | Phase 3/TDX planned，mini不可要求 |
| Portfolio URL/CTA | no | pure frontend config/content |
| `VITE_TWP_API_BASE` | no backend field | future mini build env |

## 13. FE implementation checklist for current full planner

- URL encode town code；
- date使用 `YYYY-MM-DD`；
- success需同時檢查 HTTP `ok`、`body.success`、`body.data`；
- nullable enrichments各自處理；
- warnings預期 list；
- date-adjustment不污染下一次 general query；
- HTTP errors不可被 mock遮蔽；
- forecast request使用 browser no-store；
- stale response不得覆蓋新 selection；
- localStorage只保存 preference。

## 14. Contract status note

程式 contract到 `59b5057` 的 verification是 approved；`fc2e37d` 只追加 devlog acceptance status。以上不是 deployment證據。Azure v1.0.0 old demo可能仍提供較舊 schema，Portfolio若直接指向該 backend必須先做版本相容確認，不能假設它就是本文件的 `fc2e37d` contract。（證據：E-VER-01、E-STATE-03）

# Portfolio Trip Weather Mini：Future Delivery Contract

> **Status: PROPOSED / NOT IMPLEMENTED**
>
> 本檔只定義 future mini。`frontend-mini/`、build artifact、Portfolio integration、CORS change、deployment與 screenshot目前都不存在；本 evidence task沒有建立任何一項。

## 1. Product scope

### 1.1 Goal

在 Portfolio 的 `/labs/trip-weather/` 提供輕量 weather preview，讓訪客：

1. 選一個 town；
2. 看到 Asia/Taipei today 的精簡預報；
3. 明確知道資料是 Live 或 Demo Data；
4. 在 loading、empty、error、cold-start 情境下得到可理解回饋；
5. 以 CTA 開啟完整 Trip Weather Planner。

### 1.2 Mini 不是什麼

Mini 不應：

- 複製完整七日/72h/celestial dashboard；
- 新增或假設 backend routes；
- 加入 Phase 3/TDX attractions、restaurants、maps；
- 寫入 weather payload到 localStorage；
- 隱藏 fallback source；
- 將 Azure v1.0.0 old demo標成 latest；
- 在沒有 deployment evidence時宣稱 v1.1/post-release source已上線。

### 1.3 Minimum experience

Proposed initial screen：

- project title +「Weather preview」；
- town selector；
- today card：town、date、high/low、weather、PoP；
- optional compact signals：sunrise/sunset、UV、AQI、active warning count；
- `Last updated` / source label；
- `Open Full Planner` CTA；
- clear Live/Demo Data badge。

## 2. Delivery status vocabulary

未來每項 delivery tracking使用：

| status | meaning |
|---|---|
| proposed | 本 contract提出，未有 source |
| implemented | future source存在且可由 commit/path證明 |
| verified | 有 mini-specific test/build/acceptance evidence |
| integrated | 已進 Portfolio integration branch/ref |
| deployed | GitHub Pages/Portfolio URL有版本證據 |

本檔所有 implementation條目目前都是 `proposed`。

## 3. Future source 與 artifact contract

| Item | Proposed path | Current status |
|---|---|---|
| mini source root | `frontend-mini/` | not implemented；tree不存在 |
| mini Vite config | `frontend-mini/vite.config.ts` | not implemented |
| mini app source | `frontend-mini/src/` | not implemented |
| mini tests | `frontend-mini/src/**/*.test.ts(x)` | not implemented |
| build output | `frontend-mini/dist/` | not built；future artifact |
| Portfolio hosted path | `/labs/trip-weather/` | not configured |

Future artifact必須由 future source build產生，不進本 evidence task。是否 track `dist/` 由後續 Portfolio deployment policy決定；本 contract不預先決定 commit artifact。

## 4. Existing backend mapping

Mini優先重用 current backend contract，不要求新增 routes。

### 4.1 Town selector

```http
GET /api/towns
```

Use fields：

| Mini field | Existing API field | Required |
|---|---|---|
| id/value | `Town.code` | yes |
| label | `Town.city + Town.name` | yes |
| lat/lon | `Town.lat/lon` | no UI need |

注意：client不可 hardcode 368；repo靜態 contract只保證 live completeness gate ≥300，且 fallback可能更少。（證據：E-CAVEAT-03）

### 4.2 Today forecast

```http
GET /api/forecast?town=<code>&date=<Asia/Taipei YYYY-MM-DD>
```

Proposed mini mapping：

| Mini UI | Existing response field | Fallback rendering |
|---|---|---|
| town label | `forecast.town.city/name` | selected town label |
| requested today | request query | always calculate Asia/Taipei |
| focused date | `forecast.target_date` | required on success |
| adjustment note | `forecast.date_adjusted`, `requested_date` | hide if false/null |
| high/low | matching `forecast.days[].temp_high_c/temp_low_c` | `—` |
| weather text | matching day `.weather` | `資料不足` |
| rain | matching day `.max_pop_percent` | omit/`—` |
| sunrise/sunset | `.sunrise_sunset.*` | omit block if null |
| UV | `.uv.value/level/source_label` | omit if null |
| AQI | `.aqi.value/level/source_label` | omit if null |
| warning count | `.warnings.length` | 0 |
| advice | `.ai_summary.text` | optional |
| generated/source | `.generated_at`, envelope `meta.source` | display diagnostic/source copy |
| backend cached | envelope `meta.cached` | optional debug; not a staleness warning |

Mini不應要求 API fields `demo_data`、`cold_start`、`portfolio_url`，因 current schema沒有。若 UI需要，應在 mini client state建模，或另開明確 backend change task。

### 4.3 Dataset semantics

即使 mini只顯示 today，它依賴的 current forecast仍是：

```text
weekly daily + near hourly
```

Mini可以不渲染 hourly，但不能把 backend描述成「today所以只打 near dataset」。（證據：E-BEH-02）

## 5. Environment contract

### 5.1 Proposed variable

```text
VITE_TWP_API_BASE
```

用途：future mini build時注入 Trip Weather Planner backend base，例如：

```typescript
const API_BASE = import.meta.env.VITE_TWP_API_BASE ?? "";
```

Status：**proposed/not implemented**。

### 5.2 Current mismatch

現有 full frontend使用：

```text
VITE_API_BASE
```

證據：`frontend/src/lib/api.ts`。Future mini採不同名稱時，需要自己的 type/env docs，不可修改或聲稱 current full frontend已改名。

### 5.3 Backend target version

現有 Azure backend URL只證明 v1.0.0 Phase 1 old demo。Future mini如果先串它：

- CTA/API label都需寫 legacy Phase 1；
- 需確認它實際 response schema與此 audited contract相容；
- 不可假設 warning/moon/AQI/date-adjustment/no-store fields都已部署。

理想上，mini integration應等待一個有 deployment evidence的 backend target，再固定 `VITE_TWP_API_BASE`。

## 6. GitHub Pages base

Future Vite contract：

```typescript
export default defineConfig({
  base: "/labs/trip-weather/",
})
```

或與 Portfolio host方式等價、能產生同一 public path 的 config。

Required public base：

```text
/labs/trip-weather/
```

Status：**proposed/not implemented**。Current tracked `frontend/vite.config.ts` 沒有 `base`，且它屬 full frontend，不應為 mini任務直接覆寫。

驗證時需檢查：

- built `index.html` asset URLs含正確 base；
- browser直接開 `/labs/trip-weather/`；
- refresh/deep-link策略由 Portfolio host確認；
- assets不指向 `/assets/...` root而破壞其他 labs。

## 7. CORS contract

### 7.1 Current gap

Current tracked default：

```text
http://localhost:5173
http://127.0.0.1:5173
```

Tracked old Azure deployment path另使用：

```text
https://twpfe5ce0.z23.web.core.windows.net
```

Portfolio exact origin尚未加入。

### 7.2 Proposed requirement

Future delivery前：

1. 確認 Portfolio production origin，例如 `https://<portfolio-host>`；
2. 將 exact origin加入 backend runtime `CORS_ORIGINS`；
3. 保留必要 local dev origins；
4. 不使用 wildcard `*`；
5. 以 browser preflight/simple GET實際驗證；
6. 記錄 target backend version與deployment evidence。

Subpath `/labs/trip-weather/` 不是 CORS origin的一部分；CORS allowlist只含 scheme + host + port。

Status：**proposed/not implemented**。

## 8. Timeout and cancellation contract

### 8.1 Proposed client default

```text
8 seconds
```

規格允許範圍：5–10秒；預設採8秒，在 UX速度與 Azure scale-to-zero cold start之間取中間值。

### 8.2 Required behavior

Future mini應：

- 每次 towns/forecast request建立 AbortController；
- 8秒 timer後 `abort()`；
- component unmount、town change、新 request時取消舊 request；
- `finally`清 timer；
- timeout和manual abort分開處理；
- 不讓 stale response覆蓋新 town；
- timeout後提供 Retry與可選 Demo Data；
- error message不洩漏 internal provider detail。

Illustrative proposed flow（不是 current source）：

```typescript
const controller = new AbortController();
const timer = window.setTimeout(() => controller.abort("timeout"), 8_000);
try {
  return await fetch(url, {
    cache: "no-store",
    signal: controller.signal,
  });
} finally {
  window.clearTimeout(timer);
}
```

Current full frontend沒有 AbortController/client timeout；backend upstream tracked timeout是10秒。Mini 8秒 client timeout不代表 backend/provider request已停止，除非 disconnect cancellation能一路傳遞；文案不要過度承諾。

Status：**proposed/not implemented**。

## 9. Browser cache 與 backend ownership

Future forecast request required：

```typescript
fetch(url, {
  cache: "no-store",
  signal,
})
```

Mini不得：

- 將 forecast JSON長期寫 localStorage；
- 自己另設 weather TTL並和 backend競爭；
- 用 service-worker stale cache掩蓋 source；
- 把 envelope `meta.cached=true` 說成 browser cache。

Backend仍是唯一 weather cache owner：

```text
forecast:<town>:<requested-date>
```

以及 provider-specific keys/TTLs。Tracked dynamic default是600秒，但 runtime未切換，future integration必須以 target deployment evidence確認實際 policy。（證據：E-BEH-07、E-STATE-02）

Status：

- backend ownership：current source implemented；
- mini no-store：proposed；
- deployed runtime 600s：not established。

## 10. Asia/Taipei date contract

### 10.1 Today

Mini必須以產品 timezone而非 browser timezone產生 date：

```text
Asia/Taipei
```

建議重用和 `frontend/src/lib/localDate.ts` 等價的 `Intl.DateTimeFormat` 方法，不使用 UTC `toISOString().slice(0,10)` 作 calendar day。

### 10.2 Midnight rollover

Future mini若會長時間開啟，至少需：

- 計算下一個 Asia/Taipei midnight；
- 到點刷新 current town；
- window focus / visibility return時重新比較；
- in-flight時避免 duplicate refresh；
- 同一新日期只自動查一次；
- cleanup timer/listeners。

可以抽取 full frontend的已驗證概念，但 future source應有 mini-specific tests，不能只引用 full frontend tests當 mini verification。

### 10.3 Date adjustment

若 backend回：

```json
{
  "requested_date": "today",
  "target_date": "first available day",
  "date_adjusted": true
}
```

Mini顯示 target資料並提供小型 note，例如「上游今日資料已換檔，顯示首個可用日」。下一次 refresh仍重新算 Taipei today。

Status：**proposed/not implemented in mini**；full frontend/backend已有對應 concept。

## 11. State model

Future mini必須把狀態拆開，不以單一 spinner/error涵蓋全部。

### 11.1 Idle

- towns尚未取得或尚未選 town；
- 顯示 selector skeleton/disabled state；
- 不顯示過期 weather。

### 11.2 Loading

- first load或town switch；
- card使用 skeleton；
- selector可依 product choice鎖定；
- aria-live提示「正在取得天氣」；
- 8秒內不顯示 cold-start警告。

### 11.3 Cold-start

Proposed UI heuristic：

- request超過2秒仍 pending時顯示「服務可能正在喚醒，請稍候」；
- 它是 client heuristic，不是 backend `cold_start` field；
- 8秒 timeout後轉 error，不無限 spinner。

Current full frontend沒有獨立 cold-start state。

### 11.4 Success

- 顯示 town/date/核心氣象；
- 顯示 Live 或 Demo Data badge；
- nullable enrichment缺少時只隱藏/顯示「暫無」，不把整卡視為 error；
- `date_adjusted`顯示 note。

### 11.5 Empty

定義：HTTP/envelope成功，但 `days`為空或找不到 `target_date`/first day。

UI：

- 「目前沒有可顯示的預報」；
- Retry；
- 可選 Demo Data；
- 不以 `0°C`、`0%` 假裝真值。

Current backend通常在 base forecast empty時回 upstream error；mini仍需 defensive state。

### 11.6 Error

區分：

| Error | UI |
|---|---|
| timeout | 「服務回應較久」+ Retry + Demo Data |
| offline/network | 「目前無法連線」+ Retry + Demo Data |
| HTTP 4xx | 顯示安全message；不自動 fallback |
| HTTP 5xx/invalid JSON | general service error；提供 explicit fallback |
| CORS | general connection error；console可保留 technical detail |

HTTP error不得無聲切換 Demo Data。

### 11.7 Demo Data

必須是顯式 state：

- badge固定顯示 `Demo Data`；
- copy說明「目前顯示範例資料，不是即時天氣」；
- 使用者主動點 `Use Demo Data`，或設定明確 product-approved auto fallback；
- 若 auto fallback，仍需顯示原始連線失敗；
- data deterministic，方便測試；
- Retry Live Data保留；
- analytics若有，區分 live/demo。

Current full frontend有network fallback source label基礎，但 mini的可見 UX仍是 proposed。

## 12. Error/fallback precedence

Proposed decision table：

| Situation | Live card | Demo Data |
|---|---|---|
| 2xx valid + data | show | no |
| 2xx valid + empty | empty state | offer |
| 4xx known | error message | offer only after acknowledgement |
| 5xx | error | offer |
| timeout | cold-start → timeout error | offer |
| offline/network | error | offer |
| CORS/config | error | offer；do not call it provider outage |
| invalid JSON/schema | error | offer；log sanitized diagnostic |

## 13. Open Full Planner CTA

### 13.1 Current safe target

```text
https://twpfe5ce0.z23.web.core.windows.net/
```

Mandatory CTA label：

> Open Full Planner — Azure v1.0.0 Phase 1 legacy demo

Optional adjacent repo link：

```text
https://github.com/aoitsukikage-eng/trip-weather-planner
```

### 13.2 Future update rule

CTA只有在新版 full planner有 version-specific deployment evidence後，才可移除 legacy label或改 latest。Mini本身部署不等於 full planner已更新。

## 14. Accessibility and UX requirements

Proposed:

- selector有label；
- loading region使用 `aria-live="polite"`；
- error使用 `role="alert"`；
- Retry與Demo Data為真 button；
- focus不因 auto refresh被搶走；
- color不是 warning/AQI的唯一訊號；
- nullable value顯示 `—`，不顯示 `undefined`；
- motion尊重 `prefers-reduced-motion`；
- keyboard可完成town selection、retry、CTA；
- CTA若新分頁，說明行為並加安全rel attributes。

## 15. Security and privacy

Mini不持有CWA/MOENV keys；只呼叫自有 backend。

Required：

- 不在 frontend env放provider secret；
- `VITE_TWP_API_BASE`只放public backend URL；
- error copy不洩漏stack/provider credentials；
- CORS用exact Portfolio origin；
- 不把weather response當個資持久化；
- localStorage若保存town preference，沿用safe read/write並說明目的；MVP可完全不保存。

## 16. Observability proposal

若Portfolio已有analytics，可記：

- mini load；
- town query success/error/timeout；
- Demo Data activation；
- Open Full Planner CTA。

不可記：

- provider keys；
- full raw payload；
- stack trace；
-不必要的精確位置。

Envelope `request_id`可在support/debug copy中提供，但預設不需佔主要UI。

Status：**proposed/not implemented**。

## 17. Mini gap table

| Requirement | Current repo evidence | Gap | Status |
|---|---|---|---|
| mini source | `git ls-tree`無 `frontend-mini/` | 需建立 future source | not implemented |
| mini artifact | 無 `frontend-mini/dist/` | future build產生 | not implemented |
| API env | full app用 `VITE_API_BASE` | mini contract要 `VITE_TWP_API_BASE` | proposed |
| Pages base | tracked `frontend/vite.config.ts`無 base | mini需 `/labs/trip-weather/` | proposed |
| browser timeout | forecast fetch無 AbortController/timeout | 預設8秒，允許5–10秒 | proposed |
| stale request | full app只用sequence guard | mini應abort舊request | proposed |
| Portfolio CORS | defaults為localhost；runbook為Azure old frontend | 加exact Portfolio origin | proposed |
| browser cache | full forecast有 no-store | mini需同樣使用 | proposed |
| backend cache | source已有keyed TTL owner | target runtime需版本證據 | implemented source / deployment unknown |
| timezone | full app已有Asia/Taipei today | mini需移植並測試 | proposed in mini |
| midnight rollover | full app已有timer/focus/visibility | mini需移植並測試 | proposed in mini |
| loading | full app已有 | mini需專用compact state | proposed in mini |
| error | full app已有 | mini需timeout/CORS分类 | proposed in mini |
| forecast empty | full app無獨立state | mini需新增 | proposed |
| cold-start | full app無獨立state | mini需2s copy + 8s timeout | proposed |
| Demo Data | full app有inline fallback/source | mini需顯式badge/consent/retry | proposed |
| Full Planner CTA | old Azure URL存在 | label必須含v1.0 legacy | proposed mini UI |
| Phase 3/TDX | README標planned | 不在mini scope | not implemented / excluded |

## 18. Future delivery checklist

以下是後續任務清單，不代表本卡已完成：

### Product

- [ ] 鎖定mini顯示欄位與視覺密度。
- [ ] 決定預設town與是否保存town preference。
- [ ] 確認Demo Data是user opt-in或明示auto fallback。
- [ ] 確認Full Planner CTA仍指legacy demo或等待latest deployment。

### Backend target

- [ ] 選定有version evidence的backend URL。
- [ ] 驗證`/api/towns`、`/api/forecast`實際schema。
- [ ] 確認runtime TTL；不從tracked default推測。
- [ ] 加入exact Portfolio CORS origin並部署。
- [ ] 驗證forecast success/error均no-store。

### Source

- [ ] 建立future `frontend-mini/` task/branch。
- [ ] 設`VITE_TWP_API_BASE`。
- [ ] 設Vite base `/labs/trip-weather/`。
- [ ] 建typed envelope/weather subset。
- [ ] 實作Asia/Taipei date與midnight rollover。
- [ ] 實作AbortController + 8s timeout + cleanup。
- [ ] 實作idle/loading/cold-start/success/empty/error/demo states。
- [ ] 實作Open Full Planner CTA與版本label。

### Tests

- [ ] env/base path tests。
- [ ] Asia/Taipei timezone與midnight tests。
- [ ] timeout/abort/stale response tests。
- [ ] HTTP 4xx不自動fallback tests。
- [ ] empty/null enrichment tests。
- [ ] Demo Data badge/retry tests。
- [ ] accessibility tests。
- [ ] production build與subpath asset verification。

### Integration/deployment

- [ ] Portfolio exact origin與routing review。
- [ ] mini-specific acceptance。
- [ ] build `frontend-mini/dist/`。
- [ ] deploy `/labs/trip-weather/`。
- [ ] browser CORS/live/demo/cold-start smoke。
- [ ] 記錄commit、integration ref、deployment version/URL。
- [ ] 取得證據後再把facts sheet的mini狀態改為implemented/deployed。

## 19. Explicit non-delivery statement

截至本 contract：

- 沒有 mini app；
- 沒有 `frontend-mini/`；
- 沒有 `feature/portfolio-mini`；
- 沒有 build artifact；
- 沒有 screenshot；
- 沒有 Portfolio repo change；
- 沒有 CORS/runtime/service change；
- 沒有 deployment。

本檔的唯一產出是 future specification。

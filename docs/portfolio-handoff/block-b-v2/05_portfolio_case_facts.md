# Trip Weather Planner：Portfolio Case Facts

> 使用方式：此檔可直接提供 Portfolio 對話框作為唯一 facts sheet。若和舊文案衝突，以 [00_delta_evidence.md](00_delta_evidence.md) 的 evidence ledger 與本檔版本邊界為準。

## 1. Case identity

| 欄位 | 核准內容 | 證據 |
|---|---|---|
| Project | Trip Weather Planner／旅遊行前天氣規劃 | `README.md` |
| Repo | `https://github.com/aoitsukikage-eng/trip-weather-planner` | local `remote.origin.url`; E-SNAP-01 |
| Stack | React + TypeScript + Vite frontend；FastAPI/Python backend；Terraform/Azure deployment material | repo paths、`README.md` |
| Audited source | `fc2e37dace94c420ce2c3c18efcfb0a091e26774` | E-SNAP-01 |
| Product release tag | `v1.1.0` → `faa6baa` | E-STATE-01 |
| Public demo version | **v1.0.0 Phase 1 old demo** | `README.md`; E-STATE-03 |
| Future mini | proposed/not implemented | tree 無 `frontend-mini/`; E-STATE-03 |

## 2. Version labels：必須照用

### 2.1 對 source case study

建議標示：

> **Trip Weather Planner — v1.1.0 Phase 2 source + post-release accepted fixes (not deployed)**

更精確的長版：

> Case study audit covers the v1.1.0 Phase 2 release at `faa6baa` and post-release Asia/Taipei date/cache fixes through `fc2e37d`. Phase 2 is merged/pushed; post-release fixes have acceptance evidence but are not merged, pushed, or deployed.

證據：E-STATE-01、E-STATE-02。

### 2.2 對 public URLs

必須標示：

> **Full Demo — Azure v1.0.0 Phase 1 legacy public demo**

不可標 `latest`、`v1.1`、`fc2e37d` 或「目前 source deployment」。（證據：README deployment warning、E-STATE-03）

### 2.3 Backend package metadata

不要用 backend `/` 可能回的 `0.1.0` 代替 product release label；`backend/app/__init__.py` 尚未同步 Git tag。對 Portfolio 使用「Git product release v1.1.0」，並保留上述 deployment qualifier。（證據：E-CAVEAT-04）

## 3. Approved 可用 claims

以下句子可直接採用；每句已保留必要限定語。

| ID | approved claim | evidence |
|---|---|---|
| P-01 | Built a React/Vite frontend and FastAPI backend that normalize CWA weather data into a stable travel-planning contract. | `frontend/src/`, `backend/app/`; E-BEH-01～04 |
| P-02 | The current source combines weekly forecast slices for daily cards with near-term slices for the 72-hour view in the same forecast response. | `ed64802`, `backend/app/adapters/cwa.py`; E-BEH-02 |
| P-03 | Phase 2 expanded the response with weather warnings, moonrise/moonset and lunar illumination, current AQI, and AQI forecasts without adding API routes. | `ed64802`, `e77b33e`, `192dbe3`, schema/router; E-BEH-01、03 |
| P-04 | Added localStorage-backed favorite, default, and last-successful town preferences while keeping forecast freshness in the backend. | `c5e2a18`, `d2c8042`, `frontend/src/lib/favoriteTowns.ts`; E-BEH-05 |
| P-05 | Corrected general queries to use the Asia/Taipei calendar date and refresh an open page across Taipei midnight. | `ab685c6`, `frontend/src/{App.tsx,lib/localDate.ts}`; E-BEH-06 |
| P-06 | Disabled browser storage of forecast responses and made the backend the owner of keyed TTL cache policy. | `ab685c6`, `17909e3`, frontend api + backend main/router/adapters; E-BEH-07 |
| P-07 | The tracked source policy sets dynamic weather/MOENV data to 600 seconds while retaining source-specific longer TTLs; runtime was not switched. | `17909e3`, `fc2e37d`, devlog/report |
| P-08 | Uses explicit adapter, schema, error-envelope, timeout, and partial-degradation boundaries around CWA/MOENV integrations. | backend adapters/schema/errors/router |
| P-09 | v1.1.0 Phase 2 is merged/pushed and tagged at `faa6baa`, but it has not been deployed to the Azure public demo. | refs/tag/README; E-STATE-01 |
| P-10 | Post-release fixes through `fc2e37d` are implemented and supported by acceptance/report evidence, but are not merged, pushed, or deployed. | E-STATE-02 |
| P-11 | Latest verification results are backend ruff PASS, 48 backend tests passed, 110 frontend tests passed, and frontend build PASS—observed via the 2026-07-28 acceptance report, not rerun for this audit. | E-VER-01 |
| P-12 | The repository keeps an Azure v1.0.0 Phase 1 public demo and a separate, newer source history. | README URLs/version table; E-STATE-03 |

## 4. Claims 需要限定語

| 原始想法 | 必須改成 |
|---|---|
| 「約 368 towns 已由 repo 證明」 | 「文件/runtime observation 約 368；source code 可靜態證明的完整性門檻是 ≥300。」 |
| 「v1.1 的 cache 是 600 秒」 | 「tracked v1.1 post-release source policy 是 600 秒；runtime 尚未切換。」 |
| 「最新版本已驗收」 | 「application changes through `59b5057` 有 2026-07-28 approved report；`fc2e37d` 是其上的 docs-only status commit。」 |
| 「已部署 Azure」 | 「v1.0.0 Phase 1 old demo 已部署；v1.1 與 post-release fixes 未部署。」 |
| 「使用 AI 產生建議」 | 「支援 optional Gemini mode；無 key/default path 使用 rule-based，不能無 runtime evidence 宣稱 public demo 正在用 AI。」 |
| 「依日期選 near 或 weekly」 | 「current production response 同時組合 weekly daily + near hourly。」 |
| 「favorites 保存查詢狀態」 | 「favorites/default/lastTown 保存 town preference；forecast/date 不進 localStorage。」 |
| 「CI/CD 已部署最新版本」 | 「repo 有 workflow skeleton/readiness material；不構成 latest deployment evidence。」 |
| 「Full Demo」 | 「Full Demo (Azure v1.0.0 Phase 1 legacy public demo)」。 |

## 5. 禁止 claims

不得發布：

- `fc2e37d`、v1.1.0、Phase 2 或 600-second runtime 已部署；
- post-release fixes 已 merge/push；
- Azure URLs 是 latest source；
- Phase 3、TDX、景點、餐廳、地圖已實作；
- Portfolio mini、`frontend-mini/`、`VITE_TWP_API_BASE`、`/labs/trip-weather/` 已實作；
- Portfolio origin 已加入 CORS；
- browser fetch 已有 AbortController 或 5–10 秒 timeout；
- forecast empty/cold-start 已有獨立狀態；
- 本 evidence audit 重跑 48/110 tests 或 build；
- remote tag 已被本卡透過網路驗證；
- package version 已同步成 1.1.0；
- 「368」是本卡從 source 靜態枚舉出的精確數字；
- README 的 near/weekly 二選一是 current production behavior。

## 6. Feature facts

### 6.1 Current API

只有：

```text
GET /api/health
GET /api/towns
GET /api/forecast?town=<code>&date=<YYYY-MM-DD>
```

Phase 2 擴充的是 forecast contract/adapters/state/cache，不是 routes。（證據：E-BEH-01）

### 6.2 Current response capabilities

可用 case facts：

- town + focused/requested date；
- seven-day daily summaries；
- near-term hourly slots；
- sunrise/sunset；
- UV observation；
- current AQI + AQI forecast；
- warning list；
- moonrise/moonset + phase/illumination；
- advice summary；
- request ID、cached/source metadata。

證據：`backend/app/schemas/weather.py`, `backend/app/schemas/common.py`。

### 6.3 Current frontend behavior

- initial town priority：default → last successful → Taipei Xinyi → first；
- favorites最多 6個，可排序與設預設；
- day card會重查 focused date但保留 pinned 72h chart；
- initial/main/favorite query用 Asia/Taipei today；
- Taipei midnight/focus/visibility freshness；
- loading/error已實作；
- forecast empty/cold-start未獨立建模。

證據：`c5e2a18`, `d2c8042`, `ab685c6`, `frontend/src/App.tsx`, `frontend/src/lib/favoriteTowns.ts`。

### 6.4 Cache/fallback facts

- forecast browser fetch：no-store；
- forecast response：no-store；
- backend process-local keyed TTL cache；
- HTTP 4xx/5xx顯示 error，不用 mock掩蓋；
- network failure才允許 forecast inline fallback；
- upstream enrichments可 partial degrade；
- backend upstream timeout tracked default 10秒；
- frontend explicit client timeout：不存在。

證據：E-BEH-04、07；`frontend/src/lib/api.ts`。

## 7. Latest test/build results

> **Evidence qualifier: observed-via-report. This audit did not rerun application tests or build.**

| Check | Result | Evidence |
|---|---|---|
| Backend ruff | PASS | 2026-07-28 Verification Report |
| Backend pytest | 48 passed | same |
| Frontend npm test | 110 passed | same |
| Frontend build | PASS | same |
| Verification conclusion | approved | same |

驗收範圍是 implementation head `59b5057`。`fc2e37d` 只新增 devlog acceptance status，coding report亦確認沒有 application code變更。（證據：E-VER-01）

## 8. Merge/push/deploy inventory

### 8.1 已有

| Item | implemented | accepted | merged | pushed | deployed |
|---|---|---|---|---|---|
| Phase 2 through `faa6baa` | yes | acceptance evidence | yes | yes, local origin refs | no |
| Azure v1.0.0 Phase 1 | historical source | historical evidence | historical | historical | **yes, old demo** |

### 8.2 尚未

| Item | implemented | accepted | merged | pushed | deployed |
|---|---|---|---|---|---|
| `ab685c6` Taipei today/midnight | yes | approved report stack | no | no | no |
| `17909e3` cache/no-store policy | yes | approved report stack | no | no | no |
| `59b5057` root-cause devlog | yes | approved report | no | no | no |
| `fc2e37d` acceptance-status devlog | yes | records report | no | no | no |
| runtime 600-second TTL | tracked config only | source accepted | n/a | n/a | **not switched** |
| Portfolio mini | no | no | no | no | no |
| Phase 3/TDX tourism | no | no | no | no | no |

完整判準與 refs：E-STATE-01～03。

## 9. Links

### Repository

- GitHub repo：`https://github.com/aoitsukikage-eng/trip-weather-planner`
- Evidence：local `git config --get remote.origin.url`。

### Full Demo — legacy

- Frontend：`https://twpfe5ce0.z23.web.core.windows.net/`
- Backend：`https://twp-backend.purplewave-91ee1594.southeastasia.azurecontainerapps.io`
- Mandatory label：**Azure v1.0.0 Phase 1 legacy public demo**
- Evidence：`README.md`「雲端部署」、`docs/public_demo_runbook.md`。

本卡沒有對 URLs 做 live request；只能引用既有部署文件，不能保證此刻可用或 schema已更新。

## 10. Portfolio copy blocks

### 10.1 Short card

> **Trip Weather Planner** — A React + FastAPI weather-planning system that normalizes CWA and MOENV data into seven-day, hourly, celestial, UV/AQI, warning, and trip-advice views. The v1.1.0 Phase 2 source is released in Git; newer Asia/Taipei freshness and cache-policy fixes have acceptance evidence but are not deployed.

Evidence：P-01～P-10。

### 10.2 Engineering highlight

> I separated browser preference state from weather freshness: localStorage keeps only favorite/default/last town codes, forecast requests use browser no-store, and the backend owns town/date-keyed TTL caching. I also added Asia/Taipei midnight rollover so a long-open page does not keep querying yesterday.

Evidence：`c5e2a18`, `ab685c6`, `17909e3`; E-BEH-05～07。

### 10.3 Data-contract highlight

> The backend keeps provider quirks behind adapters and Pydantic schemas. Current production code combines weekly daily slices with near-term hourly slices, then enriches the response with sun, moon, UV, warnings, and AQI while allowing partial sources to degrade independently.

Evidence：`ed64802`, adapters/router/schema; E-BEH-02～04。

### 10.4 Demo CTA

> **Open Full Planner — Azure v1.0.0 Phase 1 legacy demo**

不要省略版本限定。Future latest deployment若完成，必須先取得新的 deployed evidence才能改標籤。

## 11. Portfolio integration handoff

Portfolio對話框可安全做：

- 使用上面 short card、engineering highlight、data-contract highlight；
- 顯示 repo link；
- 顯示 Full Demo，但保留 legacy v1.0.0 label；
- 顯示 latest verification，註明 observed-via-report；
- 把 mini標為「planned lab」或等實作後再發布。

Portfolio對話框目前不可做：

- 建立或宣稱 mini已完成；
- 把 old Azure demo當 latest；
- 把 future `06` contract轉述為 current feature；
- 宣稱 runtime TTL、Portfolio CORS、GitHub Pages base已完成。

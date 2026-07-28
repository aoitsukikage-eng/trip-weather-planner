# Trip Weather Planner Block B v2：Delta Evidence Ledger

> 稽核基準：`2f3ce32cdf60382d0fb9a2f67da48c69c06b7f80..fc2e37dace94c420ce2c3c18efcfb0a091e26774`
>
> 取證日期：2026-07-28；方法限於 Git、repo 文字與既有報告。本文未執行 application tests/build、未呼叫真實 CWA、MOENV、Azure 或 GitHub API。

## 1. 判讀規則

本文使用以下五個互不替代的狀態：

| 狀態 | 本次判準 |
|---|---|
| `implemented` | 程式或文件存在於 `fc2e37d` source tree。 |
| `accepted` | 有 Verification Report 或明確 acceptance evidence；只有實作或自述不算。 |
| `merged` | commit 已進入被檢查的 integration ref。本卡 integration target 尚待管理層決定，因此另檢查 local `main` 與 `phase3-tourism`。 |
| `pushed` | local remote-tracking `refs/remotes/origin/*` 包含該 commit。這是本卡禁止網路呼叫下可重現的 origin 證據。 |
| `deployed` | 有明確部署證據證明該版本已上線；deploy-ready、dev preview 或 runbook 均不等於 public deployment。 |

證據強度由高至低為 commit + path、commit 或 path、既有報告、文件/runtime observation、inference。沒有達到門檻的內容標示為 proposed、planned、unknown 或 observation。

## 2. 稽核快照

### E-SNAP-01：開始狀態

| 項目 | 結果 |
|---|---|
| isolated worktree | `trip-weather-planner-worktrees/task-20260728-twp-block-b-v2-evidence-audit` |
| branch | `task/20260728-twp-block-b-v2-evidence-audit` |
| HEAD | `fc2e37dace94c420ce2c3c18efcfb0a091e26774` |
| comparison base | `2f3ce32cdf60382d0fb9a2f67da48c69c06b7f80` |
| status | clean |
| canonical worktree | `trip-weather-planner` 位於 `faa6baa`、branch `phase3-tourism`；本卡未修改 |
| local `origin/main` | `faa6baad33c1b2ce3d6c16c3785120ecec474a80` |
| local `origin/phase3-tourism` | `faa6baad33c1b2ce3d6c16c3785120ecec474a80` |
| 本任務 origin ref | 不存在 |
| repo remote | `https://github.com/aoitsukikage-eng/trip-weather-planner.git` |

可重現指令：

```bash
git branch --show-current
git rev-parse HEAD
git rev-parse --verify 2f3ce32^{commit}
git rev-parse --verify fc2e37d^{commit}
git status --short
git worktree list --porcelain
git for-each-ref --format='%(refname) %(objectname)' refs/remotes/origin
git remote -v
```

### E-SNAP-02：唯讀 baseline

四份舊 Block B 文件位於 repo 外的 bridge reference 目錄，本卡開始時 SHA-256 全部吻合 task card：

| 文件 | SHA-256 |
|---|---|
| `trip-weather-planner_block_b_fe_be_communication.md` | `a42c9e4b108b23fd6b4a2a2df4694329923847f3b1837eaf59c9a8e17dc4eae0` |
| `trip-weather-planner_block_b_glossary.md` | `ec0dbea7e076430be70b07ea359d793d96fb6dcb4fdcd4ef3dec36cea8305478` |
| `trip-weather-planner_block_b_project_analysis.md` | `c58b19c59f8ce8e2694c80f249348a9e792397044533daae7ac9647018157195` |
| `trip-weather-planner_block_b_textbook.md` | `6771359d5ac1e1fb1f293c8973e5887e8e445b884ef6db6884fb023a59faba8c` |

可重現指令：

```bash
sha256sum /home/esgcenter0/agent-bridge/references/trip-weather-planner/block-b-v2-baseline/*.md
```

## 3. Range 指標

### E-GIT-01：完整 ancestry range

```bash
git rev-list --count 2f3ce32..fc2e37d
# 96

git diff --shortstat 2f3ce32..fc2e37d
# 35 files changed, 3832 insertions(+), 138 deletions(-)
```

交接所稱「約 96 commits／35 files／+3832/-138」重算吻合；因數字精確吻合，本文改以「96」而非「約 96」。這 96 是完整 ancestry range，包含 release merge 帶入的細粒度 per-AC commits，不是 96 個線性整合 commits。

### E-GIT-02：first-parent 整合步驟

```bash
git rev-list --first-parent --count 2f3ce32..fc2e37d
# 5

git log --first-parent --reverse --oneline 2f3ce32..fc2e37d
# faa6baa release: Trip Weather Planner v1.1.0 weather suitability (#1)
# ab685c6 fix: query weather with Taipei today
# 17909e3 fix: enforce 600-second weather cache policy
# 59b5057 docs: record date and cache policy root cause
# fc2e37d docs: record cache policy acceptance status
```

因此正確敘述是「96 個 ancestry commits、5 個 first-parent 整合步驟」。

### E-GIT-03：release 後 delta

```bash
git rev-list --count faa6baa..fc2e37d
# 4

git diff --shortstat faa6baa..fc2e37d
# 19 files changed, 275 insertions(+), 28 deletions(-)
```

四筆依序為 `ab685c6`、`17909e3`、`59b5057`、`fc2e37d`。其中程式驗收針對 implementation head `59b5057`；`fc2e37d` 只在其上追加 devlog acceptance-status，沒有再改 application code（證據：兩筆 commit stat 與既有 Verification Report）。

## 4. Changed-files 分群

### E-GIT-04：top-level 分群

| top-level | files | insertions | deletions |
|---|---:|---:|---:|
| `(root)` | 1 | 93 | 49 |
| `.github` | 1 | 1 | 1 |
| `backend` | 10 | 777 | 27 |
| `docs` | 2 | 691 | 2 |
| `frontend` | 18 | 2267 | 56 |
| `infra` | 3 | 3 | 3 |
| **合計** | **35** | **3832** | **138** |

可重現指令：

```bash
git diff --numstat 2f3ce32..fc2e37d
git diff --name-status 2f3ce32..fc2e37d
```

以 `git diff --numstat` 的 path 第一段聚合；root 檔案單獨歸入 `(root)`。

### E-GIT-05：file-type 分群

| 類型 | files |
|---|---:|
| `.css` | 1 |
| `.example` | 2 |
| `.md` | 3 |
| `.py` | 9 |
| `.tf` | 2 |
| `.ts` | 6 |
| `.tsx` | 11 |
| `.yml` | 1 |
| **合計** | **35** |

以檔名最後一個 `.` 後綴聚合；因此 `backend/.env.example` 歸 `.example`。

完整 name-status 為：1 個 workflow、`README.md`、10 個 backend、2 個 docs、18 個 frontend、3 個 infra。可直接用 `git diff --name-status 2f3ce32..fc2e37d` 重現，沒有 `frontend-mini/`。

## 5. Commit timeline 與完整 hash 對照

### E-GIT-06：timeline

| 時段 | 事實 | 代表證據 |
|---|---|---|
| 2026-07-09 | 開啟 Phase 2 developer log。 | `e7ae6a0`, `docs/dev-process/developer_log.md` |
| 2026-07-15～20 | 加入目的地 suitability signals：CWA 警特報、月相/月出月沒、MOENV AQI 與 schema/router wiring，後續修正 MOENV list payload 與 missing-today。 | `ed64802`, `67c78c4`; `backend/app/{adapters,routers,schemas}` |
| 2026-07-21～25 | 多輪月相、照光比例、縣市標籤、跨午夜 celestial arc、UV/AQI gauge 與介面修正；大量 per-AC test/chore commits 位於 ancestry 中。 | `e77b33e`, `192dbe3`, `e2e6040`, `858615f`; `frontend/src/components/CelestialArc.tsx` |
| 2026-07-26 | 加入常用鄉鎮 preference persistence、UI、單一選取狀態與初始化優先序。 | `c5e2a18`, `b35992b`, `d2c8042`; `frontend/src/lib/favoriteTowns.ts`, `frontend/src/App.tsx` |
| 2026-07-27 | `faa6baa` 將 Phase 2 合併為 v1.1.0 release；local `main`、`phase3-tourism`、`origin/main`、`origin/phase3-tourism` 與 annotated `v1.1.0^{}` 均指向此 commit。 | `faa6baa`, local refs |
| 2026-07-27 | release 後修正一般查詢使用 Asia/Taipei today、跨午夜刷新與 browser no-store。 | `ab685c6`; `frontend/src/App.tsx`, `frontend/src/lib/{api,localDate}.ts` |
| 2026-07-27 | 將動態 weather/MOENV/warning policy 收斂為 600 秒，forecast response 也設 `Cache-Control: no-store`；只改 tracked config/runbook，runtime 未切換。 | `17909e3`; `backend/app/{core/config.py,main.py,adapters}`, `docs/public_demo_runbook.md` |
| 2026-07-27～28 | 記錄根因與 acceptance 狀態。程式驗收針對 `59b5057`；`fc2e37d` 是其上方 docs-only status commit。 | `59b5057`, `fc2e37d`, Verification Report |

### E-GIT-07：本文主要短 hash 對照

| short | full |
|---|---|
| `2f3ce32` | `2f3ce32cdf60382d0fb9a2f67da48c69c06b7f80` |
| `e7ae6a0` | `e7ae6a0f6ab318712afbaac923120050ed58a426` |
| `ed64802` | `ed64802a1ad66021b91dcbbea452143f4c099adb` |
| `67c78c4` | `67c78c4082798faea2970d73e28ade05e0f89f38` |
| `e77b33e` | `e77b33e099d18152537cc2a141708a93c4562df6` |
| `192dbe3` | `192dbe3b2f18f4bc4fdecf5ac80da1de5e020af2` |
| `e2e6040` | `e2e60404c315dc219f8498e029bc37f90c40681a` |
| `858615f` | `858615fbc6dcadb9c69a4eb3b8f9ea756d47cd6f` |
| `c5e2a18` | `c5e2a186a3cdf07dd3bb17d238213f2cf0acec78` |
| `b35992b` | `b35992b4a718b8fea3b54c26de8d6d0c27c1ee28` |
| `d2c8042` | `d2c80420bd209ac90dade24f9bcd90c35ffd6144` |
| `faa6baa` | `faa6baad33c1b2ce3d6c16c3785120ecec474a80` |
| `ab685c6` | `ab685c6c286e143b74227ea1963b4e325d92aa93` |
| `17909e3` | `17909e35a7fe2d0a08030bd30f422da67483a206` |
| `59b5057` | `59b50575563200bb591fe68447a37c5d4d0fded6` |
| `fc2e37d` | `fc2e37dace94c420ce2c3c18efcfb0a091e26774` |

完整 96 筆可用下列命令取得，不把它們誤寫為 first-parent timeline：

```bash
git log --reverse --format='%H|%h|%ad|%s' --date=short 2f3ce32..fc2e37d
```

## 6. 功能與行為 delta

### E-BEH-01：API inventory 沒有新增 route

`backend/app/routers/forecast.py` 在 range 前後仍只有：

| method | endpoint | 現況 |
|---|---|---|
| GET | `/api/health` | health、mock mode |
| GET | `/api/towns` | mock/static fallback 或 CWA live catalog |
| GET | `/api/forecast?town=<code>&date=<YYYY-MM-DD>` | 聚合後的 forecast contract |

`git diff 2f3ce32..fc2e37d -- backend/app/routers/forecast.py` 顯示變更是 import、編排、response fields 與 fallback，沒有新增 `@router` route。`backend/app/main.py` 另有既存的 `GET /` service metadata，不屬於 `/api` inventory。

### E-BEH-02：forecast 是 weekly + near 組合

Production code 的 `CWAAdapter.fetch_forecast_slices(town)` 每次都：

1. 以 `F-D0047-091` logical weekly dataset 取得 daily 原料；
2. 以 `F-D0047-093` logical near-term dataset 取得 hourly 原料；
3. 回傳 `ForecastSlices(daily=weekly, hourly=near, source_label="weekly + near")`。

證據：`ed64802`、`backend/app/adapters/cwa.py` 的 `fetch_forecast_slices`；router 再由 `normalize_to_daily` 與 `normalize_to_hourly` 組成單一 response（`backend/app/routers/forecast.py`）。`select_dataset(target_date)` 仍存在，但 production forecast 路徑沒有呼叫它。

因此 README「依目標日期切換 093 或 091」是落後敘述，不可作為最新 production behavior。

### E-BEH-03：Phase 2 response contract 擴充

`ForecastData` 新增：

- `requested_date`、`date_adjusted`：若上游 horizon 缺今天，可將 requested today 調整到第一個可用日；
- `aqi`：最近測站即時 AQI；
- `warnings`：CWA 警特報；
- `moon`：縣市、target/source date、月出月沒、phase/icon、`illumination_fraction`、waxing；
- `DailyForecast.aqi_forecast`：逐日 AQI 預報。

證據：`ed64802`、`67c78c4`、`e77b33e`、`192dbe3`、`e2e6040`；`backend/app/schemas/weather.py`、`backend/app/routers/forecast.py`。

### E-BEH-04：adapter 與 fallback

- CWA：weather、sunrise/sunset、UV、warnings、moon；logical dataset 映射至 county transport dataset，錯誤轉為 `UpstreamError`，httpx 使用設定 timeout。證據：`ed64802`、`backend/app/adapters/cwa.py`。
- MOENV：`aqx_p_432` current AQI、`aqf_p_01` forecast；支援 API 直接 list 或 `{records: [...]}`，無 MOENV key 時 current 回明示「示範」值、forecast 留空。證據：`ed64802`、`67c78c4`、`backend/app/adapters/moenv.py`。
- partial upstream failure 不使整筆 forecast 崩潰：sun/UV、moon/warnings、AQI 分組捕捉 `UpstreamError`。證據：`backend/app/routers/forecast.py`。

### E-BEH-05：frontend state 與 preference boundary

- 常用地點最多 6 個，可新增、刪除、排序、設預設；初始化優先序為 custom default → last successful → `taipei-xinyi` → first town。證據：`c5e2a18`、`b35992b`、`d2c8042`；`frontend/src/lib/favoriteTowns.ts`、`frontend/src/App.tsx`。
- `localStorage` 只保存 favorite codes、default town code、last successful town code；不保存 forecast payload、target date、cache 或 TTL。證據：`frontend/src/lib/favoriteTowns.ts`。
- React memory state 分開保存當前 result 與 pinned `chartResult`；點日卡重查該日但不更新 72h chart。證據：`frontend/src/App.tsx`。
- UI 已有 towns loading、query loading、error panel、day-selection error；沒有獨立 forecast-empty 或 cold-start state。證據：`frontend/src/App.tsx`、`frontend/src/components/ForecastView.tsx`。

### E-BEH-06：日期與跨午夜 freshness

- 一般查詢、initial load、favorite shortcut 都使用 `Intl.DateTimeFormat(... timeZone: "Asia/Taipei")` 算 today；只有日卡點選帶明確 non-today date。
- 頁面以 Asia/Taipei 下一個午夜 timer、window focus、visibility return 檢查換日；in-flight/date guards 防止重複刷新。

證據：`ab685c6`；`frontend/src/App.tsx`、`frontend/src/lib/localDate.ts`。

### E-BEH-07：cache ownership 與 no-store

| 層 | policy at `fc2e37d` | 證據 |
|---|---|---|
| browser forecast fetch | `{ cache: "no-store" }` | `ab685c6`, `frontend/src/lib/api.ts` |
| forecast HTTP response | `/api/forecast` 成功與錯誤均 `Cache-Control: no-store` | `17909e3`, `backend/app/main.py` |
| full forecast result key | `forecast:<town>:<requested-date>`，TTL `settings.cache_ttl_seconds` | `backend/app/routers/forecast.py` |
| raw CWA forecast | dataset + sorted params key，TTL setting | `17909e3`, `backend/app/adapters/cwa.py` |
| MOENV current/forecast | `moenv:<dataset>`，TTL setting | `17909e3`, `backend/app/adapters/moenv.py` |
| CWA warnings | 600 秒 | `17909e3`, `backend/app/adapters/cwa.py` |
| UV | 3600 秒 | `backend/app/adapters/cwa.py` |
| towns/stations | 86400 秒 | `backend/app/adapters/cwa.py` |
| sunrise/moon | date-keyed、31536000 秒 | `backend/app/adapters/cwa.py` |

Tracked `Settings.cache_ttl_seconds` 是 600 秒（`17909e3`, `backend/app/core/config.py`），但 acceptance evidence 明確說 Ubuntu 真實 `.env` 與 runtime 尚未切換。因此只能說「source/config policy 已實作並 accepted」，不可說「public/runtime 600 秒已生效」。

## 7. Test/build 證據

### E-VER-01：observed-via-report

本卡沒有重跑 application tests/build。latest 可引用結果來自 2026-07-28 Verification Report：

| command 類別 | 報告結果 | 本文標示 |
|---|---|---|
| backend ruff | PASS | observed-via-report |
| backend pytest | 48 passed | observed-via-report |
| frontend npm test | 110 passed | observed-via-report |
| frontend build | PASS | observed-via-report |

來源：`/home/esgcenter0/agent-bridge/reports/acceptance/task-20260727-twp-query-date-cache-policy-codexvs-verification.md`。該報告驗收 implementation head `59b5057`；`fc2e37d` 只追加 `docs/dev-process/developer_log.md` 的 acceptance-status（亦見 coding report `task-20260728-twp-cache-policy-devlog-acceptance-codexcli-report.md`）。

## 8. implemented / accepted / merged / pushed / deployed 矩陣

### E-STATE-01：Phase 2 release（截至 `faa6baa`）

| 範圍 | implemented | accepted | merged | pushed | deployed |
|---|---|---|---|---|---|
| Phase 2：warnings、moon、AQI、favorites、celestial/status UI | 是：source tree at `faa6baa` | 是：`docs/dev-process/developer_log.md` 多筆明確 approved/accepted evidence | 是：`faa6baa` 是 local `main`/`phase3-tourism` tip，parent 含 Phase 2 history | 是：local `origin/main` 與 `origin/phase3-tourism` 指向 `faa6baa` | **否**：README 明示 Azure demo 仍是 v1.0.0 Phase 1 |

annotated tag `v1.1.0^{}` 指向 `faa6baa`。local origin refs 證明 release commit pushed；本卡未使用網路查詢，故不額外宣稱 remote tag 狀態。

### E-STATE-02：release 後（`ab685c6..fc2e37d`）

| 範圍 | implemented | accepted | merged | pushed | deployed |
|---|---|---|---|---|---|
| Taipei today/midnight/no-store、600 秒 tracked policy、root-cause/devlog status | 是：`ab685c6`, `17909e3`, `59b5057`, `fc2e37d` | 是：2026-07-28 Verification Report 驗收 `59b5057`；`fc2e37d` 記錄該 status | **否**：local `main` 與 `phase3-tourism` 仍在 `faa6baa`；integration target pending | **否**：所有 local `origin/*` 仍在 `faa6baa`，無 task ref | **否**：無新版部署證據；runtime TTL 也未切換 |

這段不能簡化成「branch accepted，所以已 merged/deployed」。

### E-STATE-03：公開 demo

| 項目 | 狀態 | 證據 |
|---|---|---|
| Azure frontend/backend URLs | deployed，但僅 v1.0.0 Phase 1 舊 demo | `README.md`「版本狀態」「雲端部署」 |
| v1.1.0 Phase 2 | merged/pushed/tagged source，未部署 | `faa6baa`, refs, `README.md` |
| `fc2e37d` latest audited source | implemented/accepted evidence，未 merge/push/deploy | refs + reports |
| planned Phase 3 / TDX tourism | planned、not implemented | `README.md` |
| Portfolio mini / `frontend-mini/` | proposed、not implemented | `git ls-tree -r --name-only fc2e37d` 無該路徑 |

## 9. Evidence caveats

### E-CAVEAT-01：README release label 落後

README 仍把 `phase2-dev` 寫成 v1.1.0 RC，並說「合併 main、打 tag 後才正式」；但 local refs 與 tag 已顯示 `main`/`origin/main` 在 `faa6baa`，`v1.1.0^{}` 也指向該 release。版本狀態應以 Git refs 為準，README 是 stale label。

### E-CAVEAT-02：README dataset selection 落後

README 說 forecast 依目標日期二選一 near 或 weekly；production `fetch_forecast_slices` 實際每次同時取 weekly daily + near hourly。應以 `backend/app/adapters/cwa.py` 為準。

### E-CAVEAT-03：「約 368 towns」證據層級

README 與 runtime/devlog observation 稱 live catalog 約 368；repo 靜態可重現的完整性條件只有 `fetch_all_towns()` 在 `< 300` 時丟 `town_catalog_incomplete`。因此：

- 「live 約 368」只能標示 document/runtime observation；
- 「production code 有 >=300 完整性門檻」是可靜態取證事實；
- 不把 368 寫成由本卡程式靜態計數所得。

### E-CAVEAT-04：package version 未同步

產品 Git tag 是 `v1.1.0`，但 `backend/app/__init__.py` 的 `__version__` 仍為 `0.1.0`。對外談 release 應明說「Git product release tag v1.1.0」，不把 backend package metadata 誤報成 1.1.0。

## 10. Claim-to-evidence

| claim ID | 可用 claim | commit | repo/report evidence | 狀態 |
|---|---|---|---|---|
| C-01 | Phase 2 增加 CWA warning、moon、MOENV AQI 與 response fields，沒有新增 API route。 | `ed64802`, `e77b33e`, `192dbe3` | `backend/app/routers/forecast.py`, `backend/app/schemas/weather.py`, adapters | implemented；Phase 2 acceptance evidence |
| C-02 | forecast dataset 是 weekly daily + near-term hourly 的同次組合。 | `ed64802` | `backend/app/adapters/cwa.py` | implemented |
| C-03 | CWA 與 MOENV 失敗可局部 degrade，且 upstream client 有 timeout。 | `ed64802` | adapters + router | implemented |
| C-04 | favorite 是 localStorage preference，不是 weather cache。 | `c5e2a18`, `d2c8042`, `59b5057` | `frontend/src/lib/favoriteTowns.ts`, `frontend/src/App.tsx`, devlog | implemented；root cause documented |
| C-05 | 一般查詢以 Asia/Taipei today 為準，頁面會處理跨午夜。 | `ab685c6` | `frontend/src/App.tsx`, `frontend/src/lib/localDate.ts` | implemented、accepted-via-report |
| C-06 | browser 不快取 forecast；backend 擁有 keyed TTL cache。 | `ab685c6`, `17909e3` | `frontend/src/lib/api.ts`, `backend/app/main.py`, router/adapters | implemented、accepted-via-report |
| C-07 | tracked dynamic TTL policy 是 600 秒，但 runtime 未切換。 | `17909e3`, `fc2e37d` | `backend/app/core/config.py`, devlog, reports | implemented/accepted；not deployed |
| C-08 | latest acceptance report 為 ruff PASS、48 backend、110 frontend、build PASS。 | `59b5057`, `fc2e37d` | 2026-07-28 Verification Report | observed-via-report；本卡未重跑 |
| C-09 | Phase 2 v1.1.0 release 在 `faa6baa`，已在 local origin refs，未部署。 | `faa6baa` | refs、tag、README deployment warning | merged/pushed；not deployed |
| C-10 | `fc2e37d` 未 merge、push、deploy。 | `fc2e37d` | local main/origin refs + devlog/report | implemented/accepted evidence only |
| C-11 | Azure URLs 是 v1.0.0 Phase 1 舊 demo。 | `2f3ce32` deployment baseline | `README.md`, `docs/public_demo_runbook.md` | deployed old demo only |
| C-12 | Phase 3/TDX tourism 與 Portfolio mini 尚未實作。 | n/a | README planned label；tree 無 `frontend-mini/` | planned/proposed |

## 11. 本 ledger 的限制

- 未驗證任何 live URL 可用性，也未向 remote provider 查詢；deployment 判讀只採現有 repo/report 證據。
- 未重跑 tests/build；測試數字一律標示 observed-via-report。
- 未宣稱 runtime `.env` 已採 600 秒。
- 未把 Phase 3、TDX、景點／餐廳／地圖、Portfolio integration、`frontend-mini/` 或 mini contract 當成現有功能。
- `implemented` 只代表 `fc2e37d` source tree 存在，不自動推導 accepted、merged、pushed 或 deployed。

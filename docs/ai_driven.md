# AI Driven 開發流程

本專案的 AI Driven 只指向開發流程:以多 agent 分層協作方式完成需求拆解、任務派發、實作與驗收。
本版本產品執行期不呼叫任何 LLM。行前建議由後端規則式摘要與 `backend/app/services/weather.py` 的 `advice_hint` 共同產生。
摘要服務位置:`backend/app/services/ai_summary.py`。

## 分層協作

- **管理層**:將使用者目標拆成可驗收任務,定義任務卡、保護規則、驗收條件與交付順序。
- **編碼層**:依任務卡在指定範圍內修改程式或文檔,執行測試,提交 Task Report。
- **驗收層**:以獨立視角檢查結果是否符合任務卡、測試與實際畫面,產出 Verification Report。

## 任務卡驅動

每次變更先有明確任務卡,內容包含目標、範圍、禁止修改區域、驗收條件與報告位置。這讓個人專案也能保留接近團隊協作的節奏:需求可追溯、變更可審查、驗收可重現。

## 原始紀錄

脫敏後的任務卡、開發日誌與驗收軌跡保留於 [`docs/dev-process/`](dev-process/)。
這些紀錄呈現從決策、實作到驗收的分層協作鏈路,也對應 `docs/git_workflow.md` 中的 PR、CI 與 review 流程。

"""AI trip summary service.

Two modes, chosen at runtime by whether GEMINI_API_KEY is set:
  1. Real: call Gemini via the standard google-genai SDK (NOT the local Engine).
  2. Degraded: a deterministic rule-based summary, so the feature never hard-fails
     and the app is fully runnable with zero credentials.

Data governance (see docs/ai_driven.md): only public weather/POI data is sent to
Gemini — never any PII. Free tier is for development/demo; production would use a
paid/enterprise route where content is not used for training.
"""

from __future__ import annotations

from app.core.config import Settings
from app.schemas.weather import DailyForecast, Town
from app.services.weather import pick_target_day

_SYSTEM_PROMPT = (
    "你是旅遊行前助理。根據以下公開天氣預報,用繁體中文寫一段 2-3 句、"
    "友善且具體的行前建議,包含穿著或攜帶物品提醒。不要編造預報以外的資訊。"
)


def _rule_based_summary(town: Town, day: DailyForecast) -> str:
    parts = [f"{town.city}{town.name}在 {_display_date(day.date)} "]
    if day.weather:
        parts.append(f"預報為「{day.weather}」,")
    if day.temp_low_c is not None and day.temp_high_c is not None:
        parts.append(f"氣溫約 {day.temp_low_c:.0f}–{day.temp_high_c:.0f}°C,")
    if day.max_pop_percent is not None:
        parts.append(f"降雨機率最高 {day.max_pop_percent}%。")
    parts.append(day.advice_hint or "")
    return "".join(parts).strip()


def _display_date(value: str) -> str:
    parts = value.split("-")
    if len(parts) == 3:
        return f"{int(parts[1])}/{int(parts[2])}"
    return value


class AiSummaryService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled_real(self) -> bool:
        return bool(self._settings.gemini_api_key.strip())

    def summarize(
        self,
        town: Town,
        days: list[DailyForecast],
        target_date: str,
    ) -> tuple[str, str]:
        """Return (summary_text, mode) where mode is 'gemini' or 'rule-based'."""
        if not days:
            return ("目前沒有可用的預報資料。", "rule-based")
        focused_days = pick_target_day(days, target_date)
        primary = focused_days[0]
        if not self.enabled_real:
            return (_rule_based_summary(town, primary), "rule-based")
        try:
            return (self._gemini_summary(town, focused_days), "gemini")
        except Exception:
            # Graceful degrade: never let the AI block the weather result.
            return (_rule_based_summary(town, primary), "rule-based-fallback")

    def _gemini_summary(self, town: Town, days: list[DailyForecast]) -> str:
        from google import genai  # imported lazily; optional dependency

        client = genai.Client(api_key=self._settings.gemini_api_key)
        facts = "\n".join(
            f"- {d.date}: {d.weather}, {d.temp_low_c}-{d.temp_high_c}°C, "
            f"降雨機率 {d.max_pop_percent}%"
            for d in days
        )
        prompt = f"{_SYSTEM_PROMPT}\n\n地點:{town.city}{town.name}\n預報:\n{facts}"
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return (response.text or "").strip() or _rule_based_summary(town, days[0])

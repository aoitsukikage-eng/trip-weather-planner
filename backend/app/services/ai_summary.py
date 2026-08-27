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

_SYSTEM_PROMPT_ZH = (
    "你是旅遊行前助理。根據以下公開天氣預報,用繁體中文寫一段 2-3 句、"
    "友善且具體的行前建議,包含穿著或攜帶物品提醒。不要編造預報以外的資訊。"
)

_SYSTEM_PROMPT_EN = (
    "You are a trip preparation assistant. Based on the public weather forecast below, "
    "write a friendly and concise 2-3 sentence travel recommendation in English, "
    "including tips on clothing or items to bring. Do not invent information beyond the forecast."
)

_SYSTEM_PROMPT_JA = (
    "あなたは旅行の事前準備アシスタントです。以下の公開天気予報に基づき、"
    "服装や持参品のアドバイスを含む、親切で具体的な旅行のアドバイスを日本語で2〜3文で作成してください。"
    "予報以外の情報を捏造しないでください。"
)


def _rule_based_summary(town: Town, day: DailyForecast, lang: str = "zh") -> str:
    if lang == "en":
        town_name = town.name_en or town.name
        city_name = town.city_en or town.city
        parts = [f"The forecast for {town_name}, {city_name} on {_display_date(day.date)} "]
        if day.weather:
            parts.append(f'is "{day.weather}", ')
        if day.temp_low_c is not None and day.temp_high_c is not None:
            parts.append(
                f"with temperatures around {day.temp_low_c:.0f}–{day.temp_high_c:.0f}°C "
            )
        if day.max_pop_percent is not None:
            parts.append(f"and a peak precipitation chance of {day.max_pop_percent}%. ")
        if day.advice_hint:
            parts.append(day.advice_hint)
        return "".join(parts).strip()

    if lang == "ja":
        parts = [f"{_display_date(day.date)}の{town.city}{town.name}の天気予報は"]
        if day.weather:
            parts.append(f"「{day.weather}」で、")
        if day.temp_low_c is not None and day.temp_high_c is not None:
            parts.append(
                f"気温は約{day.temp_low_c:.0f}〜{day.temp_high_c:.0f}℃、"
            )
        if day.max_pop_percent is not None:
            parts.append(f"最高降水確率は{day.max_pop_percent}%です。")
        if day.advice_hint:
            parts.append(day.advice_hint)
        return "".join(parts).strip()

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
        lang: str = "zh",
    ) -> tuple[str, str]:
        """Return (summary_text, mode) where mode is 'gemini' or 'rule-based'."""
        if not days:
            no_data_msg = (
                "No forecast data currently available."
                if lang == "en"
                else "現在利用可能な予報データがありません。"
                if lang == "ja"
                else "目前沒有可用的預報資料。"
            )
            return (no_data_msg, "rule-based")
        focused_days = pick_target_day(days, target_date)
        primary = focused_days[0]
        if not self.enabled_real:
            return (_rule_based_summary(town, primary, lang=lang), "rule-based")
        try:
            return (self._gemini_summary(town, focused_days, lang=lang), "gemini")
        except Exception:
            # Graceful degrade: never let the AI block the weather result.
            return (_rule_based_summary(town, primary, lang=lang), "rule-based-fallback")

    def _gemini_summary(
        self, town: Town, days: list[DailyForecast], lang: str = "zh"
    ) -> str:
        from google import genai  # imported lazily; optional dependency

        client = genai.Client(api_key=self._settings.gemini_api_key)
        system_prompt = (
            _SYSTEM_PROMPT_EN
            if lang == "en"
            else _SYSTEM_PROMPT_JA
            if lang == "ja"
            else _SYSTEM_PROMPT_ZH
        )
        facts = "\n".join(
            f"- {d.date}: {d.weather}, {d.temp_low_c}-{d.temp_high_c}°C, "
            f"chance of rain {d.max_pop_percent}%" if lang == "en"
            else f"- {d.date}: {d.weather}, {d.temp_low_c}-{d.temp_high_c}°C, "
            f"降水確率 {d.max_pop_percent}%" if lang == "ja"
            else f"- {d.date}: {d.weather}, {d.temp_low_c}-{d.temp_high_c}°C, "
            f"降雨機率 {d.max_pop_percent}%"
            for d in days
        )
        location_label = (
            f"Location: {town.name_en or town.name}, {town.city_en or town.city}"
            if lang == "en"
            else f"場所:{town.city}{town.name}" if lang == "ja"
            else f"地點:{town.city}{town.name}"
        )
        prompt = f"{system_prompt}\n\n{location_label}\nForecast:\n{facts}"
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return (response.text or "").strip() or _rule_based_summary(
            town, days[0], lang=lang
        )

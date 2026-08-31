"""Weather domain bilingual (zh/en) lookup tables and formatters.

This module acts as the backend single source of truth for all weather-related
bilingual text composition across the 8 required domains:
  1. weather_code_text
  2. advice_hint
  3. aqi_level
  4. uv_level
  5. warning_title_and_description
  6. moon_phase
  7. county_name
  8. town_name
"""

from __future__ import annotations

from typing import Literal

from app.i18n.town_names import TOWN_NAME_EN_BY_GEOCODE

LangType = Literal["zh", "en", "ja"]

# ---------------------------------------------------------------------------
# Domain 1: Weather Phenomena Codes (WxCode) - CWA Official Standard
# ---------------------------------------------------------------------------
WX_CODE_TO_TEXT: dict[str, dict[str, str]] = {
    "01": {"zh": "晴天", "en": "Clear", "ja": "晴れ"},
    "02": {"zh": "晴時多雲", "en": "Partly Cloudy", "ja": "晴れ時々くもり"},
    "03": {"zh": "多雲時晴", "en": "Partly Cloudy", "ja": "晴れ時々くもり"},
    "04": {"zh": "多雲", "en": "Cloudy", "ja": "くもり"},
    "05": {"zh": "多雲時陰", "en": "Mostly Cloudy", "ja": "くもり時々晴れ"},
    "06": {"zh": "陰時多雲", "en": "Mostly Cloudy", "ja": "くもり時々晴れ"},
    "07": {"zh": "陰天", "en": "Overcast", "ja": "くもり"},
    "08": {"zh": "短暫陣雨", "en": "Short Shower", "ja": "一時雨"},
    "09": {"zh": "短暫陣雨", "en": "Short Shower", "ja": "一時雨"},
    "10": {"zh": "短暫陣雨", "en": "Short Shower", "ja": "一時雨"},
    "11": {"zh": "陣雨", "en": "Showers", "ja": "にわか雨"},
    "12": {"zh": "短暫雨", "en": "Light Rain", "ja": "小雨"},
    "13": {"zh": "陣雨", "en": "Showers", "ja": "にわか雨"},
    "14": {"zh": "陣雨", "en": "Showers", "ja": "にわか雨"},
    "15": {"zh": "短暫陣雨或雷雨", "en": "Short Shower or Thunderstorm", "ja": "一時雨か雷雨"},
    "16": {"zh": "陣雨或雷雨", "en": "Showers or Thunderstorm", "ja": "にわか雨か雷雨"},
    "17": {"zh": "陣雨或雷雨", "en": "Showers or Thunderstorm", "ja": "にわか雨か雷雨"},
    "18": {"zh": "陣雨或雷雨", "en": "Showers or Thunderstorm", "ja": "にわか雨か雷雨"},
    "19": {"zh": "晴午後短暫雷陣雨", "en": "Afternoon Thunderstorms", "ja": "晴れ午後一時雷雨"},
    "20": {"zh": "多雲午後短暫雷陣雨", "en": "Afternoon Thunderstorms", "ja": "くもり午後一時雷雨"},
    "21": {"zh": "陣雨或雷雨", "en": "Showers or Thunderstorms", "ja": "にわか雨か雷雨"},
    "22": {"zh": "陣雨或雷雨", "en": "Showers or Thunderstorms", "ja": "にわか雨か雷雨"},
    "23": {"zh": "雨或雪", "en": "Rain or Snow", "ja": "雨か雪"},
    "24": {"zh": "晴有霧", "en": "Clear with Fog", "ja": "晴れ、霧を伴う"},
    "25": {"zh": "多雲有霧", "en": "Cloudy with Fog", "ja": "くもり、霧を伴う"},
    "26": {"zh": "陰有霧", "en": "Overcast with Fog", "ja": "くもり、霧を伴う"},
    "27": {"zh": "霧", "en": "Fog", "ja": "霧"},
    "28": {"zh": "霧", "en": "Fog", "ja": "霧"},
    "29": {"zh": "局霧", "en": "Local Fog", "ja": "所により霧"},
    "30": {"zh": "局霧", "en": "Local Fog", "ja": "所により霧"},
    "31": {"zh": "霾", "en": "Haze", "ja": "煙霧"},
    "32": {"zh": "霾", "en": "Haze", "ja": "煙霧"},
    "33": {"zh": "霾", "en": "Haze", "ja": "煙霧"},
    "34": {"zh": "颳風", "en": "Windy", "ja": "やや強い風"},
    "35": {"zh": "強風", "en": "Gale", "ja": "強風"},
    "36": {"zh": "烈風", "en": "Gale", "ja": "強風"},
    "37": {"zh": "暴風", "en": "Storm", "ja": "暴風"},
    "38": {"zh": "吹雪", "en": "Blowing Snow", "ja": "地吹雪"},
    "39": {"zh": "豪雨", "en": "Heavy Rain", "ja": "大雨"},
    "40": {"zh": "大豪雨", "en": "Torrential Rain", "ja": "非常に激しい雨"},
    "41": {"zh": "超大豪雨", "en": "Extreme Heavy Rain", "ja": "猛烈な雨"},
    "42": {"zh": "積雪", "en": "Snow Cover", "ja": "積雪"},
}

# Fallback text mappings if code is missing or unmapped
WEATHER_TEXT_FALLBACK_EN: dict[str, str] = {
    "晴天": "Clear",
    "晴時多雲": "Partly Cloudy",
    "多雲時晴": "Partly Cloudy",
    "多雲": "Cloudy",
    "多雲時陰": "Mostly Cloudy",
    "陰時多雲": "Mostly Cloudy",
    "陰天": "Overcast",
    "陰時多雲短暫雨": "Mostly Cloudy with Light Rain",
    "短暫陣雨": "Short Shower",
    "短暫雨": "Light Rain",
    "陣雨": "Showers",
    "雨": "Rain",
    "雷陣雨": "Thunderstorm",
}


def get_weather_text(weather: str | None, weather_code: str | None, lang: str = "zh") -> str | None:
    if lang == "zh":
        if weather:
            return weather
        if weather_code:
            code_str = weather_code.zfill(2)
            if code_str in WX_CODE_TO_TEXT:
                return WX_CODE_TO_TEXT[code_str]["zh"]
        return weather

    if weather_code:
        code_str = weather_code.zfill(2)
        if code_str in WX_CODE_TO_TEXT:
            entry = WX_CODE_TO_TEXT[code_str]
            return entry.get(lang) or entry["zh"]

    if lang == "en" and weather and weather in WEATHER_TEXT_FALLBACK_EN:
        return WEATHER_TEXT_FALLBACK_EN[weather]

    return weather


# ---------------------------------------------------------------------------
# Domain 2: Advice Hint
# ---------------------------------------------------------------------------
ADVICE_HINT_MAP: dict[str, dict[str, str]] = {
    "rain_likely": {
        "zh": "降雨機率高,建議攜傘或準備室內備案。",
        "en": "Rain is likely. Bring an umbrella, or plan an indoor alternative.",
        "ja": (
            "雨が降りやすい一日です。折り畳み傘を持って、"
            "屋内で過ごせる場所も調べておきましょう。"
        ),
    },
    "rain_chance": {
        "zh": "可能會下雨,建議隨身帶把傘。",
        "en": "A chance of rain. Pack an umbrella just in case.",
        "ja": "雨の可能性があります。念のため折り畳み傘を持っておきましょう。",
    },
    "hot": {
        "zh": "高溫炎熱,注意防曬與補充水分。",
        "en": "A hot day ahead. Drink plenty of water and stay out of the midday sun.",
        "ja": (
            "厳しい暑さになりそうです。こまめに水分を補給し、"
            "日差しの強い時間帯は日陰で休みましょう。"
        ),
    },
    "cold": {
        "zh": "氣溫偏低,出門記得保暖。",
        "en": "A chilly day ahead. Dress in layers before you head out.",
        "ja": "冷え込む一日です。暖かい服装でお出かけください。",
    },
    "stable": {
        "zh": "天氣大致穩定,適合安排戶外行程。",
        "en": "Settled weather — a good day for outdoor plans.",
        "ja": "天気は穏やかで、お出かけ日和になりそうです。",
    },
}


def get_advice_hint_key(
    temp_high: float | None, temp_low: float | None, max_pop: int | None
) -> str:
    # Rain tiers follow the NWS probability-of-precipitation wording table:
    # 60-70% is "likely", 30-50% is "chance". Below 30% the day is settled and
    # "stable" can claim so without contradicting the precipitation figure
    # printed on the same card.
    if max_pop is not None and max_pop >= 60:
        return "rain_likely"
    if temp_high is not None and temp_high >= 33:
        return "hot"
    if temp_low is not None and temp_low <= 12:
        return "cold"
    if max_pop is not None and max_pop >= 30:
        return "rain_chance"
    return "stable"


def get_advice_hint(key: str, lang: str = "zh") -> str:
    entry = ADVICE_HINT_MAP.get(key, ADVICE_HINT_MAP["stable"])
    return entry.get(lang) or entry["zh"]


# ---------------------------------------------------------------------------
# Domain 3: Air Quality Index (AQI) Categories
# ---------------------------------------------------------------------------
AQI_LEVEL_MAP: dict[str, dict[str, str]] = {
    "良好": {"zh": "良好", "en": "Good", "ja": "良好"},
    "普通": {"zh": "普通", "en": "Moderate", "ja": "普通"},
    "對敏感族群不健康": {
        "zh": "對敏感族群不健康",
        "en": "Unhealthy for Sensitive Groups",
        "ja": "敏感なグループには健康に有害",
    },
    "對所有族群不健康": {"zh": "對所有族群不健康", "en": "Unhealthy", "ja": "健康に有害"},
    "非常不健康": {"zh": "非常不健康", "en": "Very Unhealthy", "ja": "極めて健康に有害"},
    "危害": {"zh": "危害", "en": "Hazardous", "ja": "危険"},
    # Fallback / demo strings from MOENV API & mock data
    "資料不足": {"zh": "資料不足", "en": "Insufficient Data", "ja": "データ不足"},
    "示範測站": {"zh": "示範測站", "en": "Demo Station", "ja": "デモ観測局"},
    "目前空氣品質（示範）": {
        "zh": "目前空氣品質（示範）",
        "en": "Current Air Quality (Demo)",
        "ja": "現在の空気質（デモ）",
    },
    "目前空氣品質": {"zh": "目前空氣品質", "en": "Current Air Quality", "ja": "現在の空気質"},
}


def get_aqi_level_text(level: str | None, lang: str = "zh") -> str | None:
    if level is None:
        return None
    entry = AQI_LEVEL_MAP.get(level)
    return (entry.get(lang) or entry["zh"]) if entry else level


def get_aqi_level_code(value: int | float | None) -> str | None:
    if value is None:
        return None
    if value <= 50:
        return "good"
    if value <= 100:
        return "moderate"
    if value <= 150:
        return "unhealthy_sensitive"
    if value <= 200:
        return "unhealthy"
    if value <= 300:
        return "very_unhealthy"
    return "hazardous"


def get_aqi_source_label(label: str, lang: str = "zh") -> str:
    entry = AQI_LEVEL_MAP.get(label)
    if entry:
        return entry.get(lang) or entry["zh"]
    if "示範" in label:
        if lang == "en":
            return "Current Air Quality (Demo)"
        if lang == "ja":
            return "現在の空気質（デモ）"
        return "目前空氣品質（示範）"
    if lang == "en":
        return "Current Air Quality"
    if lang == "ja":
        return "現在の空気質"
    return "目前空氣品質"


# ---------------------------------------------------------------------------
# Domain 4: UV Index Level
# ---------------------------------------------------------------------------
UV_LEVEL_MAP: dict[str, dict[str, str]] = {
    "低": {"zh": "低", "en": "Low", "ja": "弱い"},
    "中": {"zh": "中", "en": "Moderate", "ja": "中程度"},
    "高": {"zh": "高", "en": "High", "ja": "強い"},
    "過量": {"zh": "過量", "en": "Very High", "ja": "非常に強い"},
    "危險": {"zh": "危險", "en": "Extreme", "ja": "極めて強い"},
}

UV_LABEL_MAP: dict[str, dict[str, str]] = {
    "目前紫外線": {"zh": "目前紫外線", "en": "Current UV Index", "ja": "現在の紫外線インデックス"},
    "目前紫外線僅供參考": {
        "zh": "目前紫外線僅供參考",
        "en": "Current UV Index (for reference only)",
        "ja": "現在の紫外線インデックス（参考値）",
    },
}


def get_uv_level_text(level: str | None, lang: str = "zh") -> str | None:
    if level is None:
        return None
    entry = UV_LEVEL_MAP.get(level)
    return (entry.get(lang) or entry["zh"]) if entry else level


def get_uv_level_code(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 2:
        return "low"
    if value <= 5:
        return "moderate"
    if value <= 7:
        return "high"
    if value <= 10:
        return "very_high"
    return "extreme"


def get_uv_source_label(label: str, lang: str = "zh") -> str:
    entry = UV_LABEL_MAP.get(label)
    return (entry.get(lang) or entry["zh"]) if entry else label


# ---------------------------------------------------------------------------
# Domain 5: Weather Warning Title & Description Template
# ---------------------------------------------------------------------------
WARNING_TITLE_MAP: dict[str, dict[str, str]] = {
    "豪雨特報": {"zh": "豪雨特報", "en": "Extremely Heavy Rain Advisory", "ja": "大雨警報"},
    "大雨特報": {"zh": "大雨特報", "en": "Heavy Rain Advisory", "ja": "大雨注意報"},
    "陸上強風特報": {"zh": "陸上強風特報", "en": "Land Strong Wind Warning", "ja": "強風注意報"},
    "颱風警報": {"zh": "颱風警報", "en": "Typhoon Warning", "ja": "台風警報"},
}


def format_warning(
    title: str, county: str, lang: str = "zh"
) -> tuple[str, str]:
    """Return (translated_title, translated_description)."""
    county_en = get_county_name_text(county, lang="en")
    title_entry = WARNING_TITLE_MAP.get(title)
    if lang == "en":
        title_text = title_entry["en"] if title_entry else title
        desc_text = (
            f"{title_text} for {county_en}. Please stay tuned for the latest weather updates."
        )
    elif lang == "ja":
        title_text = title_entry.get("ja") if title_entry else title
        desc_text = f"{county}に{title_text}が発表されています。最新の気象情報にご注意ください。"
    else:
        title_text = title_entry["zh"] if title_entry else title
        desc_text = f"{county}{title_text}，請留意最新天氣資訊。"
    return title_text, desc_text


# ---------------------------------------------------------------------------
# Domain 6: Moon Phase Names
# ---------------------------------------------------------------------------
MOON_PHASE_MAP: dict[str, dict[str, str]] = {
    "新月": {"zh": "新月", "en": "New Moon", "ja": "新月"},
    "眉月": {"zh": "眉月", "en": "Waxing Crescent", "ja": "三日月"},
    "上弦月": {"zh": "上弦月", "en": "First Quarter", "ja": "上弦の月"},
    "盈凸月": {"zh": "盈凸月", "en": "Waxing Gibbous", "ja": "十三夜月"},
    "滿月": {"zh": "滿月", "en": "Full Moon", "ja": "満月"},
    "虧凸月": {"zh": "虧凸月", "en": "Waning Gibbous", "ja": "寝待月"},
    "下弦月": {"zh": "下弦月", "en": "Last Quarter", "ja": "下弦の月"},
    "殘月": {"zh": "殘月", "en": "Waning Crescent", "ja": "有明の月"},
}


def get_moon_phase_text(phase: str, lang: str = "zh") -> str:
    entry = MOON_PHASE_MAP.get(phase)
    return (entry.get(lang) or entry["zh"]) if entry else phase


# ---------------------------------------------------------------------------
# Domain 7: County / City Standard Names (Taiwan Official English Names)
# ---------------------------------------------------------------------------
COUNTY_NAME_MAP: dict[str, dict[str, str]] = {
    "宜蘭縣": {"zh": "宜蘭縣", "en": "Yilan County"},
    "桃園市": {"zh": "桃園市", "en": "Taoyuan City"},
    "新竹縣": {"zh": "新竹縣", "en": "Hsinchu County"},
    "苗栗縣": {"zh": "苗栗縣", "en": "Miaoli County"},
    "彰化縣": {"zh": "彰化縣", "en": "Changhua County"},
    "南投縣": {"zh": "南投縣", "en": "Nantou County"},
    "雲林縣": {"zh": "雲林縣", "en": "Yunlin County"},
    "嘉義縣": {"zh": "嘉義縣", "en": "Chiayi County"},
    "屏東縣": {"zh": "屏東縣", "en": "Pingtung County"},
    "臺東縣": {"zh": "臺東縣", "en": "Taitung County"},
    "台東縣": {"zh": "臺東縣", "en": "Taitung County"},
    "花蓮縣": {"zh": "花蓮縣", "en": "Hualien County"},
    "澎湖縣": {"zh": "澎湖縣", "en": "Penghu County"},
    "基隆市": {"zh": "基隆市", "en": "Keelung City"},
    "新竹市": {"zh": "新竹市", "en": "Hsinchu City"},
    "嘉義市": {"zh": "嘉義市", "en": "Chiayi City"},
    "臺北市": {"zh": "臺北市", "en": "Taipei City"},
    "台北市": {"zh": "臺北市", "en": "Taipei City"},
    "高雄市": {"zh": "高雄市", "en": "Kaohsiung City"},
    "新北市": {"zh": "新北市", "en": "New Taipei City"},
    "臺中市": {"zh": "臺中市", "en": "Taichung City"},
    "台中市": {"zh": "臺中市", "en": "Taichung City"},
    "臺南市": {"zh": "臺南市", "en": "Tainan City"},
    "台南市": {"zh": "臺南市", "en": "Tainan City"},
    "連江縣": {"zh": "連江縣", "en": "Lienchiang County"},
    "金門縣": {"zh": "金門縣", "en": "Kinmen County"},
}


def get_county_name_text(county: str, lang: str = "zh") -> str:
    entry = COUNTY_NAME_MAP.get(county)
    return (entry.get(lang) or entry["zh"]) if entry else county


# ---------------------------------------------------------------------------
# Domain 8: Township Standard Names (Taiwan Official English Names)
# ---------------------------------------------------------------------------
TOWN_NAME_MAP: dict[str, dict[str, str]] = {
    # Key can be town code or town name
    "taipei-xinyi": {"zh": "信義區", "en": "Xinyi District"},
    "newtaipei-banqiao": {"zh": "板橋區", "en": "Banqiao District"},
    "keelung-ren-ai": {"zh": "仁愛區", "en": "Ren'ai District"},
    "taoyuan-taoyuan": {"zh": "桃園區", "en": "Taoyuan District"},
    "hsinchu-east": {"zh": "東區", "en": "East District"},
    "taichung-xitun": {"zh": "西屯區", "en": "Xitun District"},
    "nantou-yuchi": {"zh": "魚池鄉", "en": "Yuchi Township"},
    "chiayi-east": {"zh": "東區", "en": "East District"},
    "tainan-west-central": {"zh": "中西區", "en": "West Central District"},
    "kaohsiung-zuoying": {"zh": "左營區", "en": "Zuoying District"},
    "pingtung-hengchun": {"zh": "恆春鎮", "en": "Hengchun Township"},
    "yilan-yilan": {"zh": "宜蘭市", "en": "Yilan City"},
    "hualien-hualien": {"zh": "花蓮市", "en": "Hualien City"},
    "taitung-taitung": {"zh": "臺東市", "en": "Taitung City"},
    "penghu-magong": {"zh": "馬公市", "en": "Magong City"},
    "hsinchu-county-zhubei": {"zh": "竹北市", "en": "Zhubei City"},
    "miaoli-miaoli": {"zh": "苗栗市", "en": "Miaoli City"},
    "changhua-changhua": {"zh": "彰化市", "en": "Changhua City"},
    "yunlin-douliu": {"zh": "斗六市", "en": "Douliu City"},
    "chiayi-county-alishan": {"zh": "阿里山鄉", "en": "Alishan Township"},
    "kinmen-jincheng": {"zh": "金城鎮", "en": "Jincheng Township"},
    "lienchiang-nangan": {"zh": "南竿鄉", "en": "Nangan Township"},
}

TOWN_BY_NAME_MAP: dict[str, str] = {
    "信義區": "Xinyi District",
    "板橋區": "Banqiao District",
    "仁愛區": "Ren'ai District",
    "桃園區": "Taoyuan District",
    "西屯區": "Xitun District",
    "魚池鄉": "Yuchi Township",
    "中西區": "West Central District",
    "左營區": "Zuoying District",
    "恆春鎮": "Hengchun Township",
    "宜蘭市": "Yilan City",
    "花蓮市": "Hualien City",
    "臺東市": "Taitung City",
    "台東市": "Taitung City",
    "馬公市": "Magong City",
    "竹北市": "Zhubei City",
    "苗栗市": "Miaoli City",
    "彰化市": "Changhua City",
    "斗六市": "Douliu City",
    "阿里山鄉": "Alishan Township",
    "金城鎮": "Jincheng Township",
    "南竿鄉": "Nangan Township",
    "貢寮區": "Gongliao District",
}


def get_town_name_text(town_code: str, name_zh: str, lang: str = "zh") -> str:
    if lang == "en":
        if town_code.startswith("cwa-"):
            geocode = town_code[4:]
            if geocode in TOWN_NAME_EN_BY_GEOCODE:
                return TOWN_NAME_EN_BY_GEOCODE[geocode]
        if town_code in TOWN_NAME_MAP:
            return TOWN_NAME_MAP[town_code]["en"]
        if name_zh in TOWN_BY_NAME_MAP:
            return TOWN_BY_NAME_MAP[name_zh]
    return name_zh

"""Starter township registry (town -> city + centroid coordinates).

This is the app's current selectable subset. It spans all 22 counties/cities
with at least one representative township so both mock mode and live CWA mode
can stay on the same stable town codes during Phase 1.

The `city` field is what TDX's city-scoped Tourism API expects (Phase 2), and
the lat/lon centroid is used to radius-filter attractions down to the chosen
township — hence we advertise "attractions near the destination", not
"township-exclusive attractions".
"""

from __future__ import annotations

from app.schemas.weather import Town

# code: (name, city, lat, lon)
_TOWNS: dict[str, tuple[str, str, float, float]] = {
    "taipei-xinyi": ("信義區", "臺北市", 25.0330, 121.5654),
    "newtaipei-banqiao": ("板橋區", "新北市", 25.0143, 121.4677),
    "keelung-ren-ai": ("仁愛區", "基隆市", 25.1276, 121.7392),
    "taoyuan-taoyuan": ("桃園區", "桃園市", 24.9937, 121.3010),
    "hsinchu-east": ("東區", "新竹市", 24.8015, 120.9718),
    "taichung-xitun": ("西屯區", "臺中市", 24.1817, 120.6167),
    "nantou-yuchi": ("魚池鄉", "南投縣", 23.8960, 120.9380),  # Sun Moon Lake
    "chiayi-east": ("東區", "嘉義市", 23.4800, 120.4491),
    "tainan-west-central": ("中西區", "臺南市", 22.9924, 120.2043),
    "kaohsiung-zuoying": ("左營區", "高雄市", 22.6900, 120.2954),
    "pingtung-hengchun": ("恆春鎮", "屏東縣", 22.0021, 120.7469),  # Kenting gateway
    "yilan-yilan": ("宜蘭市", "宜蘭縣", 24.7570, 121.7530),
    "hualien-hualien": ("花蓮市", "花蓮縣", 23.9769, 121.6044),
    "taitung-taitung": ("臺東市", "臺東縣", 22.7583, 121.1444),
    "penghu-magong": ("馬公市", "澎湖縣", 23.5655, 119.5794),
    "hsinchu-county-zhubei": ("竹北市", "新竹縣", 24.8386, 121.0177),
    "miaoli-miaoli": ("苗栗市", "苗栗縣", 24.5602, 120.8214),
    "changhua-changhua": ("彰化市", "彰化縣", 24.0809, 120.5416),
    "yunlin-douliu": ("斗六市", "雲林縣", 23.7075, 120.5439),
    "chiayi-county-alishan": ("阿里山鄉", "嘉義縣", 23.5083, 120.8027),
    "kinmen-jincheng": ("金城鎮", "金門縣", 24.4166, 118.3171),
    "lienchiang-nangan": ("南竿鄉", "連江縣", 26.1520, 119.9500),
}


def all_towns() -> list[Town]:
    return [
        Town(code=code, name=name, city=city, lat=lat, lon=lon)
        for code, (name, city, lat, lon) in _TOWNS.items()
    ]


def get_town(code: str) -> Town | None:
    entry = _TOWNS.get(code)
    if entry is None:
        return None
    name, city, lat, lon = entry
    return Town(code=code, name=name, city=city, lat=lat, lon=lon)

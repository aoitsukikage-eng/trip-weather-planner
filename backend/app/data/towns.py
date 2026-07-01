"""Starter township registry (town -> city + centroid coordinates).

This is a representative subset covering popular travel destinations across
Taiwan, enough to drive Phase 1/2 demos. It is NOT the full 368-township list;
the full set can be loaded from CWA's location list or a data file later.

The `city` field is what TDX's city-scoped Tourism API expects (Phase 2), and
the lat/lon centroid is used to radius-filter attractions down to the chosen
township — hence we advertise "attractions near the destination", not
"township-exclusive attractions".
"""

from __future__ import annotations

from app.schemas.weather import Town

# code: (name, city, lat, lon)
_TOWNS: dict[str, tuple[str, str, float, float]] = {
    "taipei-zhongzheng": ("中正區", "臺北市", 25.0324, 121.5199),
    "taipei-xinyi": ("信義區", "臺北市", 25.0330, 121.5654),
    "taipei-datong": ("大同區", "臺北市", 25.0630, 121.5130),
    "newtaipei-banqiao": ("板橋區", "新北市", 25.0143, 121.4677),
    "newtaipei-tamsui": ("淡水區", "新北市", 25.1695, 121.4406),
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

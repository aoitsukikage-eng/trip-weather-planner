"""Versioned local town catalog plus backwards-compatible legacy aliases."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.i18n.weather_text import get_county_name_text, get_town_name_text
from app.schemas.weather import Town

_CATALOG_PATH = Path(__file__).with_name("cwa_towns_catalog.json")

# code: (name, city, lat, lon, canonical CWA geocode)
_LEGACY_TOWNS: dict[str, tuple[str, str, float, float, str]] = {
    "taipei-xinyi": ("信義區", "臺北市", 25.0330, 121.5654, "cwa-63000020"),
    "newtaipei-banqiao": ("板橋區", "新北市", 25.0143, 121.4677, "cwa-65000010"),
    "keelung-ren-ai": ("仁愛區", "基隆市", 25.1276, 121.7392, "cwa-10017040"),
    "taoyuan-taoyuan": ("桃園區", "桃園市", 24.9937, 121.3010, "cwa-68000010"),
    "hsinchu-east": ("東區", "新竹市", 24.8015, 120.9718, "cwa-10018010"),
    "taichung-xitun": ("西屯區", "臺中市", 24.1817, 120.6167, "cwa-66000060"),
    "nantou-yuchi": ("魚池鄉", "南投縣", 23.8960, 120.9380, "cwa-10008090"),
    "chiayi-east": ("東區", "嘉義市", 23.4800, 120.4491, "cwa-10020010"),
    "tainan-west-central": ("中西區", "臺南市", 22.9924, 120.2043, "cwa-67000370"),
    "kaohsiung-zuoying": ("左營區", "高雄市", 22.6900, 120.2954, "cwa-64000030"),
    "pingtung-hengchun": ("恆春鎮", "屏東縣", 22.0021, 120.7469, "cwa-10013040"),
    "yilan-yilan": ("宜蘭市", "宜蘭縣", 24.7570, 121.7530, "cwa-10002010"),
    "hualien-hualien": ("花蓮市", "花蓮縣", 23.9769, 121.6044, "cwa-10015010"),
    "taitung-taitung": ("臺東市", "臺東縣", 22.7583, 121.1444, "cwa-10014010"),
    "penghu-magong": ("馬公市", "澎湖縣", 23.5655, 119.5794, "cwa-10016010"),
    "hsinchu-county-zhubei": ("竹北市", "新竹縣", 24.8386, 121.0177, "cwa-10004010"),
    "miaoli-miaoli": ("苗栗市", "苗栗縣", 24.5602, 120.8217, "cwa-10005010"),
    "changhua-changhua": ("彰化市", "彰化縣", 24.0809, 120.5416, "cwa-10007010"),
    "yunlin-douliu": ("斗六市", "雲林縣", 23.7075, 120.5439, "cwa-10009010"),
    "chiayi-county-alishan": ("阿里山鄉", "嘉義縣", 23.5083, 120.8027, "cwa-10010180"),
    "kinmen-jincheng": ("金城鎮", "金門縣", 24.4166, 118.3171, "cwa-09020010"),
    "lienchiang-nangan": ("南竿鄉", "連江縣", 26.1520, 119.9500, "cwa-09007010"),
}


@lru_cache(maxsize=1)
def _catalog_by_code() -> dict[str, Town]:
    payload = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    towns = payload.get("towns")
    if payload.get("schema_version") != 1 or not isinstance(towns, list):
        raise RuntimeError("Invalid local CWA town catalog.")
    return {item["code"]: Town.model_validate(item) for item in towns}


@lru_cache(maxsize=1)
def _legacy_by_code() -> dict[str, Town]:
    return {
        code: Town(
            code=code,
            name=name,
            city=city,
            name_en=get_town_name_text(code, name, lang="en"),
            city_en=get_county_name_text(city, lang="en"),
            lat=lat,
            lon=lon,
        )
        for code, (name, city, lat, lon, _canonical) in _LEGACY_TOWNS.items()
    }


def all_towns() -> list[Town]:
    """Return canonical catalog towns in deterministic code order."""
    return list(_catalog_by_code().values())


def get_town(code: str) -> Town | None:
    """Resolve either public identity while retaining a legacy alias's payload."""
    return _legacy_by_code().get(code) or _catalog_by_code().get(code)


def canonical_code_for(code: str) -> str | None:
    """Return the local canonical CWA identity for a code without network I/O."""
    if code in _LEGACY_TOWNS:
        return _LEGACY_TOWNS[code][4]
    return code if code in _catalog_by_code() else None


def get_canonical_town(code: str) -> Town | None:
    canonical_code = canonical_code_for(code)
    return _catalog_by_code().get(canonical_code) if canonical_code else None

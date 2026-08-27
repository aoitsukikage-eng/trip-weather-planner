"""Generator for CWA UV and MOENV AQI official station English names.

Fetches station datasets from CWA (C-B0074-002, C-B0074-001) and MOENV (AQX_P_07),
applies official CWA capitalization normalization, includes MOENV fallback station
combination rules for siteids 203, 204, 311, 313, validates record quality,
and writes deterministic backend/app/i18n/station_names.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

# Ensure backend package can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.i18n.town_names import TOWN_NAME_EN_BY_GEOCODE  # noqa: E402
from app.i18n.weather_text import COUNTY_NAME_MAP  # noqa: E402

OUTPUT_PATH = BACKEND_DIR / "app" / "i18n" / "station_names.py"
ENV_PATH = BACKEND_DIR / ".env"

CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
MOENV_BASE_URL = "https://data.moenv.gov.tw/api/v2"


def normalize_cwa_name(name: str) -> str:
    """Normalize CWA StationNameEN capitalization.

    If a space-separated word is all-uppercase (word.isupper() is True),
    capitalize it (first character uppercase, rest lowercase).
    Otherwise, preserve the word unchanged.
    """
    words = name.split(" ")
    norm_words = []
    for word in words:
        if word.isupper():
            norm_words.append(word.capitalize())
        else:
            norm_words.append(word)
    return " ".join(norm_words)


def fetch_cwa_uv_stations(cwa_api_key: str, timeout: int = 30) -> dict[str, str]:
    """Fetch and normalize station English names from C-B0074-002 and C-B0074-001."""
    stations: dict[str, str] = {}
    datasets = ("C-B0074-002", "C-B0074-001")
    for dataset in datasets:
        url = f"{CWA_BASE_URL}/{dataset}"
        try:
            resp = httpx.get(url, params={"Authorization": cwa_api_key}, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as err:
            raise RuntimeError(f"Failed to fetch CWA dataset {dataset}: {err}") from err

        raw_stations = (
            data.get("records", {})
            .get("data", {})
            .get("stationStatus", {})
            .get("station", [])
        )
        for st in raw_stations:
            if not isinstance(st, dict):
                continue
            st_id = str(st.get("StationID") or "").strip()
            st_en = str(st.get("StationNameEN") or "").strip().replace("–", "-")
            if st_id and st_en:
                norm_en = normalize_cwa_name(st_en)
                if not norm_en.isascii():
                    raise ValueError(f"Non-ASCII CWA station EN name for {st_id}: {norm_en}")
                stations[st_id] = norm_en

    # Verify coverage of current O-A0005-001 UV stations
    url_uv = f"{CWA_BASE_URL}/O-A0005-001"
    try:
        resp_uv = httpx.get(url_uv, params={"Authorization": cwa_api_key}, timeout=timeout)
        resp_uv.raise_for_status()
        data_uv = resp_uv.json()
    except Exception as err:
        raise RuntimeError(f"Failed to fetch CWA dataset O-A0005-001: {err}") from err

    locations = (
        data_uv.get("records", {})
        .get("weatherElement", {})
        .get("location", [])
    )
    current_uv_ids = [
        str(loc.get("StationID")).strip()
        for loc in locations
        if isinstance(loc, dict) and loc.get("StationID")
    ]
    missing = [st_id for st_id in current_uv_ids if st_id not in stations]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} active UV stations in CWA tables: {missing}")

    return stations


def build_moenv_fallbacks() -> dict[str, str]:
    """Build official combined English names for 4 MOENV stations missing siteengname."""
    fallbacks_info = {
        "203": ("南投縣", "10008070"),  # Lugu Township -> Nantou (Lugu Township)
        "204": ("屏東縣", "10013220"),  # Liuqiu Township -> Pingtung (Liuqiu Township)
        "311": ("新北市", "65000070"),  # Shulin District -> New Taipei (Shulin District)
        "313": ("屏東縣", "10013250"),  # Fangshan Township -> Pingtung (Fangshan Township)
    }
    result = {}
    for siteid, (city, geocode) in fallbacks_info.items():
        city_en = (
            COUNTY_NAME_MAP[city]["en"]
            .replace(" County", "")
            .replace(" City", "")
        )
        town_en = TOWN_NAME_EN_BY_GEOCODE[geocode]
        result[siteid] = f"{city_en} ({town_en})"
    return result


def fetch_moenv_aqi_stations(moenv_api_key: str, timeout: int = 30) -> dict[str, str]:
    """Fetch AQX_P_07 station metadata and combine with 4 fallback siteids."""
    url = f"{MOENV_BASE_URL}/AQX_P_07"
    try:
        resp = httpx.get(url, params={"api_key": moenv_api_key}, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as err:
        raise RuntimeError(f"Failed to fetch MOENV AQX_P_07: {err}") from err

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("records", [])
    else:
        records = []

    stations: dict[str, str] = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        siteid = str(row.get("siteid") or "").strip()
        siteengname = str(row.get("siteengname") or "").strip()
        if siteid and siteengname:
            if not siteengname.isascii():
                raise ValueError(f"Non-ASCII MOENV siteengname for {siteid}: {siteengname}")
            # MOENV siteengname case MUST NOT be modified
            stations[siteid] = siteengname

    # Combine the 4 fallback stations
    fallbacks = build_moenv_fallbacks()
    for siteid, en_name in fallbacks.items():
        stations[siteid] = en_name

    # Validate against current aqx_p_432 live siteids
    url_432 = f"{MOENV_BASE_URL}/aqx_p_432"
    try:
        resp_432 = httpx.get(url_432, params={"api_key": moenv_api_key}, timeout=timeout)
        resp_432.raise_for_status()
        payload_432 = resp_432.json()
    except Exception as err:
        raise RuntimeError(f"Failed to fetch MOENV aqx_p_432: {err}") from err

    records_432 = payload_432 if isinstance(payload_432, list) else payload_432.get("records", [])
    siteids_432 = set(
        str(row.get("siteid")).strip()
        for row in records_432
        if isinstance(row, dict) and row.get("siteid")
    )
    missing_432 = siteids_432 - set(stations.keys())
    if missing_432:
        raise RuntimeError(f"Missing {len(missing_432)} siteids from aqx_p_432: {missing_432}")

    return stations


def generate_station_names_module(
    uv_stations: dict[str, str], aqi_stations: dict[str, str], output_path: Path
) -> None:
    """Write deterministic station_names.py sorted by station key."""
    lines = [
        '"""Official station English names mapping for UV and AQI datasets.',
        "",
        "Data Source URLs:",
        "  CWA: https://opendata.cwa.gov.tw/api/v1/rest/datastore/C-B0074-002",
        "       https://opendata.cwa.gov.tw/api/v1/rest/datastore/C-B0074-001",
        "  MOENV: https://data.moenv.gov.tw/api/v2/AQX_P_07",
        "Generator Script: backend/scripts/generate_station_names.py",
        "Generated Date: 2026-08-27",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "UV_STATION_NAME_EN_BY_ID: dict[str, str] = {",
    ]

    for st_id in sorted(uv_stations.keys()):
        en_name = uv_stations[st_id]
        lines.append(f'    "{st_id}": "{en_name}",')

    lines.extend([
        "}",
        "",
        "AQI_STATION_NAME_EN_BY_ID: dict[str, str] = {",
    ])

    for siteid in sorted(aqi_stations.keys()):
        en_name = aqi_stations[siteid]
        lines.append(f'    "{siteid}": "{en_name}",')

    lines.extend([
        "}",
        "",
        "",
        "def get_uv_station_name_text(",
        '    station_id: str | None, name_zh: str, lang: str = "zh"',
        ") -> str:",
        '    """Get UV station name for the target language.',
        "",
        "    If lang is 'en', looks up the station_id in UV_STATION_NAME_EN_BY_ID.",
        "    Falls back to name_zh if not found or when lang is 'zh'.",
        '    """',
        '    if lang == "en" and station_id and station_id in UV_STATION_NAME_EN_BY_ID:',
        "        return UV_STATION_NAME_EN_BY_ID[station_id]",
        "    return name_zh",
        "",
        "",
        "def get_aqi_station_name_text(",
        '    site_id: str | None, name_zh: str, lang: str = "zh"',
        ") -> str:",
        '    """Get AQI station name for the target language.',
        "",
        "    If lang is 'en', looks up the site_id in AQI_STATION_NAME_EN_BY_ID.",
        "    Falls back to name_zh if not found or when lang is 'zh'.",
        '    """',
        '    if lang == "en" and site_id and site_id in AQI_STATION_NAME_EN_BY_ID:',
        "        return AQI_STATION_NAME_EN_BY_ID[site_id]",
        "    return name_zh",
        "",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = Settings(_env_file=ENV_PATH)
    if not settings.cwa_api_key:
        raise RuntimeError("CWA_API_KEY is missing in environment / .env file")
    if not settings.moenv_api_key:
        raise RuntimeError("MOENV_API_KEY is missing in environment / .env file")

    print("Fetching CWA UV station names...")
    uv_stations = fetch_cwa_uv_stations(settings.cwa_api_key)
    print(f"Collected {len(uv_stations)} CWA UV stations.")

    print("Fetching MOENV AQI station names...")
    aqi_stations = fetch_moenv_aqi_stations(settings.moenv_api_key)
    print(f"Collected {len(aqi_stations)} MOENV AQI stations.")

    print(f"Generating {OUTPUT_PATH}...")
    generate_station_names_module(uv_stations, aqi_stations, OUTPUT_PATH)
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

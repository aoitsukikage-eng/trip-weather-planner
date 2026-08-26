"""Generator for Taiwan official 368 township English names from MOI KML dataset.

Downloads TOWN_MOI.kml to /tmp, parses TOWNCODE and TOWNENG attributes,
validates exact 368 records, and writes deterministic backend/app/i18n/town_names.py.
"""

from __future__ import annotations

import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

KML_URL = "https://www.post.gov.tw/post/download/TOWN_MOI.kml"
TMP_KML_PATH = Path("/tmp/TOWN_MOI.kml")
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "app" / "i18n" / "town_names.py"
EXPECTED_COUNT = 368


def download_kml(target_path: Path, timeout: int = 30) -> None:
    """Download KML dataset to temporary location with timeout."""
    req = urllib.request.Request(KML_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            target_path.write_bytes(data)
    except Exception as err:
        raise RuntimeError(f"Failed to download {KML_URL}: {err}") from err


def parse_town_names(kml_path: Path) -> dict[str, str]:
    """Parse TOWNCODE and TOWNENG from KML Placemark elements."""
    records: dict[str, str] = {}
    try:
        context = ET.iterparse(kml_path, events=("end",))
        for _, elem in context:
            if elem.tag.endswith("Placemark"):
                record: dict[str, str] = {}
                for child in elem.iter():
                    if child.tag.endswith("SimpleData"):
                        name = child.attrib.get("name")
                        text = child.text
                        if name and text:
                            record[name] = text.strip()
                code = record.get("TOWNCODE", "")
                eng = record.get("TOWNENG", "")
                if code and eng:
                    if len(code) != 8 or not code.isdigit():
                        raise ValueError(f"Invalid TOWNCODE format: {code}")
                    if not eng.isascii():
                        raise ValueError(f"Non-ASCII TOWNENG for geocode {code}: {eng}")
                    records[code] = eng
                elem.clear()
    except Exception as err:
        raise RuntimeError(f"Failed to parse KML {kml_path}: {err}") from err

    if len(records) != EXPECTED_COUNT:
        raise RuntimeError(
            f"Record count anomaly: expected {EXPECTED_COUNT}, got {len(records)}"
        )

    return records


def generate_town_names_module(records: dict[str, str], output_path: Path) -> None:
    """Write deterministic town_names.py sorted by geocode key."""
    lines = [
        '"""Taiwan official township English names by 8-digit MOI TOWNCODE geocode.',
        "",
        f"Data Source URL: {KML_URL}",
        "Generator Script: backend/scripts/generate_town_names.py",
        "Generated Date: 2026-08-27",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "TOWN_NAME_EN_BY_GEOCODE: dict[str, str] = {",
    ]

    for code in sorted(records.keys()):
        eng = records[code]
        lines.append(f'    "{code}": "{eng}",')

    lines.append("}")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print(f"Downloading KML from {KML_URL}...")
    download_kml(TMP_KML_PATH)

    print(f"Parsing town names from {TMP_KML_PATH}...")
    records = parse_town_names(TMP_KML_PATH)

    print(f"Generating {OUTPUT_PATH}...")
    generate_town_names_module(records, OUTPUT_PATH)
    print(f"Successfully generated {OUTPUT_PATH} with {len(records)} records.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

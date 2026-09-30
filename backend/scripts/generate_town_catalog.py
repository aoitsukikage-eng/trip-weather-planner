"""Build the versioned local CWA town catalog from an explicit input source.

This script is deliberately an offline build step: the application never calls
the source URL while serving a request.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_SOURCE_URL = (
    "https://twp-backend.purplewave-91ee1594.southeastasia.azurecontainerapps.io/"
    "api/towns?lang=zh"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "app/data/cwa_towns_catalog.json"
CODE_PATTERN = re.compile(r"^cwa-[0-9]+$")
REQUIRED_FIELDS = ("code", "name", "city", "name_en", "city_en", "lat", "lon")
MINIMUM_TOWNS = 368
EXPECTED_CITY_COUNT = 22


class CatalogError(ValueError):
    """An input payload cannot safely become the runtime catalog."""


def _read_source(source_url: str, timeout: float) -> object:
    request = Request(source_url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            if response.status != 200:
                raise CatalogError(f"Source returned HTTP {response.status}.")
            raw = response.read()
    except HTTPError as exc:
        raise CatalogError(f"Source returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise CatalogError(f"Could not reach source: {exc.reason}.") from exc
    except TimeoutError as exc:
        raise CatalogError("Source request timed out.") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CatalogError("Source response was not valid JSON.") from exc


def _read_input(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CatalogError(f"Could not read input file: {exc}.") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError("Input file was not valid JSON.") from exc


def _extract_towns(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise CatalogError("Catalog envelope must be a JSON object.")
    if payload.get("success") is False:
        raise CatalogError("Source envelope reported success=false.")
    towns = payload.get("data", payload.get("towns"))
    if not isinstance(towns, list):
        raise CatalogError("Catalog envelope must contain a data or towns list.")
    if not all(isinstance(town, dict) for town in towns):
        raise CatalogError("Catalog towns must all be JSON objects.")
    return towns


def validate_towns(towns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return normalized towns after enforcing the runtime catalog invariants."""
    codes: set[str] = set()
    cities: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(towns):
        missing = [field for field in REQUIRED_FIELDS if not raw.get(field)]
        if missing:
            raise CatalogError(f"Town {index} is missing required fields: {missing}.")
        code = raw["code"]
        if not isinstance(code, str) or not CODE_PATTERN.fullmatch(code):
            raise CatalogError(f"Town {index} has invalid canonical code: {code!r}.")
        if code in codes:
            raise CatalogError(f"Duplicate canonical code: {code}.")
        try:
            lat = float(raw["lat"])
            lon = float(raw["lon"])
        except (TypeError, ValueError) as exc:
            raise CatalogError(f"Town {code} has invalid coordinates.") from exc
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise CatalogError(f"Town {code} has out-of-range coordinates.")
        town = {
            "code": code,
            "name": str(raw["name"]).strip(),
            "city": str(raw["city"]).strip(),
            "name_en": str(raw["name_en"]).strip(),
            "city_en": str(raw["city_en"]).strip(),
            "lat": lat,
            "lon": lon,
        }
        if not all(town[field] for field in ("name", "city", "name_en", "city_en")):
            raise CatalogError(f"Town {code} has empty required text.")
        codes.add(code)
        cities.add(town["city"])
        normalized.append(town)
    if len(normalized) < MINIMUM_TOWNS:
        raise CatalogError(
            f"Catalog has {len(normalized)} towns; expected at least {MINIMUM_TOWNS}."
        )
    if len(cities) != EXPECTED_CITY_COUNT:
        raise CatalogError(f"Catalog has {len(cities)} cities; expected {EXPECTED_CITY_COUNT}.")
    return sorted(normalized, key=lambda town: town["code"])


def build_catalog(payload: object, source_url: str) -> dict[str, object]:
    towns = validate_towns(_extract_towns(payload))
    return {"schema_version": 1, "source_url": source_url, "towns": towns}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    source.add_argument("--input", type=Path, help="Previously downloaded JSON envelope.")
    parser.add_argument(
        "--source-label",
        help="Provenance URL to record when generating from --input.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    source_url = args.source_label or args.source_url
    try:
        payload = (
            _read_input(args.input)
            if args.input
            else _read_source(args.source_url, args.timeout)
        )
        catalog = build_catalog(payload, source_url)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except CatalogError as exc:
        print(f"Catalog generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

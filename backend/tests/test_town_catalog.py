"""Regression tests for the versioned, request-independent town catalog."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.data.towns import (
    _LEGACY_TOWNS,
    all_towns,
    canonical_code_for,
    get_canonical_town,
    get_town,
)


def _generator_module():
    path = Path(__file__).resolve().parents[1] / "scripts/generate_town_catalog.py"
    spec = importlib.util.spec_from_file_location("generate_town_catalog", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_catalog_has_valid_canonical_records_for_all_22_cities():
    towns = all_towns()
    assert len(towns) >= 368
    assert len({town.city for town in towns}) == 22
    assert len({town.code for town in towns}) == len(towns)
    for town in towns:
        assert town.code.startswith("cwa-")
        assert town.name and town.city and town.name_en and town.city_en
        assert -90 <= town.lat <= 90
        assert -180 <= town.lon <= 180


def test_generator_validates_the_checked_in_catalog():
    generator = _generator_module()
    payload = {"success": True, "data": [town.model_dump() for town in all_towns()]}
    catalog = generator.build_catalog(payload, "https://example.invalid/towns")
    assert catalog["schema_version"] == 1
    assert len(catalog["towns"]) >= 368


def test_all_legacy_aliases_preserve_their_public_identity_and_map_to_cwa():
    assert len(_LEGACY_TOWNS) == 22
    for alias, (name, city, _lat, _lon, canonical_code) in _LEGACY_TOWNS.items():
        legacy = get_town(alias)
        canonical = get_canonical_town(alias)
        assert legacy is not None and canonical is not None
        assert legacy.code == alias
        assert (legacy.name, legacy.city) == (name, city)
        assert canonical_code_for(alias) == canonical_code
        assert canonical.code == canonical_code
        assert (canonical.name, canonical.city) == (name, city)


def test_widget_aliases_have_canonical_identities():
    for alias in (
        "taipei-xinyi",
        "hualien-hualien",
        "kaohsiung-zuoying",
        "taitung-taitung",
    ):
        canonical = get_canonical_town(alias)
        assert canonical is not None
        assert canonical.code.startswith("cwa-")

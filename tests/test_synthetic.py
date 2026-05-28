# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests against synthetic Samsung Health export."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.exporters import export_to_solid
from src.loader import enrich_row_with_json, load_export
from src.normalizer import ms_to_aware_datetime, normalize_export
from src.rdf_transformer import (
    TransformOptions,
    count_clinical_triples,
    merge_graphs,
    transform_export,
)
from src.utils import (
    DEFAULT_EXPORT_DIR,
    DEFAULT_TEMPLATE_PATH,
    data_type_from_filename,
    resolve_export_root,
)

SYNTHETIC = ROOT / "data" / "synthetic_samsung_export"
REAL_EXPORT = ROOT / "20250221_SamsungHealth"


@pytest.fixture(scope="module")
def normalized():
    if not SYNTHETIC.is_dir():
        pytest.skip("Run scripts/generate_synthetic_export.py first")
    loaded = load_export(SYNTHETIC)
    return normalize_export(loaded)


def test_synthetic_folder_exists():
    assert SYNTHETIC.is_dir(), "Generate synthetic export first"


def test_resolve_real_samsung_export_root():
    if not REAL_EXPORT.is_dir():
        pytest.skip("Real export not present")
    root = resolve_export_root(REAL_EXPORT)
    assert list(root.glob("*.csv"))
    assert (root / "jsons").is_dir()


def test_load_real_export_has_weight_and_sleep():
    if not REAL_EXPORT.is_dir():
        pytest.skip("Real export not present")
    loaded = load_export(REAL_EXPORT)
    types = loaded["data_types"]
    assert "com.samsung.health.weight" in types
    assert "com.samsung.shealth.sleep" in types
    assert loaded["dataframes_count"] >= 40


def test_load_csv_count(normalized):
    assert len(normalized["dataframes"]) >= 4


def test_data_type_from_filename():
    assert data_type_from_filename("com.samsung.health.weight.20260525120000.csv") == (
        "com.samsung.health.weight"
    )


def test_timestamp_with_offset():
    # 2026-05-01 08:00 UTC, offset +60 min
    ms = 1777632000000  # placeholder - use computed
    from datetime import datetime, timezone

    dt_utc = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    ms = int(dt_utc.timestamp() * 1000)
    result = ms_to_aware_datetime(ms, 60)
    assert result is not None
    assert result.tzinfo is not None


def test_weight_normalization(normalized):
    df = None
    for fname, frame in normalized["dataframes"].items():
        if "weight" in fname:
            df = frame
            break
    assert df is not None
    assert "start_datetime" in df.columns
    assert "weight" in df.columns


def test_rdf_transform(normalized):
    graphs = transform_export(normalized, DEFAULT_TEMPLATE_PATH)
    assert "com.samsung.health.weight" in graphs
    assert len(graphs["com.samsung.health.weight"]) > 0


def test_heart_rate_json_link(normalized):
    loaded = load_export(SYNTHETIC)
    hr_name = [k for k in loaded["dataframes"] if "heart_rate" in k][0]
    df = loaded["dataframes"][hr_name]
    if "binning_data" in df.columns:
        row = df.iloc[0].to_dict()
        enriched = enrich_row_with_json(loaded, row)
        assert enriched.get("_json_payload") is not None


def test_solid_export(normalized, tmp_path):
    graphs = transform_export(normalized, DEFAULT_TEMPLATE_PATH)
    written = export_to_solid(graphs, tmp_path)
    assert len(written["ttl"]) >= 1
    for p in written["ttl"]:
        assert p.exists()
        assert p.read_text(encoding="utf-8").startswith("@prefix") or "schema:" in p.read_text()


def test_merge_graphs(normalized):
    graphs = transform_export(normalized, DEFAULT_TEMPLATE_PATH)
    merged = merge_graphs(graphs)
    assert len(merged) >= sum(len(g) for g in graphs.values()) - 1


def test_clinical_mode_adds_references(normalized):
    simple = transform_export(
        normalized, DEFAULT_TEMPLATE_PATH, options=TransformOptions(clinical_mode=False)
    )
    clinical = transform_export(
        normalized, DEFAULT_TEMPLATE_PATH, options=TransformOptions(clinical_mode=True)
    )
    g_simple = simple["com.samsung.health.weight"]
    g_clinical = clinical["com.samsung.health.weight"]
    assert len(g_clinical) > len(g_simple)
    counts = count_clinical_triples(g_clinical)
    assert counts["health_ref"] > 0 or counts["snomed"] > 0 or counts["fhir"] > 0


def test_qudt_units_in_graph(normalized):
    graphs = transform_export(normalized, DEFAULT_TEMPLATE_PATH)
    g = graphs["com.samsung.health.weight"]
    turtle = g.serialize(format="turtle")
    assert "qudt.org" in turtle or "Kilogram" in turtle

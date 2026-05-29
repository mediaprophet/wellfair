# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
HuBMAP Human Reference Atlas (HRA) semantic client.

Queries the HRA Knowledge Graph SPARQL endpoint for ASCT+B data
(Anatomical Structures, Cell Types, Biomarkers) keyed by UBERON ID.

Results are cached locally as Turtle files to avoid repeated queries
against the 125GB remote KG.  Cache TTL: 30 days.

Endpoints used:
  SPARQL:  https://lod.humanatlas.io/sparql
  grlc:    https://apps.humanatlas.io/api/grlc/
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Cache ──────────────────────────────────────────────────────────────────────
_CACHE_DIR = Path(__file__).parent.parent / "data" / "hra_cache"
_CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 days

_SPARQL_ENDPOINT = "https://lod.humanatlas.io/sparql"
_GRLC_BASE = "https://apps.humanatlas.io/api/grlc"

# ── SPARQL query templates ──────────────────────────────────────────────────────
# Returns cell types and gene/protein biomarkers for a given UBERON structure.
_ASCTB_QUERY = """
PREFIX ccf:    <http://purl.org/ccf/>
PREFIX uberon: <http://purl.obolibrary.org/obo/UBERON_>
PREFIX cl:     <http://purl.obolibrary.org/obo/CL_>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?cellTypeLabel ?cellTypeId ?biomarkerLabel ?biomarkerType
WHERE {{
  ?as ccf:ccf_part_of* <http://purl.obolibrary.org/obo/{uberon_local}> .
  ?as ccf:has_cell_type ?ct .
  ?ct rdfs:label ?cellTypeLabel .
  BIND(str(?ct) AS ?cellTypeId)
  OPTIONAL {{
    ?ct ccf:has_biomarker ?bm .
    ?bm rdfs:label ?biomarkerLabel .
    OPTIONAL {{ ?bm ccf:biomarker_type ?biomarkerType }}
  }}
}}
LIMIT 100
"""

# Simpler fallback: just cell types for an organ label (uses text match)
_CELL_TYPES_BY_LABEL_QUERY = """
PREFIX ccf:  <http://purl.org/ccf/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?asLabel ?ctLabel ?ctId
WHERE {{
  ?as rdfs:label ?asLabel .
  FILTER(CONTAINS(LCASE(str(?asLabel)), LCASE("{organ_label}")))
  ?as ccf:has_cell_type ?ct .
  ?ct rdfs:label ?ctLabel .
  BIND(str(?ct) AS ?ctId)
}}
LIMIT 50
"""


# ── Data types ─────────────────────────────────────────────────────────────────
@dataclass
class CellType:
    label: str
    uri: str


@dataclass
class Biomarker:
    label: str
    biomarker_type: str = "gene"  # gene | protein | lipid | metabolite


@dataclass
class OrganAnnotation:
    uberon_id: str           # e.g. "UBERON:0000948"
    organ_label: str
    cell_types: list[CellType] = field(default_factory=list)
    biomarkers: list[Biomarker] = field(default_factory=list)

    def to_mesh_tooltip(self) -> str:
        ct_names = ", ".join(ct.label for ct in self.cell_types[:5])
        bm_names = ", ".join(bm.label for bm in self.biomarkers[:8])
        parts = []
        if ct_names:
            parts.append(f"Cell types: {ct_names}")
        if bm_names:
            parts.append(f"Biomarkers: {bm_names}")
        return " | ".join(parts) if parts else self.organ_label

    def to_rdf_turtle(self) -> str:
        """Emit RDFS/CCF triples linking this annotation to the health namespace."""
        lines = [
            f"@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .",
            f"@prefix ccf:    <http://purl.org/ccf/> .",
            f"@prefix uberon: <http://purl.obolibrary.org/obo/UBERON_> .",
            f"@prefix cl:     <http://purl.obolibrary.org/obo/CL_> .",
            f"@prefix health: <https://health.example.org/ns#> .",
            "",
        ]
        uberon_local = self.uberon_id.replace("UBERON:", "").replace(":", "_")
        as_uri = f"<http://purl.obolibrary.org/obo/UBERON_{uberon_local}>"
        lines.append(f"{as_uri} rdfs:label \"{self.organ_label}\" .")
        for ct in self.cell_types:
            lines.append(f"{as_uri} ccf:has_cell_type <{ct.uri}> .")
            lines.append(f"<{ct.uri}> rdfs:label \"{ct.label}\" .")
        for bm in self.biomarkers:
            lines.append(f"{as_uri} health:associatedBiomarker \"{bm.label}\" .")
        return "\n".join(lines)


# ── Cache helpers ──────────────────────────────────────────────────────────────
def _cache_key(query_id: str) -> str:
    return hashlib.sha256(query_id.encode()).hexdigest()[:16]


def _cache_path(query_id: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{_cache_key(query_id)}.json"


def _cache_load(query_id: str) -> dict[str, Any] | None:
    p = _cache_path(query_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - data.get("cached_at", 0) > _CACHE_TTL_SECONDS:
            p.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _cache_save(query_id: str, payload: dict[str, Any]) -> None:
    payload["cached_at"] = time.time()
    _cache_path(query_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ── SPARQL execution ───────────────────────────────────────────────────────────
def _sparql_select(query: str, timeout: int = 15) -> list[dict[str, str]]:
    """Execute a SPARQL SELECT against the HRA endpoint; return rows as dicts."""
    params = urlencode({"query": query, "format": "application/sparql-results+json"})
    url = f"{_SPARQL_ENDPOINT}?{params}"
    req = Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": "wellfair/0.0.3"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        raise RuntimeError(f"HRA SPARQL request failed: {e}") from e

    rows = []
    vars_ = data.get("head", {}).get("vars", [])
    for binding in data.get("results", {}).get("bindings", []):
        row = {v: binding[v]["value"] for v in vars_ if v in binding}
        rows.append(row)
    return rows


# ── Public API ─────────────────────────────────────────────────────────────────
def get_organ_annotation(uberon_id: str, organ_label: str = "") -> OrganAnnotation:
    """
    Fetch ASCT+B data for a UBERON anatomical structure.
    Returns cached result if available and fresh.

    uberon_id: "UBERON:0000948"  (colon or underscore separator accepted)
    organ_label: human-readable name used as fallback display
    """
    # Normalise: "UBERON:0000948" → "UBERON_0000948" for OBO URIs
    uberon_norm = uberon_id.replace(":", "_")
    cache_key = f"asctb_{uberon_norm}"

    cached = _cache_load(cache_key)
    if cached:
        ann = OrganAnnotation(
            uberon_id=uberon_id,
            organ_label=cached.get("organ_label", organ_label),
            cell_types=[CellType(**ct) for ct in cached.get("cell_types", [])],
            biomarkers=[Biomarker(**bm) for bm in cached.get("biomarkers", [])],
        )
        return ann

    query = _ASCTB_QUERY.format(uberon_local=uberon_norm)
    try:
        rows = _sparql_select(query)
    except RuntimeError:
        # Network unavailable — return empty annotation, do not cache
        return OrganAnnotation(uberon_id=uberon_id, organ_label=organ_label)

    cell_types: dict[str, CellType] = {}
    biomarkers: dict[str, Biomarker] = {}

    for row in rows:
        ct_id = row.get("cellTypeId", "")
        ct_label = row.get("cellTypeLabel", "")
        if ct_id and ct_label and ct_id not in cell_types:
            cell_types[ct_id] = CellType(label=ct_label, uri=ct_id)
        bm_label = row.get("biomarkerLabel", "")
        bm_type = row.get("biomarkerType", "gene")
        if bm_label and bm_label not in biomarkers:
            biomarkers[bm_label] = Biomarker(label=bm_label, biomarker_type=bm_type)

    ann = OrganAnnotation(
        uberon_id=uberon_id,
        organ_label=organ_label or uberon_id,
        cell_types=list(cell_types.values()),
        biomarkers=list(biomarkers.values()),
    )
    _cache_save(cache_key, {
        "organ_label": ann.organ_label,
        "cell_types": [{"label": ct.label, "uri": ct.uri} for ct in ann.cell_types],
        "biomarkers": [{"label": bm.label, "biomarker_type": bm.biomarker_type} for bm in ann.biomarkers],
    })
    return ann


# UBERON IDs for the organs loaded in loadTelemetryHologram()
ORGAN_UBERON_MAP: dict[str, tuple[str, str]] = {
    "heart":           ("UBERON:0000948", "Heart"),
    "kidney_left":     ("UBERON:0004538", "Left Kidney"),
    "kidney_right":    ("UBERON:0004539", "Right Kidney"),
    "lung":            ("UBERON:0002048", "Lung"),
    "large_intestine": ("UBERON:0000059", "Large Intestine"),
    "brain":           ("UBERON:0000955", "Brain"),
    "liver":           ("UBERON:0002107", "Liver"),
    "spleen":          ("UBERON:0002106", "Spleen"),
    "skin":            ("UBERON:0002097", "Skin"),
    "lymph_node":      ("UBERON:0000029", "Lymph Node"),
    "vasculature":     ("UBERON:0004537", "Blood Vasculature"),
}


def get_all_organ_annotations(organs: list[str] | None = None) -> dict[str, OrganAnnotation]:
    """
    Fetch annotations for all (or a subset of) known organs.
    Returns dict keyed by organ name (matching loadTelemetryHologram keys).
    """
    keys = organs or list(ORGAN_UBERON_MAP.keys())
    return {
        key: get_organ_annotation(ORGAN_UBERON_MAP[key][0], ORGAN_UBERON_MAP[key][1])
        for key in keys
        if key in ORGAN_UBERON_MAP
    }


def annotation_map_to_json(annotations: dict[str, OrganAnnotation]) -> str:
    """Serialise annotations to JSON for embedding in the Three.js bioData payload."""
    out: dict[str, dict] = {}
    for key, ann in annotations.items():
        out[key] = {
            "uberonId": ann.uberon_id,
            "label": ann.organ_label,
            "cellTypes": [ct.label for ct in ann.cell_types[:5]],
            "biomarkers": [bm.label for bm in ann.biomarkers[:8]],
            "tooltip": ann.to_mesh_tooltip(),
        }
    return json.dumps(out, ensure_ascii=False)


def clear_cache() -> int:
    """Delete all cached HRA responses. Returns number of files removed."""
    if not _CACHE_DIR.exists():
        return 0
    files = list(_CACHE_DIR.glob("*.json"))
    for f in files:
        f.unlink(missing_ok=True)
    return len(files)

# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Export RDF to Solid-style pod folders (Turtle + JSON-LD)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from rdflib import Graph
import json

from src.rdf_transformer import graph_to_jsonld


def _month_key_from_graph(graph: Graph) -> str:
    """Pick YYYY-MM from first schema:startDate literal in graph."""
    for _, _, lit in graph.triples((None, None, None)):
        if hasattr(lit, "toPython") and isinstance(lit.toPython(), datetime):
            return lit.toPython().strftime("%Y-%m")
        s = str(lit)
        m = re.match(r"(\d{4}-\d{2})", s)
        if m:
            return m.group(1)
    return datetime.now().strftime("%Y-%m")


def _slug_from_data_type(data_type: str) -> str:
    """com.samsung.health.weight -> weight"""
    parts = data_type.split(".")
    return parts[-1] if parts else "health"


def export_to_solid(
    graphs: dict[str, Graph] | Graph,
    output_folder: str | Path,
    *,
    also_jsonld: bool = True,
) -> dict[str, list[Path]]:
    """
    Write Solid-style folder layout:
      /health/{slug}/{YYYY-MM}.ttl
      /health/{slug}/{YYYY-MM}.jsonld
    """
    out_root = Path(output_folder).resolve()
    written: dict[str, list[Path]] = {"ttl": [], "jsonld": []}

    if isinstance(graphs, Graph):
        graphs = {"merged": graphs}

    for data_type, graph in graphs.items():
        if len(graph) == 0:
            continue

        slug = _slug_from_data_type(data_type)
        month = _month_key_from_graph(graph)
        dest_dir = out_root / "health" / slug
        dest_dir.mkdir(parents=True, exist_ok=True)

        ttl_path = dest_dir / f"{month}.ttl"
        graph.serialize(destination=str(ttl_path), format="turtle")
        written["ttl"].append(ttl_path)

        if also_jsonld:
            jsonld_path = dest_dir / f"{month}.jsonld"
            with jsonld_path.open("w", encoding="utf-8") as f:
                f.write(graph_to_jsonld(graph))
            written["jsonld"].append(jsonld_path)

    return written


def export_combined(
    graphs: dict[str, Graph],
    output_folder: str | Path,
) -> Path:
    """Single combined health.ttl at pod root."""
    out_root = Path(output_folder).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    combined = Graph()
    for g in graphs.values():
        for t in g:
            combined.add(t)
    path = out_root / "health" / "combined.ttl"
    path.parent.mkdir(parents=True, exist_ok=True)
    combined.serialize(destination=str(path), format="turtle")
    return path


def graph_to_turtle_string(graph: Graph, max_lines: int = 200) -> str:
    text = graph.serialize(format="turtle")
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... ({len(lines) - max_lines} more lines)"]
    return "\n".join(lines)


def get_sync_state_path(output_folder: str | Path) -> Path:
    return Path(output_folder).resolve() / "sync_state.json"


def load_sync_state(output_folder: str | Path) -> dict:
    path = get_sync_state_path(output_folder)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_sync_state(output_folder: str | Path, state: dict) -> None:
    path = get_sync_state_path(output_folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        import json
        json.dump(state, f, indent=2)


def update_sync_state_for_dtype(output_folder: str | Path, data_type: str, row_count: int) -> None:
    state = load_sync_state(output_folder)
    state[data_type] = {
        "row_count": row_count,
        "last_sync": datetime.now().isoformat()
    }
    save_sync_state(output_folder, state)

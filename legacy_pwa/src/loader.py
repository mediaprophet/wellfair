# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Parse Samsung Health export folders (CSVs + jsons/)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import data_type_from_filename, resolve_export_root

_SAMSUNG_META_RE = re.compile(r"^com\.samsung\.(?:health|shealth)\.")


def _read_csv(path: Path) -> pd.DataFrame:
    """Read Samsung export CSV (skips package metadata row when present)."""
    with path.open(encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()
    if _SAMSUNG_META_RE.match(first_line.strip()):
        return pd.read_csv(path, skiprows=[0], index_col=False, low_memory=False, on_bad_lines="skip")
    return pd.read_csv(path, index_col=False, low_memory=False, on_bad_lines="skip")


def _find_json_file(jsons_dir: Path, ref: str) -> Path | None:
    """Resolve JSON under flat or nested jsons/ layout (real exports use subfolders)."""
    name = Path(str(ref).strip()).name
    if not name:
        return None

    candidates = [
        jsons_dir / ref,
        jsons_dir / name,
    ]
    for c in candidates:
        if c.is_file():
            return c

    if not name.endswith(".json"):
        stem = name
        for found in jsons_dir.rglob(f"{stem}*.json"):
            return found
    else:
        for found in jsons_dir.rglob(name):
            return found
    return None


def _load_json_if_exists(jsons_dir: Path, ref: str | float | int | None) -> dict[str, Any] | list[Any] | None:
    if ref is None or (isinstance(ref, float) and pd.isna(ref)):
        return None
    path = _find_json_file(jsons_dir, str(ref))
    if path is None:
        return None
    with path.open(encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_export(export_path: str | Path, progress_cb=None) -> dict[str, Any]:
    """
    Load a Samsung Health export directory.

    ``export_path`` may be the top-level folder (e.g. 20250221_SamsungHealth/)
    or the inner folder that directly contains CSV + jsons/ files.

    Returns:
        {
            "export_path": Path,
            "export_root_requested": Path,
            "dataframes": {filename: DataFrame},
            "data_types": {data_type_key: filename},
            "jsons_dir": Path | None,
            "json_cache": {},
        }
    """
    requested = Path(export_path).resolve()
    root = resolve_export_root(requested)

    jsons_dir = root / "jsons"
    has_jsons = jsons_dir.is_dir()

    dataframes: dict[str, pd.DataFrame] = {}
    data_types: dict[str, str] = {}

    csv_files = sorted(root.glob("*.csv"))
    total_csvs = len(csv_files)

    for idx, csv_path in enumerate(csv_files):
        fname = csv_path.name
        if progress_cb:
            progress_cb(idx, total_csvs, f"Loading: {fname}")
            
        df = _read_csv(csv_path)
        dataframes[fname] = df
        dtype = data_type_from_filename(fname)
        data_types[dtype] = fname

    if progress_cb and total_csvs > 0:
        progress_cb(total_csvs, total_csvs, "Loading complete.")

    return {
        "export_path": root,
        "export_root_requested": requested,
        "dataframes": dataframes,
        "dataframes_count": len(dataframes),
        "data_types": data_types,
        "jsons_dir": jsons_dir if has_jsons else None,
        "json_cache": {},
    }


def enrich_row_with_json(
    loaded: dict[str, Any],
    row: dict[str, Any],
    json_column: str = "binning_data",
) -> dict[str, Any]:
    """Lazily attach JSON payload from jsons/ when row references a file."""
    jsons_dir = loaded.get("jsons_dir")
    if not jsons_dir:
        return row

    ref = row.get(json_column) or row.get("extra_data")
    if ref is None or (isinstance(ref, float) and pd.isna(ref)):
        return row

    cache: dict[str, Any] = loaded.setdefault("json_cache", {})
    key = str(ref)
    if key not in cache:
        cache[key] = _load_json_if_exists(jsons_dir, ref)

    out = dict(row)
    out["_json_payload"] = cache[key]
    return out


def dataframe_with_json(
    loaded: dict[str, Any],
    df: pd.DataFrame,
    json_column: str = "binning_data",
) -> pd.DataFrame:
    """Expand rows that reference jsons/ (binning_data or extra_data)."""
    col = json_column
    if col not in df.columns and "extra_data" in df.columns:
        col = "extra_data"
    if col not in df.columns or not loaded.get("jsons_dir"):
        return df

    payloads = []
    for _, row in df.iterrows():
        enriched = enrich_row_with_json(loaded, row.to_dict(), col)
        payloads.append(enriched.get("_json_payload"))

    out = df.copy()
    out["_json_payload"] = payloads
    return out

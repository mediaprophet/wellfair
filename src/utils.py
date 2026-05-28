# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared utilities for health-to-solid."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOT = PROJECT_ROOT
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "20250221_SamsungHealth"
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "config" / "ontology_template.yaml"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "solid_pod"

# Resolved lazily — real export is nested under 20250221_SamsungHealth/
_DEFAULT_EXPORT_ROOT: Path | None = None


def resolve_export_root(path: str | Path) -> Path:
    """
    Find the Samsung export folder that contains CSV files.

    Accepts the zip extract root (e.g. 20250221_SamsungHealth/) or the inner
    samsunghealth_* folder directly.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Export folder not found: {root}")

    csv_here = list(root.glob("*.csv"))
    if csv_here:
        return root

    best_dir: Path | None = None
    best_count = 0
    for csv_path in root.rglob("*.csv"):
        parent = csv_path.parent
        count = len(list(parent.glob("*.csv")))
        if count > best_count:
            best_count = count
            best_dir = parent

    if best_dir is not None and best_count > 0:
        return best_dir

    raise FileNotFoundError(f"No Samsung Health CSV export found under: {root}")


def get_default_export_path() -> Path:
    """Default export path (resolves nested Samsung folder when present)."""
    global _DEFAULT_EXPORT_ROOT
    if _DEFAULT_EXPORT_ROOT is not None:
        return _DEFAULT_EXPORT_ROOT
    if DEFAULT_EXPORT_DIR.is_dir():
        try:
            _DEFAULT_EXPORT_ROOT = resolve_export_root(DEFAULT_EXPORT_DIR)
            return _DEFAULT_EXPORT_ROOT
        except FileNotFoundError:
            pass
    fallback = PROJECT_ROOT / "data" / "synthetic_samsung_export"
    _DEFAULT_EXPORT_ROOT = fallback if fallback.is_dir() else DEFAULT_EXPORT_DIR
    return _DEFAULT_EXPORT_ROOT


# Back-compat name used by UI/tests
DEFAULT_EXPORT_PATH = get_default_export_path()


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    """Resolve relative paths against project root or given base."""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    root = base or PROJECT_ROOT
    return (root / p).resolve()


def data_type_from_filename(filename: str) -> str:
    """
    Extract Samsung data type key from export CSV filename.
    e.g. com.samsung.health.weight.20250221185535.csv -> com.samsung.health.weight
    """
    stem = Path(filename).stem
    match = re.match(r"^(.+?)\.(\d{8,})$", stem)
    if match:
        return match.group(1)
    return stem


def clean_column_name(col: str) -> str:
    """
    Normalize Samsung column headers to short field names.
    e.g. com.samsung.health.sleep.start_time -> start_time
    """
    col = str(col).strip()
    match = re.match(
        r"^com\.samsung\.(?:health|shealth)\.(?:[\w.]+\.)?(.+)$",
        col,
    )
    if match:
        return match.group(1)
    for prefix in (
        "com.samsung.health.",
        "com.samsung.shealth.",
        "com.samsung.",
    ):
        if col.startswith(prefix):
            return col[len(prefix) :]
    if "." in col:
        return col.split(".")[-1]
    return col


def safe_str(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None


def get_export_mtime(export_path: str | Path) -> float:
    """Find the maximum modification timestamp among all CSV files in the export folder."""
    root = Path(export_path).resolve()
    if not root.is_dir():
        return 0.0
    
    max_mtime = 0.0
    for path in root.rglob("*.csv"):
        try:
            mtime = path.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime
        except Exception:
            pass
    return max_mtime


def check_cache_status(export_path: str | Path, output_path: str | Path) -> tuple[bool, str]:
    """
    Checks if the local pickle cache is stale compared to the raw export files.
    Returns (is_stale: bool, reason: str).
    """
    cache_file = Path(output_path).resolve() / "local_cache.pkl"
    if not cache_file.exists():
        return True, "No local cache found."
        
    try:
        cache_mtime = cache_file.stat().st_mtime
        export_mtime = get_export_mtime(export_path)
        
        if export_mtime == 0.0:
            return False, "Export folder contains no CSV files. Cache is assumed up-to-date."
            
        if export_mtime > cache_mtime:
            return True, "Export CSV files have been updated since last sync."
            
        return False, "Cache is up-to-date with export files."
    except Exception as e:
        return True, f"Failed to verify cache: {e}"


def save_uploaded_pdf(uploaded_file, subdir="psychiatric") -> str:
    """Save an uploaded PDF to the project's data assessments directory.

    Parameters
    ----------
    uploaded_file: UploadedFile
        Streamlit uploaded file object.
    subdir: str, optional
        Subdirectory under ``data/assessments``; default ``"psychiatric"``.

    Returns
    -------
    str
        Absolute file URI (``file://``) of the saved PDF.
    """
    # Ensure target directory exists
    target_dir = PROJECT_ROOT / "data" / "assessments" / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Resolve safe filename and write bytes
    filename = Path(uploaded_file.name).name
    target_path = target_dir / filename
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return target_path.as_uri()

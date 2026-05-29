# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared utilities for wellfair and health-to-solid semantic export."""

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


# ---------------------------------------------------------------------------
# PDF Text Extraction & Structured Parsing Utilities
# ---------------------------------------------------------------------------

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # Will degrade gracefully in environments without pypdf


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """
    Extract raw text from a PDF file.
    Works with both local paths and (in future) in-memory uploads.
    """
    if PdfReader is None:
        return "[PDF text extraction not available - pypdf not installed]"

    path = Path(pdf_path)
    if not path.exists():
        return ""

    try:
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as e:
        return f"[Error extracting PDF text: {e}]"


def parse_pathology_report(text: str) -> list[dict]:
    """
    Improved regex-based parser for common pathology report formats (especially Australian labs).
    Handles many variations seen in Laverty, DHM, Sonic, etc. reports.
    """
    import re

    observations = []

    # Expanded patterns for real-world Australian pathology reports
    patterns = [
        # "Fasting Blood Glucose   5.4   mmol/L   (3.0 - 6.0)" or "(3.0-6.0)"
        r"([A-Za-z][A-Za-z\s\-\(\),]+?)\s+(\d+\.?\d*)\s*([a-zA-Z/%]+)\s*\(?\s*([\d.<>]+)\s*[-–]\s*([\d.<>]+)\)?",

        # "Total Cholesterol: 6.1 mmol/L   Reference: < 5.5"
        r"([A-Za-z][A-Za-z\s\-\(\),]+?):\s*(\d+\.?\d*)\s*([a-zA-Z/%]+)\s*(?:Reference|Ref|Range)?[:\s]*[<≤]?\s*([\d.]+)",

        # "HbA1c   48   mmol/mol   (20-42)"
        r"([A-Za-z][A-Za-z0-9\s\-\(\)]+?)\s+(\d+\.?\d*)\s*([a-zA-Z/%]+)\s*\(?\s*([\d.]+)\s*[-–]\s*([\d.]+)\)?",

        # Handle "< 5.0" or "> 100" as the value
        r"([A-Za-z][A-Za-z\s\-\(\),]+?)\s*[<≤>]\s*(\d+\.?\d*)\s*([a-zA-Z/%]+)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            groups = match.groups()
            obs = {}

            try:
                test_name = groups[0].strip().rstrip(":").strip()
                value_str = groups[1].replace("<", "").replace(">", "").strip()
                unit = groups[2].strip()

                obs = {
                    "test_name": test_name,
                    "value": float(value_str),
                    "unit": unit,
                }

                # Handle reference range if present
                if len(groups) >= 5 and groups[3] and groups[4]:
                    low = groups[3].replace("<", "").replace(">", "").strip()
                    high = groups[4].replace("<", "").replace(">", "").strip()
                    if low:
                        obs["reference_range_low"] = float(low)
                    if high:
                        obs["reference_range_high"] = float(high)
                elif len(groups) == 4 and groups[3]:
                    high = groups[3].replace("<", "").replace(">", "").strip()
                    if high:
                        obs["reference_range_high"] = float(high)

                observations.append(obs)
            except (ValueError, IndexError):
                continue

    # Deduplicate by normalized test name
    seen = set()
    unique = []
    for o in observations:
        key = o["test_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(o)

    return unique


def generate_rdf_for_pathology_report(report: "DiagnosticReport") -> str:
    """Generate basic Turtle RDF for a DiagnosticReport and its observations."""
    try:
        from rdflib import Graph, URIRef, Literal, Namespace
        from rdflib.namespace import RDF, XSD

        HEALTH = Namespace("urn:health:schema:")
        g = Graph()

        subj = URIRef(f"urn:health:diagnostic:{report.id}")
        g.add((subj, RDF.type, HEALTH.DiagnosticReport))
        g.add((subj, HEALTH.dateIssued, Literal(str(report.date_issued.date()), datatype=XSD.date)))

        for obs in report.observations:
            obs_subj = URIRef(f"urn:health:observation:{obs.id}")
            g.add((subj, HEALTH.hasObservation, obs_subj))
            g.add((obs_subj, RDF.type, HEALTH.PathologyObservation))
            g.add((obs_subj, HEALTH.testName, Literal(obs.test_name)))
            g.add((obs_subj, HEALTH.value, Literal(obs.value)))
            g.add((obs_subj, HEALTH.unit, Literal(obs.unit)))
            if obs.reference_range_low is not None:
                g.add((obs_subj, HEALTH.referenceLow, Literal(obs.reference_range_low)))
            if obs.reference_range_high is not None:
                g.add((obs_subj, HEALTH.referenceHigh, Literal(obs.reference_range_high)))

        return g.serialize(format="turtle")
    except Exception as e:
        return f"# RDF generation failed: {e}"


def generate_rdf_for_questionnaire(record: dict) -> str:
    """Generate Turtle RDF for a questionnaire submission (supports multiple completions)."""
    try:
        from rdflib import Graph, URIRef, Literal, Namespace
        from rdflib.namespace import RDF, XSD

        HEALTH = Namespace("urn:health:schema:")
        g = Graph()

        qid = record.get("id", "unknown")
        subj = URIRef(f"urn:health:questionnaire:{qid}")

        g.add((subj, RDF.type, HEALTH.PsychiatricQuestionnaire))
        g.add((subj, HEALTH.assessmentType, Literal(record.get("type", "Unknown"))))
        g.add((subj, HEALTH.dateTaken, Literal(record.get("date_taken"))))
        g.add((subj, HEALTH.totalScore, Literal(record.get("total_score", 0))))

        if record.get("notes"):
            g.add((subj, HEALTH.notes, Literal(record["notes"])))

        for q, val in record.get("scores", {}).items():
            if val is not None:
                g.add((subj, URIRef(f"{HEALTH}{q}"), Literal(val)))

        return g.serialize(format="turtle")
    except Exception as e:
        return f"# RDF generation failed: {e}"


# ---------------------------------------------------------------------------
# Vault Persistence Helpers for Structured Assessments
# ---------------------------------------------------------------------------

def save_structured_assessment(record: dict, assessment_type: str = "questionnaire"):
    """Persist a structured assessment (questionnaire or pathology) to session vault."""
    key = "vault_questionnaires" if assessment_type == "questionnaire" else "vault_pathology_reports"
    if key not in st.session_state:
        st.session_state[key] = []
    st.session_state[key].append(record)


def get_all_structured_assessments():
    """Return all persisted structured assessments for timeline / RDF use."""
    questionnaires = st.session_state.get("vault_questionnaires", [])
    pathology = st.session_state.get("vault_pathology_reports", [])
    return questionnaires + pathology

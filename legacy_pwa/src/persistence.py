"""
Simple file-based persistence for WellFair vault data.

This module provides lightweight, human-readable JSON storage for structured
data that should survive app restarts (questionnaires, pathology reports, etc.).

It is intentionally minimal so it works in both:
- Native Streamlit (normal filesystem)
- Pyodide / Stlite (falls back to in-memory if filesystem is restricted)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # Allow importing the module outside Streamlit (for testing/scripts)

from src.utils import PROJECT_ROOT

VAULT_DIR = PROJECT_ROOT / "data" / "vault"
VAULT_DIR.mkdir(parents=True, exist_ok=True)


def _get_path(name: str) -> Path:
    return VAULT_DIR / f"{name}.json"


def save_vault_data(name: str, data: list[dict] | dict) -> bool:
    """
    Save a list or dict of structured records to disk as JSON.
    Returns True on success.
    """
    try:
        path = _get_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        # In Pyodide this can fail — we silently degrade
        st.warning(f"Could not save {name} to disk: {e}")
        return False


def load_vault_data(name: str, default: list | dict | None = None) -> Any:
    """
    Load structured data from disk. Returns default if file does not exist
    or cannot be read.
    """
    path = _get_path(name)
    if not path.exists():
        return default if default is not None else []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else []


def save_questionnaires(records: list[dict]) -> bool:
    """Persist questionnaire submissions."""
    return save_vault_data("questionnaires", records)


def load_questionnaires() -> list[dict]:
    """Load previously saved questionnaire submissions."""
    return load_vault_data("questionnaires", [])


def save_pathology_reports(reports: list[dict]) -> bool:
    """Persist extracted pathology reports."""
    return save_vault_data("pathology_reports", reports)


def load_pathology_reports() -> list[dict]:
    """Load previously saved pathology reports."""
    return load_vault_data("pathology_reports", [])


def auto_save_structured_data():
    """
    Convenience function — call this after any important structured data change.
    It will persist the main vault collections if they exist in session_state.
    """
    if st is None:
        return  # Running outside Streamlit
    if "vault_questionnaires" in st.session_state:
        save_questionnaires(st.session_state.vault_questionnaires)

    if "vault_pathology_reports" in st.session_state:
        save_pathology_reports(st.session_state.vault_pathology_reports)


def auto_load_structured_data():
    """
    Load persisted data into session_state on startup if not already present.
    Call this early in ui/app.py or in the relevant tabs.
    """
    if st is None:
        return
    if "vault_questionnaires" not in st.session_state:
        st.session_state.vault_questionnaires = load_questionnaires()

    if "vault_pathology_reports" not in st.session_state:
        st.session_state.vault_pathology_reports = load_pathology_reports()
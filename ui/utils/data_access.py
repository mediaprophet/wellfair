from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.loader import load_export
from src.normalizer import normalize_export
from src.rdf_transformer import TransformOptions, transform_export
from src.utils import DEFAULT_OUTPUT_PATH, ROOT, check_cache_status


@st.cache_data(show_spinner=False)
def cached_load(export_path: str, output_path: str = None) -> dict:
    output_dir = Path(output_path) if output_path else Path(DEFAULT_OUTPUT_PATH)
    cache_file = output_dir / "local_cache.pkl"
    
    is_stale, reason = check_cache_status(export_path, output_dir)
    if not is_stale and cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def load_cb(idx: int, total: int, msg: str):
        progress = (idx / total) if total > 0 else 0
        progress_bar.progress(progress)
        status_text.text(msg)
        
    def norm_cb(idx: int, total: int, msg: str):
        progress = (idx / total) if total > 0 else 0
        progress_bar.progress(progress)
        status_text.text(msg)
        
    loaded = load_export(export_path, progress_cb=load_cb)
    normalized = normalize_export(loaded, progress_cb=norm_cb)
    
    progress_bar.empty()
    status_text.empty()
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            pickle.dump(normalized, f)
    except Exception:
        pass
        
    return normalized


@st.cache_data(show_spinner=False)
def cached_transform(export_path: str, template_path: str, clinical_mode: bool, output_path: str = None) -> dict:
    normalized = cached_load(export_path, output_path)
    options = TransformOptions(clinical_mode=clinical_mode, include_provenance=True)
    return transform_export(normalized, template_path, progress=False, options=options)


@st.cache_resource
def load_dataset_mappings() -> dict:
    try:
        mappings_path = ROOT / "config" / "dataset_mappings.json"
        if mappings_path.exists():
            with open(mappings_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Failed to load dataset mappings: {e}")
    return {}

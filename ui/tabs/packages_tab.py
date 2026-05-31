"""
Packages Tab — manage optional capability packages.
Displays install status and lets users trigger the download UI for each package.
"""
from __future__ import annotations

import streamlit as st
from ui.utils.package_bridge import (
    get_capabilities,
    get_package_status,
    is_feature_available,
    trigger_install_ui,
)

# Display metadata for each package (mirrors registry.json)
_PACKAGES: list[dict] = [
    {
        "id":          "oxigraph",
        "icon":        "🗄️",
        "name":        "RDF Store (oxigraph)",
        "description": "In-browser SPARQL 1.1 query engine. Compiled into the base app — always available.",
        "features":    ["SPARQL queries", "RDF data management", "User profile store"],
        "size":        "Bundled",
        "bundled":     True,
        "platform":    "All platforms",
    },
    {
        "id":          "prolog-wasm",
        "icon":        "🧠",
        "name":        "Prolog Reasoning Engine",
        "description": (
            "SWI-Prolog compiled to WebAssembly. Runs differential diagnosis rules, "
            "welfare eligibility checks, and clinical logic entirely in your browser. "
            "No data leaves your device."
        ),
        "features":    [
            "Differential diagnosis evaluation",
            "Welfare & NDIS eligibility",
            "Clinical logic rules from published studies",
            "3D anatomy reasoning",
        ],
        "size":        "~8 MB",
        "bundled":     False,
        "platform":    "All platforms",
    },
    {
        "id":          "llm-mediapipe",
        "icon":        "🤖",
        "name":        "On-device LLM — MediaPipe / LiteRT",
        "description": (
            "Runs Gemma 2B locally on your Android device via Google's MediaPipe LiteRT framework. "
            "Enables paper extraction from journal PDFs, document ingestion, and natural language "
            "explanations of diagnostic results. GPU-accelerated on Android Chrome. "
            "Requires a one-time model download (~1.3 GB stored on your device)."
        ),
        "features":    [
            "Paper & document extraction",
            "Natural language explanations",
            "Study vault authoring",
            "Local AI — no cloud, no data sharing",
        ],
        "size":        "~5 MB runtime + ~1.3 GB model",
        "bundled":     False,
        "platform":    "Android / Chromium (GPU recommended)",
        "note":        (
            "The Gemma model requires accepting Google's licence on Kaggle. "
            "After downloading the .bin file, use the 'Load from file' option in the install dialog."
        ),
    },
    {
        "id":          "llm-nvidia",
        "icon":        "⚡",
        "name":        "On-device LLM — NVIDIA / CUDA",
        "description": "Future support for NVIDIA GPU-accelerated inference on desktop. Not yet available.",
        "features":    ["High-performance desktop inference"],
        "size":        "—",
        "bundled":     False,
        "platform":    "Desktop (NVIDIA GPU)",
        "future":      True,
    },
]

_CAP_LABELS: dict[str, str] = {
    "core:rdf":         "RDF / Turtle",
    "core:sparql":      "SPARQL queries",
    "reasoning:prolog": "Prolog reasoning",
    "reasoning:n3":     "N3Logic / EYE",
    "llm:inference":    "LLM inference",
    "llm:extraction":   "Document extraction",
    "llm:explanation":  "Language explanations",
}

_STATUS_LABEL: dict[str, tuple[str, str]] = {
    "bundled":       ("✓ Bundled",    "#2dd4bf"),
    "installed":     ("✓ Installed",  "#2dd4bf"),
    "loaded":        ("✓ Active",     "#4ade80"),
    "downloading":   ("⬇ Downloading","#fbbf24"),
    "not-installed": ("Not installed","#71717a"),
    "error":         ("Error",        "#f87171"),
    "future":        ("Coming soon",  "#71717a"),
}


def render_packages(dark_mode: bool = True) -> None:
    st.markdown("## Capability Packages")
    st.markdown(
        "WellFair uses an on-demand package system. Base features are always available. "
        "Advanced reasoning and AI features require optional packages — each downloaded "
        "once and stored on your device. **All computation stays local.**"
    )

    # Active capabilities summary
    caps = get_capabilities()
    if caps:
        cap_pills = " &nbsp;·&nbsp; ".join(
            f'<span style="color:#2dd4bf">{_CAP_LABELS.get(c, c)}</span>'
            for c in sorted(caps)
        )
        st.markdown(
            f"<div style='font-size:0.82rem;color:#a1a1aa;margin-bottom:1.2rem;'>"
            f"Active capabilities: {cap_pills}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    for pkg in _PACKAGES:
        _render_package_card(pkg, dark_mode)


def _render_package_card(pkg: dict, dark_mode: bool) -> None:
    pkg_id   = pkg["id"]
    is_future = pkg.get("future", False)

    if is_future:
        status_str = "future"
    elif pkg.get("bundled"):
        status_str = "bundled"
    else:
        status_str = get_package_status(pkg_id)

    label, color = _STATUS_LABEL.get(status_str, ("Unknown", "#71717a"))

    # Header row
    col_info, col_status = st.columns([4, 1])
    with col_info:
        st.markdown(f"### {pkg['icon']}  {pkg['name']}")
    with col_status:
        st.markdown(
            f"<div style='text-align:right;padding-top:12px;font-size:0.85rem;"
            f"font-weight:600;color:{color}'>{label}</div>",
            unsafe_allow_html=True,
        )

    # Description
    st.markdown(
        f"<p style='color:#a1a1aa;font-size:0.88rem;margin-bottom:0.6rem;'>"
        f"{pkg['description']}</p>",
        unsafe_allow_html=True,
    )

    # Note (e.g. Kaggle auth requirement)
    if pkg.get("note"):
        st.info(pkg["note"], icon="ℹ️")

    # Features unlocked
    col_features, col_action = st.columns([3, 1])
    with col_features:
        st.markdown(
            "<div style='font-size:0.8rem;color:#71717a;'>Enables:</div>",
            unsafe_allow_html=True,
        )
        for feat in pkg["features"]:
            st.markdown(
                f"<div style='font-size:0.82rem;color:#a1a1aa;padding-left:12px;'>• {feat}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='font-size:0.75rem;color:#52525b;margin-top:6px;'>Platform: {pkg['platform']}</div>",
            unsafe_allow_html=True,
        )

    with col_action:
        if not is_future and not pkg.get("bundled"):
            if status_str in ("installed", "loaded"):
                st.success("Ready")
            elif status_str == "downloading":
                st.spinner("Downloading…")
            else:
                size_note = f" ({pkg['size']})" if pkg.get("size") else ""
                if st.button(
                    f"Install{size_note}",
                    key=f"pkg_install_{pkg_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    trigger_install_ui(pkg_id)
                    st.info("Opening install dialog in your browser…", icon="📦")
        elif pkg.get("bundled"):
            st.markdown(
                "<div style='text-align:center;font-size:0.8rem;color:#2dd4bf;padding-top:8px;'>Always on</div>",
                unsafe_allow_html=True,
            )

    st.divider()

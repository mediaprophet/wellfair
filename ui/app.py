import argparse
import sys
import os

import streamlit as st
from pathlib import Path


def _ensure_project_on_path() -> None:
    """Make sure the project root is importable.
    
    This is especially important under Pyodide/Stlite where the virtual
    filesystem and sys.path can be surprising.
    """
    candidates: list[str] = []

    # Best effort from __file__
    try:
        here = Path(__file__).resolve().parent.parent
        candidates.append(str(here))
    except Exception:
        pass

    # Common Pyodide/Stlite mount roots
    candidates.extend(["/home/pyodide", ".", str(Path.cwd())])

    for p in candidates:
        if p and p not in sys.path:
            sys.path.insert(0, p)


_ensure_project_on_path()

from src.utils import ROOT, DEFAULT_EXPORT_PATH, DEFAULT_TEMPLATE_PATH, DEFAULT_OUTPUT_PATH, PROJECT_ROOT, check_cache_status
from ui.utils import (
    inject_css,
    cached_load,
    init_mock_data,
    auto_load_structured_data,
    auto_save_structured_data,
)

DEVICE_DATA_DIR = "/device_data"

def has_device_data() -> bool:
    """Check if files were injected from the phone's file system via the PWA bridge."""
    try:
        return os.path.isdir(DEVICE_DATA_DIR) and len(os.listdir(DEVICE_DATA_DIR)) > 0
    except Exception:
        return False

def get_device_data_files() -> list[str]:
    try:
        if has_device_data():
            return [os.path.join(DEVICE_DATA_DIR, f) for f in os.listdir(DEVICE_DATA_DIR)]
    except Exception:
        pass
    return []
from ui.utils.navigation import render_sidebar_nav, get_nav_items
import os
from ui.tabs.personal_health import render_personal_health
from ui.tabs.pathology import render_pathology
from ui.tabs.mental_health import render_mental_health
from ui.tabs.assessment_psychiatric import render_psychiatric_assessments
from ui.tabs.psychology import render_psychology
from ui.tabs.life_events import render_life_events
from ui.tabs.location import render_location
from ui.tabs.agent_directory import render_agent_directory
from ui.tabs.vault_admin import render_vault_admin
from ui.tabs.document_ingestion import render_document_ingestion
from ui.tabs.calendar_timeline import render_calendar_timeline
from ui.tabs.sanctuary_mode import render_sanctuary_mode
from ui.tabs.anatomy_3d import render_anatomy_3d
from ui.tabs.case_management import render_case_management
from ui.tabs.social_work import render_social_work
from ui.tabs.profile_intake import render_profile_intake
from ui.tabs.study_vault import render_study_vault
from ui.tabs.dev_tools import render_dev_tools


st.set_page_config(
    page_title="Episteme:WellFair v0.0.4-dev – Personal Well-Fair Vault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",   # Better mobile experience — user can open sidebar when needed
)

def parse_args():
    parser = argparse.ArgumentParser(description="Samsung Health RDF Vault Dashboard")
    parser.add_argument("--export-path", type=str, default=str(DEFAULT_EXPORT_PATH), help="Path to Samsung Health export folder")
    parser.add_argument("--template", type=str, default=str(DEFAULT_TEMPLATE_PATH), help="Path to ontology mapping template")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="Output directory for RDF files")
    
    # Check if run by streamlit or pyodide and skip parsing if so
    if "streamlit" in sys.argv[0] or "pyodide" in sys.modules:
        return parser.parse_args([])
    try:
        return parser.parse_args()
    except SystemExit:
        return parser.parse_args([])

def main():
    args = parse_args()
    
    # Profile selection
    profile_options = ["gemini", "developer_real", "production", "michael", "elena", "rebecca", "margaret", "robert", "jordan"]
    profile_labels = {
        "gemini": "♊ gemini (Demo Dev Profile)",
        "developer_real": "🛠️ developer_real (Real Data)",
        "production": "🔒 production (Production)",
        "michael": "👤 Michael R. (Demo)",
        "elena": "👤 Elena V. (Demo)",
        "rebecca": "👤 Rebecca L. (Demo)",
        "margaret": "👤 Margaret T. (Demo)",
        "robert": "👤 Robert K. (Demo)",
        "jordan": "👤 Jordan M. (Demo)"
    }

    # Add device data source if available (from installed PWA file system bridge)
    if has_device_data():
        profile_options = ["device"] + profile_options
        profile_labels["device"] = "📱 Device Exports (Phone Storage)"

    profile = st.sidebar.selectbox(
        "Environment Profile",
        options=profile_options,
        index=0,
        format_func=lambda x: profile_labels.get(x, x)
    )
    
    if profile == "device" and has_device_data():
        # Use files injected from the phone via the PWA File System Access bridge
        export_path = DEVICE_DATA_DIR
        output_path = str(PROJECT_ROOT / "data" / "demo" / "device" / "solid_pod")
    elif profile == "gemini":
        export_path = str(PROJECT_ROOT / "data" / "demo" / "gemini" / "samsung_export")
        output_path = str(PROJECT_ROOT / "data" / "demo" / "gemini" / "solid_pod")
    elif profile in ["michael", "elena", "rebecca", "margaret", "robert", "jordan"]:
        export_path = str(PROJECT_ROOT / "data" / "demo" / profile / "samsung_export")
        output_path = str(PROJECT_ROOT / "data" / "demo" / profile / "solid_pod")
    else:
        export_path = args.export_path
        output_path = args.output
        
    template_path = args.template
    
    # Sync status controls in sidebar for real data and production
    if profile not in ["gemini", "michael", "elena", "rebecca", "margaret", "robert", "jordan"]:
        is_stale, reason = check_cache_status(export_path, output_path)
        if is_stale:
            st.sidebar.warning(f"🔄 Sync Needed: {reason}")
            if st.sidebar.button("Trigger Sync & Import", type="primary"):
                st.cache_data.clear()
                cache_file = Path(output_path) / "local_cache.pkl"
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                    except Exception:
                        pass
                st.rerun()
        else:
            st.sidebar.success("✅ Vault Sync Complete")
            if st.sidebar.button("Force Re-Sync"):
                st.cache_data.clear()
                cache_file = Path(output_path) / "local_cache.pkl"
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                    except Exception:
                        pass
                st.rerun()
                
    st.sidebar.divider()
    
    # Initialize mock datastore early
    init_mock_data()

    # Restore persisted vault data (questionnaires, pathology reports, etc.)
    auto_load_structured_data()

    # Show device data source status (PWA + Android file system access)
    if has_device_data():
        device_files = get_device_data_files()
        st.sidebar.success(f"📱 Device imports ready: {len(device_files)} files in /device_data")
        if st.sidebar.button("Use Device Exports as Source", type="secondary"):
            # This allows the rest of the app to treat /device_data as the export root
            st.session_state["device_data_mode"] = True
            st.rerun()
    
    st.sidebar.markdown("""
         <div style='padding: 10px 0px 20px 0px;'>
             <h1 style='font-size: 2.2rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #14b8a6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;'>Episteme<br><span style='font-size: 1.7rem; font-weight: 700;'>:WellFair</span></h1>
             <p style='font-size: 0.72rem; font-weight: 600; color: #64748b; margin: 6px 0 0 0; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1.3;'>Personal Well-Fair Vault & Digital Services Ecosystem</p>
             <p style='font-size: 0.65rem; color: #64748b; margin-top: 4px;'>v0.0.4-dev • 30 May 2026</p>
         </div>
    """, unsafe_allow_html=True)
    
    # Sanctuary Mode detection & visual shift
    is_sanctuary = st.session_state.get("sanctuary_unlocked", False)
    if is_sanctuary:
        dark_mode = True
        inject_css(True)
        st.markdown(
            """<style>
            .stApp {
                background-color: #030005 !important;
                background-image: radial-gradient(circle at 50% 0%, #20000a 0%, transparent 40%), linear-gradient(0deg, #030005 0%, #030005 100%) !important;
                color: #ffb3c6 !important;
            }
            h1, h2, h3, h4, h5 {
                color: #ff1e56 !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            .premium-card {
                background: rgba(15, 0, 5, 0.7) !important;
                border: 1px solid rgba(255, 30, 86, 0.3) !important;
                box-shadow: 0 0 15px rgba(255, 30, 86, 0.1) !important;
                animation: pulse 4s infinite alternate;
            }
            @keyframes pulse {
                from { box-shadow: 0 0 15px rgba(255, 30, 86, 0.05); }
                to { box-shadow: 0 0 25px rgba(255, 30, 86, 0.2); border-color: rgba(255, 30, 86, 0.5); }
            }
            .premium-card:hover {
                border-color: #ff1e56 !important;
                box-shadow: 0 0 35px rgba(255, 30, 86, 0.4) !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #050002 !important;
                border-right: 1px solid rgba(255, 30, 86, 0.2) !important;
            }
            div[data-testid="stForm"] {
                border: 1px solid rgba(255, 30, 86, 0.2) !important;
                background: rgba(10, 0, 5, 0.8) !important;
            }
            div[data-testid="stRadio"] [data-testid="stRadioOptionCircle"] {
                display: none !important;
            }
            div[data-testid="stRadio"] label div[role="presentation"] {
                display: none !important;
            }
            </style>""",
            unsafe_allow_html=True
        )
    else:
        dark_mode = st.sidebar.toggle("Dark Mode", value=False)
        inject_css(dark_mode)
    
    st.sidebar.divider()
    
    # New premium navigation (button-driven, stable keys, excellent mobile support)
    app_section_key = render_sidebar_nav(dark_mode, is_sanctuary)
    
    st.sidebar.divider()

    # Developer Tools — direct button outside nav group to avoid sidebar clipping
    if st.sidebar.button("🔧 Dev Tools & Tests", key="nav_dev_tools", use_container_width=True):
        from ui.utils.navigation import set_current_section
        set_current_section("dev_tools")
        st.rerun()

    st.sidebar.divider()

    # Settings Toggle
    show_settings = st.sidebar.toggle("⚙️ Vault Administration", value=False)
    
    st.sidebar.divider()
    st.sidebar.subheader("🛡️ Sanctuary Vault")
    if is_sanctuary:
        st.sidebar.markdown("<span style='color: #ef4444; font-weight: bold;'>🔓 Sanctuary Vault Active</span>", unsafe_allow_html=True)
        if st.sidebar.button("🔒 Lock Vault & Exit", type="primary"):
            st.session_state.sanctuary_unlocked = False
            st.rerun()
    else:
        with st.sidebar.expander("🔑 Unlock Sanctuary Mode"):
            # In demo/Pyodide environments the export path may not exist – fall back to mock data
            _is_demo_profile = profile in ["gemini", "michael", "elena", "rebecca", "margaret", "robert", "jordan"]
            pin_label = "Vault PIN (Demo PIN: 8888)" if _is_demo_profile else "Vault PIN"
            
            sanctuary_pin = st.text_input(pin_label, type="password", key="sidebar_sanctuary_pin")
            if st.button("Unlock Vault"):
                if sanctuary_pin == "8888":
                    st.session_state.sanctuary_unlocked = True
                    st.rerun()
                else:
                    st.error("Invalid PIN")
    
    # Device data from phone is treated as real user data
    _is_device_profile = profile == "device"
    _is_demo_profile = profile in ["gemini", "michael", "elena", "rebecca", "margaret", "robert", "jordan"]

    if not os.path.exists(export_path):
        if _is_device_profile:
            st.error("Device data folder is empty or not accessible.")
            st.stop()
        elif not _is_demo_profile:
            st.error(f"Export path not found: `{export_path}`")
            st.info("Please set the correct path via CLI: `python -m streamlit run ui/app.py -- --export-path /path/to/export`")
            st.stop()
        else:
            normalized = {}
    else:
        try:
            normalized = cached_load(export_path, output_path)
        except Exception as e:
            if _is_demo_profile:
                st.warning(f"⚠️ Could not load wearable data ({e}). Running on demo data only.")
                normalized = {}
            else:
                st.error(f"Failed to load export data: {e}")
                st.stop()

    # === Clean section router (stable keys from navigation.py) ===
    SECTION_RENDERERS = {
        "personal_health": lambda: render_personal_health(dark_mode, normalized),
        "case_management": lambda: render_case_management(dark_mode, normalized),
        "profile_intake": lambda: render_profile_intake(dark_mode, normalized),
        "study_vault": lambda: render_study_vault(dark_mode),
        "pathology": lambda: render_pathology(dark_mode),
        "calendar_timeline": lambda: render_calendar_timeline(dark_mode),
        "mental_health": lambda: render_mental_health(dark_mode, normalized),
        "assessments": lambda: render_psychiatric_assessments(dark_mode),
        "anatomy_3d": lambda: render_anatomy_3d(dark_mode, normalized),
        "life_events": lambda: render_life_events(dark_mode),
        "social_work": lambda: render_social_work(dark_mode),
        "location": lambda: render_location(dark_mode),
        "agent_directory": lambda: render_agent_directory(dark_mode, normalized),
        "document_ingestion": lambda: render_document_ingestion(dark_mode),
        "sanctuary_mode": lambda: render_sanctuary_mode(dark_mode),
        "dev_tools":       lambda: render_dev_tools(dark_mode),
    }

    if show_settings:
        render_vault_admin(dark_mode, normalized, export_path, template_path, output_path)
    else:
        renderer = SECTION_RENDERERS.get(app_section_key, SECTION_RENDERERS["profile_intake"])
        renderer()

if __name__ == "__main__":
    main()

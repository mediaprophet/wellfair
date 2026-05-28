import argparse
import sys
import os

import streamlit as st
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils import ROOT, DEFAULT_EXPORT_PATH, DEFAULT_TEMPLATE_PATH, DEFAULT_OUTPUT_PATH, PROJECT_ROOT, check_cache_status
from ui.utils import inject_css, cached_load, init_mock_data
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
from ui.tabs.case_management import render_case_management
from ui.tabs.social_work import render_social_work
from ui.tabs.profile_intake import render_profile_intake
from ui.tabs.study_vault import render_study_vault


st.set_page_config(
    page_title="Episteme:WellFair – A Personal Well-Fair Vault & Digital Services Ecosystem",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def parse_args():
    parser = argparse.ArgumentParser(description="Samsung Health RDF Vault Dashboard")
    parser.add_argument("--export-path", type=str, default=str(DEFAULT_EXPORT_PATH), help="Path to Samsung Health export folder")
    parser.add_argument("--template", type=str, default=str(DEFAULT_TEMPLATE_PATH), help="Path to ontology mapping template")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="Output directory for RDF files")
    
    # Check if run by streamlit and skip parsing if so
    if "streamlit" in sys.argv[0]:
        return parser.parse_args([])
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Profile selection
    profile = st.sidebar.selectbox(
        "Environment Profile",
        options=["gemini", "developer_real", "production"],
        index=0,
        format_func=lambda x: {
            "gemini": "♊ gemini (Demo Dev Profile)",
            "developer_real": "🛠️ developer_real (Real Data)",
            "production": "🔒 production (Production)"
        }[x]
    )
    
    if profile == "gemini":
        export_path = str(PROJECT_ROOT / "data" / "demo" / "gemini" / "samsung_export")
        output_path = str(PROJECT_ROOT / "data" / "demo" / "gemini" / "solid_pod")
    else:
        export_path = args.export_path
        output_path = args.output
        
    template_path = args.template
    
    # Sync status controls in sidebar for real data and production
    if profile != "gemini":
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
    
    st.sidebar.markdown("""
         <div style='padding: 10px 0px 20px 0px;'>
             <h1 style='font-size: 2.2rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #14b8a6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;'>Episteme<br><span style='font-size: 1.7rem; font-weight: 700;'>:WellFair</span></h1>
             <p style='font-size: 0.72rem; font-weight: 600; color: #64748b; margin: 6px 0 0 0; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1.3;'>Personal Well-Fair Vault & Digital Services Ecosystem</p>
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
                background: #0c051a !important;
                color: #f4f4f7 !important;
            }
            h1, h2, h3, h4, h5 {
                color: #f43f5e !important;
            }
            .premium-card {
                background: rgba(20, 10, 35, 0.6) !important;
                border: 1px solid rgba(244, 63, 94, 0.15) !important;
                box-shadow: 0 10px 30px rgba(244, 63, 94, 0.1) !important;
            }
            .premium-card:hover {
                border-color: #a855f7 !important;
                box-shadow: 0 20px 40px rgba(168, 85, 247, 0.2) !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #080312 !important;
                border-right: 1px solid rgba(244, 63, 94, 0.1) !important;
            }
            div[data-testid="stForm"] {
                border: 1px solid rgba(168, 85, 247, 0.2) !important;
                background: rgba(15, 5, 25, 0.4) !important;
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
    
    # Navigation
    st.sidebar.subheader("Navigation")
    nav_options = [
        "❤️ Personal Health",
        "💼 Case Management & Claims Vault",
        "📋 Profile & Medical Intake",
        "📖 Study & Research Vault",
        "🔬 Lab & Pathology Results",
        "📅 Semantic Timeline & Calendar",
        "🧠 Mental Health & Wellbeing",
        "🧪 Psychology",
        "📝 Assessments",
        "🏛️ Life Events & Socioeconomic Wellbeing",
        "🤝 Social Work & Assistance",
        "📍 Location & Environmental Triggers",
        "👥 Agent Directory, Delegation & Cases",
        "📥 Document Ingestion & Claims"
    ]
    if is_sanctuary:
        nav_options.append("🤫 Sanctuary Mode")
        
    app_section = st.sidebar.radio(
        "Go to",
        options=nav_options,
        index=len(nav_options)-1 if is_sanctuary and not st.session_state.get("sanctuary_mode_redirected", False) else 0,
        label_visibility="collapsed"
    )
    if is_sanctuary:
        st.session_state.sanctuary_mode_redirected = True
    else:
        st.session_state.pop("sanctuary_mode_redirected", None)
    
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
            sanctuary_pin = st.text_input("Vault PIN", type="password", key="sidebar_sanctuary_pin")
            if st.button("Unlock Vault"):
                if sanctuary_pin == "8888":
                    st.session_state.sanctuary_unlocked = True
                    st.rerun()
                else:
                    st.error("Invalid PIN")
    
    if not os.path.exists(export_path):
        st.error(f"Export path not found: `{export_path}`")
        st.info("Please set the correct path via CLI: `python -m streamlit run ui/app.py -- --export-path /path/to/export`")
        st.stop()
        
    try:
        normalized = cached_load(export_path, output_path)
    except Exception as e:
        st.error(f"Failed to load export data: {e}")
        st.stop()

    # Route based on navigation
    if app_section == "❤️ Personal Health":
        render_personal_health(dark_mode, normalized)
    elif app_section == "💼 Case Management & Claims Vault":
        render_case_management(dark_mode, normalized)
    elif app_section == "📋 Profile & Medical Intake":
        render_profile_intake(dark_mode, normalized)
    elif app_section == "📖 Study & Research Vault":
        render_study_vault(dark_mode)
    elif app_section == "🔬 Lab & Pathology Results":
        render_pathology(dark_mode)
    elif app_section == "📅 Semantic Timeline & Calendar":
        render_calendar_timeline(dark_mode)
    elif app_section == "🧠 Mental Health & Wellbeing":
        render_mental_health(dark_mode)
    elif app_section == "🧪 Psychology":
        render_psychology(dark_mode)
    elif app_section == "📝 Assessments":
        render_psychiatric_assessments(dark_mode)
    elif app_section == "🏛️ Life Events & Socioeconomic Wellbeing":
        render_life_events(dark_mode)
    elif app_section == "🤝 Social Work & Assistance":
        render_social_work(dark_mode)
    elif app_section == "📍 Location & Environmental Triggers":
        render_location(dark_mode)
    elif app_section == "👥 Agent Directory, Delegation & Cases":
        render_agent_directory(dark_mode, normalized)
    elif app_section == "📥 Document Ingestion & Claims":
        render_document_ingestion(dark_mode)
    elif app_section == "🤫 Sanctuary Mode":
        render_sanctuary_mode(dark_mode)
        
    # Optional settings panel
    if show_settings:
        render_vault_admin(dark_mode, normalized, export_path, template_path, output_path)

if __name__ == "__main__":
    main()

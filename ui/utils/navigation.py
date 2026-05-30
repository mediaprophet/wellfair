import streamlit as st
from ui.utils.package_bridge import is_nav_section_available, missing_caps_for, _NAV_FEATURE_MAP

# Grouped nav structure: (group_label, [ (key, label), ... ])
_NAV_GROUPS = [
    ("FOUNDATION", [
        ("profile_intake",    "👤 Profile & Intake"),
        ("personal_health",   "❤️ Personal Health"),
        ("calendar_timeline", "📅 Calendar & Timeline"),
    ]),
    ("CLINICAL RECORD", [
        ("pathology",         "🔬 Pathology & Labs"),
        ("anatomy_3d",        "🧬 3D Anatomy"),
        ("mental_health",     "🧠 Mental Health & Psychiatry"),
        ("life_events",       "🗓️ Life Events"),
    ]),
    ("CASE MANAGEMENT", [
        ("case_management",   "📂 Case Management"),
        ("social_work",       "🤝 Social Work"),
        ("assessments",       "📋 Psychiatric Assessments"),
        ("document_ingestion","📄 Documents"),
    ]),
    ("RESEARCH", [
        ("study_vault",       "📚 Study Vault"),
        ("location",          "📍 Location"),
    ]),
    ("NETWORK", [
        ("agent_directory",   "🤖 Agent Directory"),
    ]),
    ("SANCTUARY", [
        ("sanctuary_mode",    "🛡️ Sanctuary Mode"),
    ]),
    ("SYSTEM", [
        ("packages",          "📦 Packages"),
    ]),
]

# Flat list for legacy callers
_NAV_ITEMS = [item for _, group in _NAV_GROUPS for item in group]

_SESSION_KEY = "_nav_section"


def get_nav_items() -> list[tuple[str, str]]:
    return _NAV_ITEMS


def get_current_section() -> str:
    return st.session_state.get(_SESSION_KEY, _NAV_ITEMS[0][0])


def set_current_section(key: str):
    st.session_state[_SESSION_KEY] = key


def render_sidebar_nav(dark_mode: bool = False, is_sanctuary: bool = False) -> str:
    current = get_current_section()

    label_color = "#94a3b8" if dark_mode else "#64748b"
    active_bg = "rgba(248,113,113,0.18)" if is_sanctuary else "rgba(20,184,166,0.18)"
    active_border = "#f87171" if is_sanctuary else "#14b8a6"
    active_text = "#fca5a5" if is_sanctuary else "#14b8a6"

    for group_label, items in _NAV_GROUPS:
        # Skip sanctuary group unless unlocked
        if group_label == "SANCTUARY" and not is_sanctuary:
            continue


        st.sidebar.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;color:{label_color};"
            f"text-transform:uppercase;letter-spacing:0.1em;"
            f"padding:10px 4px 4px 4px;'>{group_label}</div>",
            unsafe_allow_html=True,
        )

        for key, label in items:
            active = key == current
            available = is_nav_section_available(key)

            if active:
                st.sidebar.markdown(
                    f"<div style='background:{active_bg};border-left:3px solid {active_border};"
                    f"padding:8px 12px;border-radius:8px;font-weight:700;margin-bottom:3px;"
                    f"color:{active_text};font-size:0.9rem;'>{label}</div>",
                    unsafe_allow_html=True,
                )
            elif not available:
                # Show dimmed, non-clickable item with a lock indicator
                st.sidebar.markdown(
                    f"<div style='opacity:0.38;padding:8px 12px;border-radius:8px;"
                    f"margin-bottom:3px;color:#71717a;font-size:0.9rem;"
                    f"cursor:default;user-select:none;'>{label} 🔒</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
                    set_current_section(key)
                    st.rerun()

    return current

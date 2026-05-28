from __future__ import annotations

import re

import streamlit as st


HEALTH_COLORS = {
    "primary": "#0d9488",
    "secondary": "#14b8a6",
    "accent": "#f97316",
    "clinical": "#7c3aed",
    "bg_light": "#f0fdfa",
    "bg_dark": "#0f172a",
}

CLINICAL_HIGHLIGHT_PATTERNS = [
    (re.compile(r"snomed\.info", re.I), "#a855f7"),
    (re.compile(r"loinc\.org", re.I), "#6366f1"),
    (re.compile(r"hl7\.org/fhir", re.I), "#ec4899"),
    (re.compile(r"qudt\.org", re.I), "#0891b2"),
    (re.compile(r"semanticReference", re.I), "#f59e0b"),
]

def inject_css(dark: bool) -> None:
    bg = HEALTH_COLORS["bg_dark"] if dark else HEALTH_COLORS["bg_light"]
    text_color = "#f8fafc" if dark else "#0f172a"
    card_bg = "rgba(30, 41, 59, 0.5)" if dark else "rgba(255, 255, 255, 0.7)"
    card_border = "rgba(255, 255, 255, 0.08)" if dark else "rgba(15, 23, 42, 0.06)"
    shadow = "rgba(0, 0, 0, 0.3)" if dark else "rgba(0, 0, 0, 0.05)"
    
    # Mode-based input styles
    input_bg = "rgba(15, 23, 42, 0.6)" if dark else "rgba(255, 255, 255, 0.9)"
    input_border = "rgba(255, 255, 255, 0.08)" if dark else "rgba(15, 23, 42, 0.1)"
    label_color = "#cbd5e1" if dark else "#334155"
    
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        /* App and Base Typography */
        .stApp {{
            background: {bg};
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            color: {text_color};
        }}
        
        h1, h2, h3, h4, h5 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: {HEALTH_COLORS["primary"]};
            margin-bottom: 0.5rem;
        }}
        
        /* Premium Card Layouts */
        .premium-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 30px {shadow};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 18px;
        }}
        .premium-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 20px 40px {shadow};
            border-color: {HEALTH_COLORS["secondary"]};
        }}
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {"rgba(15, 23, 42, 0.95)" if dark else "rgba(240, 253, 250, 0.95)"} !important;
            border-right: 1px solid {card_border} !important;
            backdrop-filter: blur(8px);
        }}
        
        /* Navigation (stRadio) styled as premium tabs */
        div[data-testid="stRadio"] > div {{
            gap: 8px !important;
            padding: 4px 0;
        }}
        
        div[data-testid="stRadio"] label {{
            background-color: {input_bg} !important;
            border: 1px solid {input_border} !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
            color: {label_color} !important;
            font-weight: 500 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        div[data-testid="stRadio"] label:hover {{
            background-color: {"rgba(20, 184, 166, 0.1)" if dark else "rgba(20, 184, 166, 0.05)"} !important;
            border-color: {HEALTH_COLORS["primary"]} !important;
            transform: translateX(4px);
        }}
        
        div[data-testid="stRadio"] label:has(input:checked) {{
            background: linear-gradient(135deg, rgba(20, 184, 166, 0.15), rgba(59, 130, 246, 0.15)) !important;
            border-color: {HEALTH_COLORS["primary"]} !important;
            color: {HEALTH_COLORS["secondary"]} !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(20, 184, 166, 0.15);
        }}
        
        /* Hide native circular radio dot for menu items */
        div[data-testid="stRadio"] label [data-testid="stFiberManualRecord"] {{
            display: none !important;
        }}
        div[data-testid="stRadio"] label input[type="radio"] {{
            display: none !important;
        }}
        div[data-testid="stRadio"] [data-testid="stRadioOptionCircle"] {{
            display: none !important;
        }}
        div[data-testid="stRadio"] label div[role="presentation"] {{
            display: none !important;
        }}
        
        /* Toggles (stToggle) as premium switch cards */
        div[data-testid="stToggle"] {{
            background-color: {card_bg};
            border: 1px solid {card_border};
            border-radius: 14px;
            padding: 12px 18px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
            margin-bottom: 10px;
        }}
        div[data-testid="stToggle"]:hover {{
            border-color: {HEALTH_COLORS["secondary"]};
            background-color: {"rgba(30, 41, 59, 0.65)" if dark else "rgba(255, 255, 255, 0.9)"};
        }}
        div[data-testid="stToggle"] label {{
            color: {label_color} !important;
            font-weight: 500 !important;
            cursor: pointer;
        }}
        
        /* Checkboxes (stCheckbox) as premium pill-check cards */
        div[data-testid="stCheckbox"] {{
            background-color: {card_bg};
            border: 1px solid {card_border};
            border-radius: 12px;
            padding: 10px 16px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
            margin-bottom: 8px;
        }}
        div[data-testid="stCheckbox"]:hover {{
            border-color: {HEALTH_COLORS["secondary"]};
            background-color: {"rgba(30, 41, 59, 0.65)" if dark else "rgba(255, 255, 255, 0.9)"};
            transform: translateY(-1px);
        }}
        div[data-testid="stCheckbox"] label {{
            color: {label_color} !important;
            font-weight: 500 !important;
            cursor: pointer;
        }}
        
        /* Premium custom selectboxes */
        div[data-baseweb="select"] {{
            background-color: {input_bg} !important;
            border-radius: 12px !important;
            border: 1px solid {input_border} !important;
        }}
        
        /* Metric Styles */
        .metric-title {{
            font-size: 0.85rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 800;
            color: {text_color};
            margin-top: 4px;
            line-height: 1.1;
            background: linear-gradient(135deg, {text_color}, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .metric-subtitle {{
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 6px;
        }}
        
        /* Flex Alignment Utilities */
        .flex-center {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .icon-circle {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }}
        
        /* Tabs Premium styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            background-color: {input_bg};
            padding: 6px;
            border-radius: 14px;
            border: 1px solid {input_border};
        }}
        .stTabs [data-baseweb="tab"] {{
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 600;
            color: #64748b;
            background-color: transparent;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {HEALTH_COLORS["primary"]};
            background-color: rgba(20, 184, 166, 0.05);
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {"rgba(20, 184, 166, 0.15)" if dark else "#ffffff"} !important;
            color: {HEALTH_COLORS["primary"]} !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {card_border};
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {HEALTH_COLORS["primary"]}88;
        }}
        
        .clinical-line {{
            font-family: monospace;
            font-size: 0.85rem;
            padding: 2px 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def highlight_turtle_clinical(turtle: str) -> str:
    lines_html = []
    for line in turtle.splitlines():
        color = None
        for pattern, c in CLINICAL_HIGHLIGHT_PATTERNS:
            if pattern.search(line):
                color = c
                break
        if color:
            lines_html.append(
                f'<div class="clinical-line" style="background:{color}22;border-left:3px solid {color}">'
                f"{line.replace('<', '&lt;').replace('>', '&gt;')}</div>"
            )
        else:
            lines_html.append(
                f'<div class="clinical-line">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
            )
    return "\n".join(lines_html)

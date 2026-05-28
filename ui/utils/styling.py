from __future__ import annotations

import re

import streamlit as st


HEALTH_COLORS = {
    "primary": "#0d9488",
    "secondary": "#14b8a6",
    "accent": "#f97316",
    "clinical": "#7c3aed",
    "bg_light": "#f8fafc",
    "bg_dark": "#0B0F19", # Deep, rich dark navy/black
}

CLINICAL_HIGHLIGHT_PATTERNS = [
    (re.compile(r"snomed\.info", re.I), "#a855f7"),
    (re.compile(r"loinc\.org", re.I), "#6366f1"),
    (re.compile(r"hl7\.org/fhir", re.I), "#ec4899"),
    (re.compile(r"qudt\.org", re.I), "#0891b2"),
    (re.compile(r"semanticReference", re.I), "#f59e0b"),
]

def inject_css(dark: bool) -> None:
    # Hyper-premium color palettes
    bg = HEALTH_COLORS["bg_dark"] if dark else HEALTH_COLORS["bg_light"]
    text_color = "#f1f5f9" if dark else "#0f172a"
    
    # Advanced Glassmorphism Definitions
    # We use multiple shadow layers and precise border opacity to simulate depth
    card_bg = "rgba(15, 23, 42, 0.45)" if dark else "rgba(255, 255, 255, 0.6)"
    card_border_top = "rgba(255, 255, 255, 0.15)" if dark else "rgba(255, 255, 255, 0.8)"
    card_border_bottom = "rgba(255, 255, 255, 0.02)" if dark else "rgba(15, 23, 42, 0.05)"
    shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.37)" if dark else "0 8px 32px 0 rgba(31, 38, 135, 0.07)"
    
    input_bg = "rgba(15, 23, 42, 0.6)" if dark else "rgba(255, 255, 255, 0.8)"
    input_border = "rgba(255, 255, 255, 0.08)" if dark else "rgba(15, 23, 42, 0.1)"
    label_color = "#cbd5e1" if dark else "#334155"
    
    # Dynamic mesh background CSS variables
    mesh_gradient = "radial-gradient(at 40% 20%, hsla(28,100%,74%,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(189,100%,56%,0.15) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(355,100%,93%,0.1) 0px, transparent 50%)" if dark else "radial-gradient(at 40% 20%, hsla(28,100%,74%,0.3) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(189,100%,56%,0.3) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(355,100%,93%,0.3) 0px, transparent 50%)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        /* Keyframe Animations */
        @keyframes fadeUp {{
            0% {{ opacity: 0; transform: translateY(15px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes floatMesh {{
            0% {{ background-position: 0% 0%; }}
            50% {{ background-position: 100% 100%; }}
            100% {{ background-position: 0% 0%; }}
        }}

        /* App and Base Typography */
        .stApp {{
            background-color: {bg};
            background-image: {mesh_gradient};
            background-attachment: fixed;
            background-size: 200% 200%;
            animation: floatMesh 30s ease infinite;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: {text_color};
        }}
        
        h1, h2, h3, h4, h5 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: {HEALTH_COLORS["primary"]};
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}
        
        /* World-Class Premium Cards */
        .premium-card {{
            background: {card_bg};
            border-top: 1px solid {card_border_top};
            border-left: 1px solid {card_border_top};
            border-bottom: 1px solid {card_border_bottom};
            border-right: 1px solid {card_border_bottom};
            border-radius: 20px;
            padding: 24px;
            box-shadow: {shadow};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            margin-bottom: 20px;
            animation: fadeUp 0.6s ease-out forwards;
        }}
        
        .premium-card:hover {{
            transform: translateY(-4px) scale(1.005);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
            border-top: 1px solid {HEALTH_COLORS["secondary"]};
        }}
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {"rgba(11, 15, 25, 0.75)" if dark else "rgba(248, 250, 252, 0.75)"} !important;
            border-right: 1px solid {card_border_bottom} !important;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }}
        
        /* Premium Radio/Navigation Tabs */
        div[data-testid="stRadio"] > div {{
            gap: 10px !important;
            padding: 4px 0;
        }}
        
        div[data-testid="stRadio"] label {{
            background-color: {input_bg} !important;
            border: 1px solid {input_border} !important;
            border-radius: 14px !important;
            padding: 12px 18px !important;
            color: {label_color} !important;
            font-weight: 500 !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 0.95rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
            box-shadow: inset 0 2px 4px rgba(255,255,255,0.05), 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        div[data-testid="stRadio"] label:hover {{
            background-color: {"rgba(20, 184, 166, 0.15)" if dark else "rgba(20, 184, 166, 0.08)"} !important;
            border-color: {HEALTH_COLORS["primary"]} !important;
            transform: translateX(6px);
        }}
        
        div[data-testid="stRadio"] label:has(input:checked) {{
            background: linear-gradient(135deg, rgba(20, 184, 166, 0.2), rgba(59, 130, 246, 0.2)) !important;
            border-color: {HEALTH_COLORS["primary"]} !important;
            border-left: 4px solid {HEALTH_COLORS["primary"]} !important;
            color: {HEALTH_COLORS["secondary"]} !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 16px rgba(20, 184, 166, 0.2);
            transform: scale(1.02);
        }}
        
        /* Hide native circular radio dot */
        div[data-testid="stRadio"] label [data-testid="stFiberManualRecord"],
        div[data-testid="stRadio"] label input[type="radio"],
        div[data-testid="stRadio"] [data-testid="stRadioOptionCircle"],
        div[data-testid="stRadio"] label div[role="presentation"] {{
            display: none !important;
        }}
        
        /* Metric Styles */
        .metric-title {{
            font-size: 0.8rem;
            color: #94a3b8;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        .metric-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            color: {text_color};
            margin-top: 4px;
            line-height: 1.1;
            background: linear-gradient(135deg, {text_color}, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .metric-subtitle {{
            font-size: 0.8rem;
            color: {HEALTH_COLORS["primary"]};
            margin-top: 6px;
            font-weight: 500;
        }}
        
        /* Flex Alignment Utilities */
        .flex-center {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .icon-circle {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            background: linear-gradient(135deg, rgba(20,184,166,0.2), rgba(20,184,166,0.05));
            border: 1px solid rgba(20,184,166,0.3);
            box-shadow: inset 0 2px 10px rgba(255,255,255,0.1);
        }}
        
        /* Toggles and Checkboxes */
        div[data-testid="stToggle"], div[data-testid="stCheckbox"] {{
            background-color: {card_bg};
            border: 1px solid {card_border_top};
            border-radius: 12px;
            padding: 12px 18px;
            transition: all 0.3s ease;
            box-shadow: {shadow};
            backdrop-filter: blur(8px);
        }}
        div[data-testid="stToggle"]:hover, div[data-testid="stCheckbox"]:hover {{
            border-color: {HEALTH_COLORS["secondary"]};
            transform: translateY(-2px);
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
            background: rgba(148, 163, 184, 0.3);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {HEALTH_COLORS["primary"]};
        }}
        
        .clinical-line {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            padding: 4px 8px;
            border-radius: 4px;
            margin-bottom: 2px;
        }}
        
        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: {shadow};
            border: 1px solid {card_border_top};
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
                f'<div class="clinical-line" style="background:{color}15;border-left:3px solid {color}">'
                f"{line.replace('<', '&lt;').replace('>', '&gt;')}</div>"
            )
        else:
            lines_html.append(
                f'<div class="clinical-line">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
            )
    return "\n".join(lines_html)

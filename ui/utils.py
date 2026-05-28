from __future__ import annotations

import json
import re
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.loader import load_export
from src.normalizer import normalize_export
from src.rdf_transformer import TransformOptions, load_template, transform_export
from src.utils import ROOT, data_type_from_filename, check_cache_status, DEFAULT_OUTPUT_PATH

from src.phr_models.proxy_consent import RelatedPerson, ProxyConsent, PrivacyMode, LegalBasis, ProxyRelationship
from src.phr_models.psychiatry import ObservationContext
from src.phr_models.medications import AdherenceStatus
from src.phr_models.medications import DataQualityTag as MedDataQualityTag
from src.phr_models.location import SemanticCategory
from src.phr_models.life_events import (
    LifeEventCategory, WellbeingDimension, SeverityLevel,
    DocumentCategory, RecoveryStatus, MaslowLayer,
    DataQualityTag as LifeDataQualityTag,
)
from src.phr_models.cases import CaseFile, CaseTask, CaseCategory, CaseStatus
from src.phr_models.pathology import DiagnosticReport, PathologyObservation, DiagnosticReportStatus
from src.phr_models.agents import ActorType, Actor, DelegationRule, VerificationStatus

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


def get_dashboard_metrics(normalized: dict) -> dict:
    metrics = {
        "steps": {"value": "No Data", "subtitle": "Daily average steps"},
        "sleep": {"value": "No Data", "subtitle": "Average sleep duration"},
        "weight": {"value": "No Data", "subtitle": "Latest body weight"},
        "heart_rate": {"value": "No Data", "subtitle": "Average active HR"},
    }
    
    weight_df = find_df_by_keyword(normalized, "weight")
    if weight_df is not None and not weight_df.empty:
        if "weight" in weight_df.columns:
            if "start_datetime" in weight_df.columns:
                weight_df = weight_df.sort_values("start_datetime")
            latest_w = weight_df["weight"].dropna().iloc[-1]
            metrics["weight"]["value"] = f"{latest_w:.1f} kg"
            
    steps_df = find_df_by_keyword(normalized, "pedometer_day_summary")
    if steps_df is not None and not steps_df.empty:
        col_name = "count" if "count" in steps_df.columns else ("step_count" if "step_count" in steps_df.columns else None)
        if col_name:
            avg_steps = steps_df[col_name].dropna().mean()
            metrics["steps"]["value"] = f"{int(avg_steps):,} steps"
    elif (steps_df := find_df_by_keyword(normalized, "step_daily_trend")) is not None and not steps_df.empty:
        col_name = "count" if "count" in steps_df.columns else ("step_count" if "step_count" in steps_df.columns else None)
        if col_name:
            avg_steps = steps_df[col_name].dropna().mean()
            metrics["steps"]["value"] = f"{int(avg_steps):,} steps"
            
    sleep_df = find_df_by_datatype(normalized, "com.samsung.shealth.sleep")
    if sleep_df is not None and not sleep_df.empty:
        if "sleep_duration" in sleep_df.columns:
            avg_mins = sleep_df["sleep_duration"].dropna().mean()
            hrs = int(avg_mins // 60)
            mins = int(avg_mins % 60)
            metrics["sleep"]["value"] = f"{hrs}h {mins}m"
        elif "efficiency" in sleep_df.columns:
            avg_eff = sleep_df["efficiency"].dropna().mean()
            metrics["sleep"]["value"] = f"{avg_eff:.1f}% efficiency"
            
    hr_df = find_df_by_keyword(normalized, "heart_rate")
    if hr_df is not None and not hr_df.empty:
        hr_col = "heart_rate" if "heart_rate" in hr_df.columns else ("pulse" if "pulse" in hr_df.columns else None)
        if hr_col:
            avg_hr = hr_df[hr_col].dropna().mean()
            metrics["heart_rate"]["value"] = f"{int(avg_hr)} BPM"
            
    return metrics


def extract_timeline_events(normalized: dict) -> list[dict]:
    events = []
    
    def get_col_val(row, alternatives):
        for alt in alternatives:
            if alt in row:
                return row[alt]
        for key in row.keys():
            for alt in alternatives:
                if key.endswith("." + alt):
                    return row[key]
        return None

    def parse_samsung_time(raw_val):
        if pd.isna(raw_val) or raw_val is None:
            return None
        try:
            if isinstance(raw_val, (int, float)):
                dt = pd.to_datetime(raw_val, unit='ms')
            else:
                dt = pd.to_datetime(raw_val)
            if dt.year < 2000:
                return None
            return dt
        except Exception:
            return None

    exercise_df = find_df_by_keyword(normalized, "exercise")
    if exercise_df is not None and not exercise_df.empty:
        for _, row_pd in exercise_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            ex_type_code = get_col_val(row, ["exercise_type"])
            ex_type_map = {
                1001: "Walking 🚶",
                1002: "Running 🏃",
                1003: "Cycling 🚴",
                1004: "Swimming 🏊",
                10026: "Stretching 🧘",
                10027: "Strength Training 🏋️",
                13001: "Hiking 🥾",
                14001: "Aerobics 💃",
                15001: "Yoga 🧘",
            }
            try:
                ex_code_val = int(float(ex_type_code)) if ex_type_code is not None and not pd.isna(ex_type_code) else 0
            except ValueError:
                ex_code_val = 0
            ex_name = ex_type_map.get(ex_code_val, "Workout 🏃")
            
            duration = get_col_val(row, ["duration"])
            dur_mins = 0
            if duration is not None and not pd.isna(duration):
                try:
                    dur_val = float(duration)
                    if dur_val > 10000:
                        dur_mins = int(dur_val / 60000)
                    else:
                        dur_mins = int(dur_val)
                except ValueError:
                    pass
                    
            calories = get_col_val(row, ["calorie"])
            distance = get_col_val(row, ["distance"])
            
            desc_parts = []
            if dur_mins > 0:
                desc_parts.append(f"⏱️ **Duration:** {dur_mins} mins")
            if calories is not None and not pd.isna(calories) and float(calories) > 0:
                desc_parts.append(f"🔥 **Calories:** {int(float(calories))} kcal")
            if distance is not None and not pd.isna(distance) and float(distance) > 0:
                dist_km = float(distance) / 1000.0
                desc_parts.append(f"📏 **Distance:** {dist_km:.2f} km")
                
            desc = " | ".join(desc_parts) if desc_parts else "Exercise session logged."
            
            events.append({
                "datetime": dt,
                "title": f"Workout: {ex_name}",
                "category": "Activity",
                "emoji": "🏃",
                "color": "#3b82f6",
                "description": desc,
                "raw": row
            })
            
    badge_df = find_df_by_keyword(normalized, "badge")
    if badge_df is not None and not badge_df.empty:
        for _, row_pd in badge_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_time", "create_time", "update_time"]))
            if dt is None:
                continue
            
            key_name = get_col_val(row, ["key"]) or "badge"
            friendly_name = str(key_name).replace("_", " ").title()
            
            events.append({
                "datetime": dt,
                "title": f"Badge Achieved: {friendly_name}",
                "category": "Achievement",
                "emoji": "🏅",
                "color": "#fbbf24",
                "description": f"Earned the **{friendly_name}** badge for health achievements.",
                "raw": row
            })
            
    ecg_df = find_df_by_keyword(normalized, "ecg")
    if ecg_df is not None and not ecg_df.empty:
        for _, row_pd in ecg_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            hr = get_col_val(row, ["mean_heart_rate"])
            hr_str = f" {int(float(hr))} BPM" if hr is not None and not pd.isna(hr) else ""
            
            events.append({
                "datetime": dt,
                "title": "ECG Recording completed",
                "category": "Cardiovascular",
                "emoji": "🩺",
                "color": "#ef4444",
                "description": f"Electrocardiogram recording completed.{f' Mean heart rate was **{hr_str}**.' if hr_str else ''}",
                "raw": row
            })
            
    weight_df = find_df_by_keyword(normalized, "weight")
    if weight_df is not None and not weight_df.empty:
        for _, row_pd in weight_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            w = get_col_val(row, ["weight"])
            bmi = get_col_val(row, ["bmi"])
            desc_parts = []
            if w is not None and not pd.isna(w):
                desc_parts.append(f"⚖️ **Weight:** {float(w):.1f} kg")
            if bmi is not None and not pd.isna(bmi) and float(bmi) > 0:
                desc_parts.append(f"📊 **BMI:** {float(bmi):.1f}")
            
            events.append({
                "datetime": dt,
                "title": "Body Weight Logged",
                "category": "Body / Profile",
                "emoji": "⚖️",
                "color": "#10b981",
                "description": " | ".join(desc_parts) if desc_parts else "Weight log recorded.",
                "raw": row
            })
            
    alert_df = find_df_by_keyword(normalized, "alerted_heart_rate")
    if alert_df is not None and not alert_df.empty:
        for _, row_pd in alert_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            hr = get_col_val(row, ["heart_rate"])
            events.append({
                "datetime": dt,
                "title": f"Heart Rate Alert: {int(float(hr))} BPM",
                "category": "Cardiovascular",
                "emoji": "⚠️",
                "color": "#b91c1c",
                "description": f"High or low heart rate alert triggered. Wearable sensor registered **{int(float(hr))} BPM**.",
                "raw": row
            })
            
    for ev in events:
        if hasattr(ev["datetime"], "to_pydatetime"):
            ev["datetime"] = ev["datetime"].to_pydatetime()
        if ev["datetime"].tzinfo is not None:
            ev["datetime"] = ev["datetime"].replace(tzinfo=None)
            
    events = sorted(events, key=lambda x: x["datetime"], reverse=True)
    return events


def plot_dataset_chart(dtype: str, df: pd.DataFrame, display_name: str) -> None:
    if df.empty:
        st.warning("This dataset contains no rows of data.")
        return

    time_col = None
    for col in ["start_datetime", "start_time", "create_time", "update_time"]:
        if col in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass
            time_col = col
            break

    if time_col and df[time_col].notna().any():
        df_sorted = df.dropna(subset=[time_col]).sort_values(time_col)
    else:
        df_sorted = df

    layout_args = dict(
        template="plotly_white",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    if "weight" in dtype.lower() and "weight" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y="weight",
            markers=True,
            title=f"{display_name} Trend (kg)",
            color_discrete_sequence=[HEALTH_COLORS["primary"]]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "pedometer" in dtype.lower() or "step_daily_trend" in dtype.lower():
        step_col = None
        for col in ["count", "step_count", "steps"]:
            if col in df.columns:
                step_col = col
                break
        if step_col:
            fig = px.bar(
                df_sorted,
                x=time_col or df_sorted.index,
                y=step_col,
                title=f"{display_name} (Daily Steps)",
                color_discrete_sequence=[HEALTH_COLORS["accent"]]
            )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)

    elif "sleep" in dtype.lower() and not "sleep_stage" in dtype.lower():
        sleep_col = None
        for col in ["efficiency", "sleep_duration", "duration"]:
            if col in df.columns:
                sleep_col = col
                break
        if sleep_col:
            fig = px.bar(
                df_sorted,
                x=time_col or df_sorted.index,
                y=sleep_col,
                title=f"{display_name} ({sleep_col.replace('_', ' ').capitalize()})",
                color_discrete_sequence=[HEALTH_COLORS["secondary"]]
            )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)

    elif "sleep_stage" in dtype.lower() and "stage" in df.columns:
        fig = px.bar(
            df_sorted.tail(1000),
            x=time_col or df_sorted.index,
            y="stage",
            title="Sleep Stages (Timeline Segment)",
            color="stage",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "heart_rate" in dtype.lower():
        hr_col = "heart_rate" if "heart_rate" in df.columns else ("pulse" if "pulse" in df.columns else None)
        if hr_col:
            if "min" in df.columns and "max" in df.columns:
                fig = px.line(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=["heart_rate", "min", "max"] if "heart_rate" in df.columns else ["min", "max"],
                    title=f"{display_name} range over time (BPM)",
                    color_discrete_sequence=["#ef4444", "#3b82f6", "#f59e0b"]
                )
            else:
                fig = px.scatter(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=hr_col,
                    title=f"{display_name} (BPM)",
                    color_discrete_sequence=["#ef4444"],
                    opacity=0.6
                )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)

    elif "blood_pressure" in dtype.lower() and "systolic" in df.columns and "diastolic" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y=["systolic", "diastolic"],
            title=f"{display_name} (mmHg)",
            color_discrete_sequence=["#ef4444", "#3b82f6"]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "oxygen_saturation" in dtype.lower() and "spo2" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y="spo2",
            markers=True,
            title=f"{display_name} (%)",
            color_discrete_sequence=["#06b6d4"]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "stress" in dtype.lower() and "score" in df.columns:
        fig = px.bar(
            df_sorted,
            x=time_col or df_sorted.index,
            y="score",
            title=f"{display_name} (Stress Score)",
            color_discrete_sequence=["#a855f7"]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "water_intake" in dtype.lower() and "amount" in df.columns:
        fig = px.bar(
            df_sorted,
            x=time_col or df_sorted.index,
            y="amount",
            title=f"{display_name} (mL)",
            color_discrete_sequence=["#3b82f6"]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    else:
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and col not in ["time_offset", "deviceuuid", "pkg_name", "custom"]]
        if numeric_cols:
            st.caption("No custom chart defined for this dataset. Plot any numeric column:")
            selected_num_col = st.selectbox("Select column to plot", numeric_cols, key=f"sel_num_{dtype}")
            if len(df_sorted) < 50:
                fig = px.bar(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=selected_num_col,
                    title=f"{display_name} - {selected_num_col}",
                    color_discrete_sequence=[HEALTH_COLORS["primary"]]
                )
            else:
                fig = px.line(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=selected_num_col,
                    title=f"{display_name} - {selected_num_col}",
                    color_discrete_sequence=[HEALTH_COLORS["primary"]]
                )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numerical fields available to plot.")


def find_df_by_keyword(normalized: dict, keyword: str) -> pd.DataFrame | None:
    for fname, df in normalized.get("dataframes", {}).items():
        if keyword in fname.lower():
            return df
    return None


def find_df_by_datatype(normalized: dict, datatype: str) -> pd.DataFrame | None:
    for fname, df in normalized.get("dataframes", {}).items():
        if data_type_from_filename(fname) == datatype:
            return df
    return None




def init_mock_data():
    if "related_persons" not in st.session_state:
        st.session_state.related_persons = [
            RelatedPerson(
                id="rp-doctor-jenkins",
                patient_id="patient-self",
                relationship=ProxyRelationship.CARER,
                is_anonymous=False,
                description="Dr. Sarah Jenkins (GP, Sydney Medical Centre)"
            ),
            RelatedPerson(
                id="rp-carer-john",
                patient_id="patient-self",
                relationship=ProxyRelationship.GUARDIAN,
                is_anonymous=False,
                description="John Doe (Designated Carer / Father)"
            ),
            RelatedPerson(
                id="rp-partner-safety",
                patient_id="patient-self",
                relationship=ProxyRelationship.PARTNER,
                is_anonymous=True,
                description="Partner (Anonymous Contact for safety planning)"
            )
        ]
        
    if "proxy_consents" not in st.session_state:
        st.session_state.proxy_consents = [
            ProxyConsent(
                id="consent-gp",
                patient_id="patient-self",
                proxy_id="rp-doctor-jenkins",
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                audit_silenced=False
            ),
            ProxyConsent(
                id="consent-carer-mha",
                patient_id="patient-self",
                proxy_id="rp-carer-john",
                legal_basis=LegalBasis.MHA_NOMINATED,
                privacy_mode=PrivacyMode.MODE_C_SHARED,
                audit_silenced=False
            ),
            ProxyConsent(
                id="consent-partner-safety",
                patient_id="patient-self",
                proxy_id="rp-partner-safety",
                legal_basis=LegalBasis.SAFETY_OVERRIDE,
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                audit_silenced=True
            )
        ]
        
    if "psychiatric_observations" not in st.session_state:
        st.session_state.psychiatric_observations = [
            {
                "id": "psych-obs-1",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=5, hours=3),
                "context": ObservationContext.SELF_REPORTED,
                "recorded_by_proxy_id": None,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "symptom_code": "48694002",
                "symptom_name": "Anxiety / Panic Attack",
                "notes": "Felt sudden chest tightness and racing thoughts during project standup.",
                "linked_medication_id": None
            },
            {
                "id": "psych-obs-2",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=3, hours=1),
                "context": ObservationContext.CARER_OBSERVED,
                "recorded_by_proxy_id": "rp-carer-john",
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "symptom_code": "58596002",
                "symptom_name": "Agitation / Pacing",
                "notes": "Observed significant pacing and irritability in the evening after work.",
                "linked_medication_id": None
            },
            {
                "id": "psych-obs-3",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=1, hours=4),
                "context": ObservationContext.CLINICIAN_OBSERVED,
                "recorded_by_proxy_id": "rp-doctor-jenkins",
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "symptom_code": "366979004",
                "symptom_name": "Depressed mood",
                "notes": "Patient reports flat affect and low energy. Adjusted dosage of sertraline.",
                "linked_medication_id": "med-sertraline"
            }
        ]
        
    if "location_events" not in st.session_state:
        st.session_state.location_events = [
            {
                "id": "geo-1",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=5, hours=8),
                "latitude": -33.8688,
                "longitude": 151.2093,
                "category": SemanticCategory.HOME,
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "linked_symptom_id": None
            },
            {
                "id": "geo-2",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=5, hours=3),
                "latitude": -33.8568,
                "longitude": 151.2153,
                "category": SemanticCategory.WORK,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "linked_symptom_id": "psych-obs-1"
            },
            {
                "id": "geo-3",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=3, hours=4),
                "latitude": -33.8824,
                "longitude": 151.2012,
                "category": SemanticCategory.MEDICAL_FACILITY,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "linked_symptom_id": "psych-obs-3"
            },
            {
                "id": "geo-4",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=1),
                "latitude": -33.8915,
                "longitude": 151.2767,
                "category": SemanticCategory.TRAVEL,
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "linked_symptom_id": None
            }
        ]

    if "ons4_responses" not in st.session_state:
        st.session_state.ons4_responses = [
            {
                "date": datetime.now() - timedelta(days=5),
                "life_satisfaction": 6,
                "worthwhile": 7,
                "happiness": 5,
                "anxiety": 8
            },
            {
                "date": datetime.now() - timedelta(days=3),
                "life_satisfaction": 7,
                "worthwhile": 7,
                "happiness": 6,
                "anxiety": 5
            },
            {
                "date": datetime.now() - timedelta(days=1),
                "life_satisfaction": 8,
                "worthwhile": 8,
                "happiness": 7,
                "anxiety": 3
            }
        ]

    if "medication_administrations" not in st.session_state:
        st.session_state.medication_administrations = [
            {
                "id": "med-sertraline",
                "patient_id": "patient-self",
                "medication_name": "Sertraline 50mg",
                "status": AdherenceStatus.TAKEN,
                "effective_time": datetime.now() - timedelta(days=1, hours=8),
                "quality_tag": MedDataQualityTag.EXACT,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED
            },
            {
                "id": "med-sertraline-missed",
                "patient_id": "patient-self",
                "medication_name": "Sertraline 50mg",
                "status": AdherenceStatus.MISSED,
                "effective_time": datetime.now() - timedelta(days=2, hours=8),
                "quality_tag": MedDataQualityTag.SELF_REPORT,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "notes": "Forgot due to early morning meeting"
            }
        ]

    if "life_events" not in st.session_state:
        st.session_state.life_events = [
            {
                "id": "le-job-loss-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.JOB_LOSS,
                "title": "Redundancy from Employer",
                "description": "Made redundant after restructure. Position eliminated with 4 weeks notice. Unfair dismissal claim lodged with Fair Work Commission.",
                "trigger_date": datetime.now() - timedelta(days=90),
                "end_date": None,
                "severity": SeverityLevel.MODERATE,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "recorded_by_proxy_id": None,
                "involved_parties": [],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.EMPLOYMENT, "severity": SeverityLevel.HIGH, "description": "Loss of stable full-time employment"},
                    {"dimension": WellbeingDimension.INCOME_WEALTH, "severity": SeverityLevel.HIGH, "description": "Immediate 60% income reduction"},
                    {"dimension": WellbeingDimension.HEALTH_MENTAL, "severity": SeverityLevel.MODERATE, "description": "Increased anxiety and sleep disturbance"},
                    {"dimension": WellbeingDimension.SUBJECTIVE_WELLBEING, "severity": SeverityLevel.MODERATE, "description": "Reduced life satisfaction and self-worth"},
                ],
                "supporting_documents": [
                    {"id": "doc-1", "title": "Termination Letter", "category": DocumentCategory.PROFESSIONAL, "document_uri": "vault://docs/termination-letter.pdf.enc", "jurisdiction": "AU-NSW"},
                    {"id": "doc-2", "title": "Centrelink JobSeeker Claim", "category": DocumentCategory.GOVERNMENT, "document_uri": "vault://docs/centrelink-claim.pdf.enc", "jurisdiction": "AU-FED"},
                    {"id": "doc-3", "title": "Fair Work Commission Application", "category": DocumentCategory.LEGAL, "document_uri": "vault://docs/fwc-application.pdf.enc", "jurisdiction": "AU-FED"},
                ],
                "recovery_indicators": [
                    {"id": "rec-1", "description": "Register with Centrelink / JobSeeker", "status": RecoveryStatus.RESOLVED, "linked_service": "Services Australia"},
                    {"id": "rec-2", "description": "Lodge Fair Work Commission unfair dismissal claim", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "Fair Work Commission"},
                    {"id": "rec-3", "description": "Enrol in retraining program (TAFE Digital Skills)", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "TAFE NSW"},
                    {"id": "rec-4", "description": "Secure new employment or contract work", "status": RecoveryStatus.NOT_STARTED, "linked_service": None},
                ],
                "linked_psych_observation_ids": ["psych-obs-1"],
                "linked_medication_ids": [],
                "maslow_layer": MaslowLayer.SAFETY,
                "data_quality_tag": LifeDataQualityTag.EXACT,
                "notes": "Discussing options with employment lawyer. GP has noted increased anxiety since redundancy."
            },
            {
                "id": "le-separation-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.DIVORCE_SEPARATION,
                "title": "Relationship Separation",
                "description": "Separation from long-term partner. Property settlement pending. Parenting orders being negotiated through mediation.",
                "trigger_date": datetime.now() - timedelta(days=60),
                "end_date": None,
                "severity": SeverityLevel.HIGH,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "recorded_by_proxy_id": None,
                "involved_parties": ["rp-partner-safety"],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.SOCIAL_CONNECTIONS, "severity": SeverityLevel.HIGH, "description": "Primary relationship breakdown; social network disruption"},
                    {"dimension": WellbeingDimension.HOUSING, "severity": SeverityLevel.MODERATE, "description": "Relocation required; temporary accommodation"},
                    {"dimension": WellbeingDimension.INCOME_WEALTH, "severity": SeverityLevel.MODERATE, "description": "Asset division and legal costs"},
                    {"dimension": WellbeingDimension.HEALTH_MENTAL, "severity": SeverityLevel.HIGH, "description": "Depressed mood and grief response"},
                    {"dimension": WellbeingDimension.RIGHTS_LEGAL, "severity": SeverityLevel.MODERATE, "description": "Parenting orders and property settlement negotiations"},
                ],
                "supporting_documents": [
                    {"id": "doc-4", "title": "Family Dispute Resolution Certificate", "category": DocumentCategory.LEGAL, "document_uri": "vault://docs/fdr-cert.pdf.enc", "jurisdiction": "AU-FED"},
                    {"id": "doc-5", "title": "Temporary Rental Agreement", "category": DocumentCategory.HOUSING, "document_uri": "vault://docs/rental-agreement.pdf.enc", "jurisdiction": "AU-NSW"},
                ],
                "recovery_indicators": [
                    {"id": "rec-5", "description": "Attend Family Dispute Resolution (mediation)", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "Relationships Australia NSW"},
                    {"id": "rec-6", "description": "Secure stable housing", "status": RecoveryStatus.IN_PROGRESS, "linked_service": None},
                    {"id": "rec-7", "description": "Finalise property settlement", "status": RecoveryStatus.NOT_STARTED, "linked_service": "Legal Aid NSW"},
                    {"id": "rec-8", "description": "Establish regular counselling", "status": RecoveryStatus.STABLE, "linked_service": "Beyond Blue"},
                ],
                "linked_psych_observation_ids": ["psych-obs-3"],
                "linked_medication_ids": ["med-sertraline"],
                "maslow_layer": MaslowLayer.BELONGING,
                "data_quality_tag": LifeDataQualityTag.SELF_REPORT,
                "notes": "Mediation progressing slowly. Counsellor reports patient is engaging well with sessions."
            },
            {
                "id": "le-housing-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.HOMELESSNESS,
                "title": "Housing Instability (Post-Separation)",
                "description": "Temporary accommodation after separation. Couch-surfing with family while seeking affordable rental in Sydney market.",
                "trigger_date": datetime.now() - timedelta(days=45),
                "end_date": datetime.now() - timedelta(days=15),
                "severity": SeverityLevel.CRITICAL,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "recorded_by_proxy_id": "rp-carer-john",
                "involved_parties": ["rp-carer-john"],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.HOUSING, "severity": SeverityLevel.CRITICAL, "description": "No permanent address for 30 days"},
                    {"dimension": WellbeingDimension.SAFETY, "severity": SeverityLevel.HIGH, "description": "Increased vulnerability without stable shelter"},
                    {"dimension": WellbeingDimension.HEALTH_PHYSICAL, "severity": SeverityLevel.MODERATE, "description": "Disrupted sleep and nutrition routines"},
                    {"dimension": WellbeingDimension.EMPLOYMENT, "severity": SeverityLevel.LOW, "description": "Difficulty attending interviews without stable address"},
                ],
                "supporting_documents": [
                    {"id": "doc-6", "title": "Tenancy Termination Notice", "category": DocumentCategory.HOUSING, "document_uri": "vault://docs/tenancy-termination.pdf.enc", "jurisdiction": "AU-NSW"},
                ],
                "recovery_indicators": [
                    {"id": "rec-9", "description": "Apply for emergency housing through DCJ Housing", "status": RecoveryStatus.RESOLVED, "linked_service": "DCJ Housing NSW"},
                    {"id": "rec-10", "description": "Secure private rental", "status": RecoveryStatus.RESOLVED, "linked_service": None},
                ],
                "linked_psych_observation_ids": ["psych-obs-2"],
                "linked_medication_ids": [],
                "maslow_layer": MaslowLayer.PHYSIOLOGICAL,
                "data_quality_tag": LifeDataQualityTag.SELF_REPORT,
                "notes": "Resolved — secured rental. Father (John) provided support during this period."
            }
        ]

    if "case_files" not in st.session_state:
        st.session_state.case_files = [
            CaseFile(
                id="case-1",
                patient_id="patient-self",
                title="Suspected Sleep Apnea Evaluation",
                category=CaseCategory.SUSPECTED_CONDITION,
                status=CaseStatus.SUSPECTED,
                hypothesis_or_claim="Patient experiences excessive daytime sleepiness, chronic loud snoring, and witnessed breathing pauses during sleep.",
                date_created=datetime.now() - timedelta(days=14),
                date_updated=datetime.now() - timedelta(days=2),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                linked_datatypes=["com.samsung.shealth.sleep", "com.samsung.shealth.sleep_snoring"],
                tasks=[
                    CaseTask(id="task-1-1", title="Log sleep & snoring data for 14 nights", description="Gather evidence using Samsung Health wearable sensors", is_completed=True),
                    CaseTask(id="task-1-2", title="Schedule GP appointment for review", description="Discuss symptoms and snoring log with GP", is_completed=False),
                    CaseTask(id="task-1-3", title="Obtain a referral for an overnight Sleep Study", description="Get a referral to a specialist sleep clinic", is_completed=False),
                ],
                notes="Snoring events have been steadily rising over the last month according to wearable data."
            ),
            CaseFile(
                id="case-2",
                patient_id="patient-self",
                title="Routine Sexual Health / STD Screening",
                category=CaseCategory.ROUTINE_CHECK,
                status=CaseStatus.ACTIVE,
                hypothesis_or_claim="Annual routine sexual health screening/check-up.",
                date_created=datetime.now() - timedelta(days=3),
                date_updated=datetime.now() - timedelta(days=3),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                tasks=[
                    CaseTask(id="task-2-1", title="Book clinic appointment", description="Sydney Sexual Health Centre or local GP", is_completed=False),
                    CaseTask(id="task-2-2", title="Undergo pathology tests", description="Complete blood and urine collection", is_completed=False),
                ]
            ),
            CaseFile(
                id="case-3",
                patient_id="patient-self",
                title="Interval Blood Test Monitoring (Lipids & Vit D)",
                category=CaseCategory.INTERVAL_TEST,
                status=CaseStatus.MONITORING,
                hypothesis_or_claim="Quarterly lipid panel and Vitamin D test to monitor cholesterol levels and supplementation efficacy.",
                date_created=datetime.now() - timedelta(days=60),
                date_updated=datetime.now() - timedelta(days=1),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                tasks=[
                    CaseTask(id="task-3-1", title="Obtain pathology request form from GP", description="Ensure lipids and 25-hydroxyvitamin D are ticked", is_completed=True),
                    CaseTask(id="task-3-2", title="Attend Laverty Pathology collection centre", description="Fast for 12 hours prior to lipid panel", is_completed=False),
                ]
            )
        ]

    if "diagnostic_reports" not in st.session_state:
        st.session_state.diagnostic_reports = [
            DiagnosticReport(
                id="report-lipid-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=14),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/laverty-lipid-panel-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-chol-1",
                        test_name="Total Cholesterol",
                        value=6.1,
                        unit="mmol/L",
                        reference_range_high=5.5,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-trig-1",
                        test_name="Triglycerides",
                        value=1.8,
                        unit="mmol/L",
                        reference_range_high=2.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-hdl-1",
                        test_name="HDL Cholesterol",
                        value=1.2,
                        unit="mmol/L",
                        reference_range_low=1.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-ldl-1",
                        test_name="LDL Cholesterol",
                        value=4.1,
                        unit="mmol/L",
                        reference_range_high=3.5,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    )
                ]
            ),
            DiagnosticReport(
                id="report-biochem-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=1),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/dhm-glucose-hba1c-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-glucose-1",
                        test_name="Fasting Blood Glucose",
                        value=5.4,
                        unit="mmol/L",
                        reference_range_low=3.0,
                        reference_range_high=5.4,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-hba1c-1",
                        test_name="HbA1c (Glycated Hb)",
                        value=5.6,
                        unit="%",
                        reference_range_high=6.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    )
                ]
            ),
            DiagnosticReport(
                id="report-std-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=3),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/sshc-screen-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_A_STRICT, # Default Strict Privacy
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-hiv-1",
                        test_name="HIV Ag/Ab Screen",
                        value=0.08,
                        unit="Index",
                        reference_range_high=0.90,
                        privacy_mode=PrivacyMode.MODE_A_STRICT
                    ),
                    PathologyObservation(
                        id="obs-chlamydia-1",
                        test_name="Chlamydia Ur PCR",
                        value=0.0,
                        unit="PCR",
                        reference_range_high=0.0,
                        privacy_mode=PrivacyMode.MODE_A_STRICT
                    )
                ]
            )
        ]

    if "directory_actors" not in st.session_state:
        st.session_state.directory_actors = [
            Actor(
                id="actor-laverty-pathology",
                actor_type=ActorType.ORGANIZATION,
                name="Laverty Pathology",
                qualifications=["NATA Accredited Lab #12345", "ISO 15189 Accreditation"],
                roles=["Diagnostic Provider", "Pathology Laboratory"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:laverty.com.au:labs"
            ),
            Actor(
                id="actor-gp-sarah",
                actor_type=ActorType.PRACTITIONER,
                name="Dr. Sarah Jenkins",
                organization="Sydney Medical Centre",
                qualifications=["M.B.B.S.", "AHPRA Registration MED00012", "FRACGP"],
                roles=["Primary Care Physician", "General Practitioner"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:sydneymedical.com.au:practitioners:sjenkins"
            ),
            Actor(
                id="actor-carer-john",
                actor_type=ActorType.DELEGATE,
                name="John Doe",
                qualifications=["Nominated Guardian Authority (MHA NSW)"],
                roles=["Designated Carer", "Guardian"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:key:z6MkpTHR8VNsBxazR24z168m"
            ),
            Actor(
                id="actor-audit-ai",
                actor_type=ActorType.SYNTHETIC_AGENT,
                name="Clinical Compliance Auditor v1",
                qualifications=["AI Audit Model: Claude-3.5-Sonnet-v2", "ISO 27001 Compliant Agent Profile"],
                roles=["Clinical Claims Auditor", "Automated Validation Engine"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:episteme.health:agents:audit-ai"
            )
        ]

    if "delegation_rules" not in st.session_state:
        st.session_state.delegation_rules = [
            DelegationRule(
                id="rule-laverty-1",
                patient_id="patient-self",
                actor_id="actor-laverty-pathology",
                granted_roles=["log_pathology", "publish_observations"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                allowed_record_types=["PathologyObservation", "DiagnosticReport"],
                is_active=True
            ),
            DelegationRule(
                id="rule-gp-1",
                patient_id="patient-self",
                actor_id="actor-gp-sarah",
                granted_roles=["read_clinical_records", "verify_claims", "write_referrals"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                linked_case_ids=["case-1", "case-3"], # Referral evaluation cases
                is_active=True
            ),
            DelegationRule(
                id="rule-carer-1",
                patient_id="patient-self",
                actor_id="actor-carer-john",
                granted_roles=["view_wellbeing", "view_timeline", "receive_alerts"],
                legal_basis=LegalBasis.MHA_NOMINATED,
                privacy_mode_limit=PrivacyMode.MODE_C_SHARED,
                restricted_records=["PsychiatricObservation", "MedicationAdministration"], # restricted for patient safety/privacy
                is_active=True
            ),
            DelegationRule(
                id="rule-audit-1",
                patient_id="patient-self",
                actor_id="actor-audit-ai",
                granted_roles=["read_diagnostics", "audit_clinical_claims"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                restricted_records=["PsychiatricObservation"], # Explicitly block AI agent from psychiatric logs
                is_active=True
            )
        ]



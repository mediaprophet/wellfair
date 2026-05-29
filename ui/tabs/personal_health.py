import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import textwrap

from ui.utils import (
    HEALTH_COLORS,
    get_dashboard_metrics,
    extract_timeline_events,
    plot_dataset_chart,
    find_df_by_keyword,
    find_df_by_datatype,
    render_kpi_row,
)
from src.sleep_analytics import (
    SleepMetrics, SleepTrendAnalysis, SleepInsights, SleepPatterns
)

def render_personal_health(dark_mode: bool, normalized: dict):
    tab_dashboard, = st.tabs(["Personal Health Dashboard"])
    
    with tab_dashboard:
        st.markdown("## ❤️ Personal Health Dashboard")
        metrics = get_dashboard_metrics(normalized)

        kpi_configs = [
            ("steps", "Steps Tracker", "👣", "#3b82f6"),
            ("sleep", "Sleep Summary", "💤", "#8b5cf6"),
            ("weight", "Body Weight", "⚖️", "#10b981"),
            ("heart_rate", "Heart Rate", "💓", "#ef4444")
        ]

        kpis = []
        for key, title, emoji, color in kpi_configs:
            m_data = metrics.get(key, {"value": "No Data", "subtitle": "N/A"})
            kpis.append({
                "title": title,
                "value": str(m_data["value"]),
                "subtitle": m_data["subtitle"],
                "emoji": emoji,
                "color": color,
            })

        render_kpi_row(kpis, dark_mode=dark_mode)
                
        st.markdown("### 📈 Core Health Trends")
        
        view_mode = st.radio(
            "View Mode",
            options=["Interactive Timeline View (Knightlab Style) 📜", "Interactive Charts Grid View 📊"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if "Timeline" in view_mode:
            all_events = extract_timeline_events(normalized)
            if not all_events:
                st.info("No health events found (workouts, badges, ECGs, weight logs, or alerts) to construct a timeline.")
            else:
                with st.expander("🛠️ Timeline Filter", expanded=True):
                    st.markdown("**Filter Datasets**")
                    categories = ["Activity", "Achievement", "Cardiovascular", "Body / Profile"]
                    cat_labels = {
                        "Activity": "Workouts 🏃",
                        "Achievement": "Achievements 🏅",
                        "Cardiovascular": "Cardiovascular (ECG/Alerts) 🩺",
                        "Body / Profile": "Body / Weight Logs ⚖️"
                    }
                    
                    counts = {cat: 0 for cat in categories}
                    for ev in all_events:
                        cat = ev["category"]
                        if cat in counts:
                            counts[cat] += 1
                            
                    selected_cats = []
                    cols = st.columns(4)
                    for i, (cat, label) in enumerate(cat_labels.items()):
                        with cols[i]:
                            cnt = counts.get(cat, 0)
                            if cnt > 0:
                                is_checked = st.checkbox(f"{label} ({cnt})", value=True, key=f"filter_cat_{cat}")
                                if is_checked:
                                    selected_cats.append(cat)
                            else:
                                st.caption(f"No {label} data available")
                                
                filtered_events = [ev for ev in all_events if ev["category"] in selected_cats]
                
                if not filtered_events:
                    st.warning("No events match the selected filters.")
                else:
                    active_subplots = []
                    
                    if "Body / Profile" in selected_cats:
                        w_df = find_df_by_datatype(normalized, "com.samsung.health.weight")
                        if w_df is not None and not w_df.empty: active_subplots.append(("Weight (kg)", w_df, "weight", "#10b981"))
                    if "Cardiovascular" in selected_cats:
                        hr_df = find_df_by_datatype(normalized, "com.samsung.shealth.tracker.heart_rate")
                        if hr_df is not None and not hr_df.empty:
                            hr_col = "heart_rate" if "heart_rate" in hr_df.columns else "pulse"
                            active_subplots.append(("Heart Rate (BPM)", hr_df, hr_col, "#ef4444"))
                    if "Activity" in selected_cats:
                        s_df = find_df_by_datatype(normalized, "com.samsung.shealth.tracker.pedometer_day_summary")
                        if s_df is None or s_df.empty:
                            s_df = find_df_by_datatype(normalized, "com.samsung.shealth.step_daily_trend")
                        if s_df is not None and not s_df.empty:
                            s_col = "count" if "count" in s_df.columns else "step_count"
                            active_subplots.append(("Steps", s_df, s_col, "#3b82f6"))
                            
                    rows = len(active_subplots) + 1
                    row_titles = ["Discrete Events"] + [title for title, df, col, color in active_subplots]
                    fig = make_subplots(
                        rows=rows, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.05,
                        row_titles=row_titles
                    )
                    
                    # Row 1: Events
                    x_events = [ev["datetime"] for ev in filtered_events]
                    y_events = [0] * len(filtered_events)
                    
                    hover_texts = []
                    for ev in filtered_events:
                        clean_desc = str(ev['description']).replace('\n', '<br>')
                        hover_texts.append(f"<b>{ev['emoji']} {ev['title']}</b><br>{clean_desc}<br><i>{ev['datetime'].strftime('%Y-%m-%d %H:%M')}</i>")
                        
                    colors = [ev["color"] for ev in filtered_events]
                    
                    fig.add_trace(go.Scatter(
                        x=x_events, y=y_events, 
                        mode='markers',
                        marker=dict(size=24, color=colors, opacity=0.75, line=dict(width=3, color='rgba(255,255,255,0.8)')),
                        text=hover_texts,
                        hoverinfo='text',
                        name="Events",
                        showlegend=False
                    ), row=1, col=1)
                    
                    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)
                    
                    # Subsequent rows for continuous data
                    for idx, (title, df, val_col, color) in enumerate(active_subplots):
                        r = idx + 2
                        time_col = next((c for c in ["start_datetime", "start_time", "create_time"] if c in df.columns), None)
                        if time_col and val_col in df.columns:
                            if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                            
                            df_sorted = df.dropna(subset=[time_col, val_col]).sort_values(time_col)
                            
                            fig.add_trace(go.Scatter(
                                x=df_sorted[time_col], y=df_sorted[val_col],
                                mode='lines',
                                line=dict(color=color, width=2),
                                name=title,
                                showlegend=False
                            ), row=r, col=1)
                            
                    fig.update_layout(
                        height=200 + (150 * len(active_subplots)),
                        margin=dict(l=20, r=20, t=40, b=20),
                        hovermode="x unified",
                        template="plotly_dark" if dark_mode else "plotly_white",
                    )
                    
                    fig.update_xaxes(rangeslider_visible=True, row=rows, col=1)

                    st.plotly_chart(fig, use_container_width=True)
                
        else:
            c1, c2 = st.columns(2)
            weight_df = find_df_by_keyword(normalized, "weight")
            sleep_df = find_df_by_keyword(normalized, "sleep")
            steps_df = find_df_by_keyword(normalized, "pedometer")
            hr_df = find_df_by_keyword(normalized, "heart_rate")
            bp_df = find_df_by_keyword(normalized, "blood_pressure")
            
            with c1:
                if weight_df is not None and not weight_df.empty:
                    plot_dataset_chart("com.samsung.health.weight", weight_df, "Body Weight Trend", dark_mode)
                else:
                    st.info("No Weight data found for dashboard trend.")
                    
                if steps_df is not None and not steps_df.empty:
                    plot_dataset_chart("com.samsung.shealth.tracker.pedometer_day_summary", steps_df, "Daily Step Count", dark_mode)
                else:
                    st.info("No Steps data found for dashboard trend.")
                    
            with c2:
                if sleep_df is not None and not sleep_df.empty:
                    plot_dataset_chart("com.samsung.shealth.sleep", sleep_df, "Sleep Duration", dark_mode)
                else:
                    st.info("No Sleep data found for dashboard trend.")
                    
                if hr_df is not None and not hr_df.empty:
                    plot_dataset_chart("com.samsung.health.heart_rate", hr_df, "Heart Rate", dark_mode)
                elif bp_df is not None and not bp_df.empty:
                    plot_dataset_chart("com.samsung.shealth.blood_pressure", bp_df, "Blood Pressure", dark_mode)
                else:
                    st.info("No Heart Rate or Blood Pressure data found for dashboard trend.")


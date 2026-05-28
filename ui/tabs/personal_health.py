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
    find_df_by_datatype
)
from src.sleep_analytics import (
    SleepMetrics, SleepTrendAnalysis, SleepInsights, SleepPatterns
)

def render_personal_health(dark_mode: bool, normalized: dict):
    tab_dashboard, tab_sleep = st.tabs([
        "Personal Health Dashboard",
        "Sleep Analytics 💤"
    ])
    
    with tab_dashboard:
        st.markdown("## ❤️ Personal Health Dashboard")
        metrics = get_dashboard_metrics(normalized)
        cols = st.columns(4)
        
        kpi_configs = [
            ("steps", "Steps Tracker", "👣", "#3b82f6"),
            ("sleep", "Sleep Summary", "💤", "#8b5cf6"),
            ("weight", "Body Weight", "⚖️", "#10b981"),
            ("heart_rate", "Heart Rate", "💓", "#ef4444")
        ]
        
        for i, (key, title, emoji, color) in enumerate(kpi_configs):
            with cols[i]:
                m_data = metrics.get(key, {"value": "No Data", "subtitle": "N/A"})
                st.markdown(
                    textwrap.dedent(f"""
                    <div class="premium-card" style="border-left: 5px solid {color};">
                        <div class="flex-center">
                            <div class="icon-circle" style="background: {color}22; color: {color};">
                                {emoji}
                            </div>
                            <div>
                                <div class="metric-title">{title}</div>
                                <div class="metric-value">{m_data["value"]}</div>
                                <div class="metric-subtitle">{m_data["subtitle"]}</div>
                            </div>
                        </div>
                    </div>
                    """),
                    unsafe_allow_html=True
                )
                
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
                    plot_dataset_chart("com.samsung.health.weight", weight_df, "Body Weight Trend")
                else:
                    st.info("No Weight data found for dashboard trend.")
                    
                if steps_df is not None and not steps_df.empty:
                    plot_dataset_chart("com.samsung.shealth.tracker.pedometer_day_summary", steps_df, "Daily Step Count")
                else:
                    st.info("No Steps data found for dashboard trend.")
                    
            with c2:
                if sleep_df is not None and not sleep_df.empty:
                    plot_dataset_chart("com.samsung.shealth.sleep", sleep_df, "Sleep Duration")
                else:
                    st.info("No Sleep data found for dashboard trend.")
                    
                if hr_df is not None and not hr_df.empty:
                    plot_dataset_chart("com.samsung.health.heart_rate", hr_df, "Heart Rate")
                elif bp_df is not None and not bp_df.empty:
                    plot_dataset_chart("com.samsung.shealth.blood_pressure", bp_df, "Blood Pressure")
                else:
                    st.info("No Heart Rate or Blood Pressure data found for dashboard trend.")

    with tab_sleep:
        st.markdown("## 💤 World-Class Sleep Analytics Dashboard")
        
        sleep_df = find_df_by_datatype(normalized, "com.samsung.shealth.sleep")
        sleep_stage_df = find_df_by_datatype(normalized, "com.samsung.health.sleep_stage")
        
        if sleep_df is None or sleep_df.empty:
            st.warning("📊 No sleep summary data found. Please ensure your Samsung Health export contains sleep data.")
        else:
            time_col = "start_datetime" if "start_datetime" in sleep_df.columns else "com.samsung.health.sleep.start_time"
            
            st.markdown("### 📊 Sleep Quality Summary")
            
            if time_col in sleep_df.columns:
                sleep_data = sleep_df.copy()
                if not pd.api.types.is_datetime64_any_dtype(sleep_data[time_col]):
                    sleep_data[time_col] = pd.to_datetime(sleep_data[time_col], errors="coerce")
                sleep_data = sleep_data.dropna(subset=[time_col]).sort_values(time_col)
                
                latest_7 = sleep_data.tail(7)
                
                avg_duration = latest_7["sleep_duration"].mean() if "sleep_duration" in latest_7.columns else 0
                duration_hrs = int(avg_duration // 60)
                duration_mins = int(avg_duration % 60)
                
                avg_efficiency = latest_7["efficiency"].mean() if "efficiency" in latest_7.columns else 0
                
                consistency = SleepMetrics.calculate_consistency_score(latest_7, time_col)
                sleep_score = SleepMetrics.calculate_sleep_score(avg_duration, avg_efficiency, consistency)
                quality_level, quality_msg = SleepMetrics.classify_sleep_quality(sleep_score)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(
                        textwrap.dedent(f"""
                        <div class="premium-card" style="border-left: 5px solid #8b5cf6;">
                            <div class="metric-title">💤 Sleep Score</div>
                            <div class="metric-value" style="color: #8b5cf6;">{sleep_score:.0f}<span style="font-size: 0.5em; color: #94a3b8;">/100</span></div>
                            <div class="metric-subtitle">{quality_level}</div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.markdown(
                        textwrap.dedent(f"""
                        <div class="premium-card" style="border-left: 5px solid #3b82f6;">
                            <div class="metric-title">⏱️ Duration</div>
                            <div class="metric-value" style="color: #3b82f6;">{duration_hrs}h {duration_mins}m</div>
                            <div class="metric-subtitle">{"✅ Optimal" if 360 <= avg_duration <= 480 else "⚠️ Needs attention"}</div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                
                with col3:
                    st.markdown(
                        textwrap.dedent(f"""
                        <div class="premium-card" style="border-left: 5px solid #10b981;">
                            <div class="metric-title">🎯 Efficiency</div>
                            <div class="metric-value" style="color: #10b981;">{avg_efficiency:.0f}<span style="font-size: 0.5em; color: #94a3b8;">%</span></div>
                            <div class="metric-subtitle">{"Good" if avg_efficiency >= 85 else "Room for improvement"}</div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                
                with col4:
                    st.markdown(
                        textwrap.dedent(f"""
                        <div class="premium-card" style="border-left: 5px solid #f59e0b;">
                            <div class="metric-title">📅 Consistency</div>
                            <div class="metric-value" style="color: #f59e0b;">{consistency:.0f}<span style="font-size: 0.5em; color: #94a3b8;">%</span></div>
                            <div class="metric-subtitle">{"Regular" if consistency >= 70 else "Variable"}</div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                
                st.divider()
                
                st.markdown("### 💡 Personalized Insights")
                
                insights = SleepInsights.generate_insights(latest_7, sleep_stage_df)
                
                insight_cols = st.columns(len(insights) if len(insights) <= 3 else 3)
                for idx, insight in enumerate(insights[:3]):
                    with insight_cols[idx % 3]:
                        color = "#10b981" if insight.get("severity") == "success" else ("#f59e0b" if insight.get("severity") == "warning" else "#64748b")
                        st.markdown(
                            textwrap.dedent(f"""
                            <div class="premium-card" style="border-left: 5px solid {color};">
                                <div style="font-size: 1.5rem; margin-bottom: 8px;">{insight['icon']}</div>
                                <div style="font-weight: 600; color: {color}; margin-bottom: 4px;">{insight['title']}</div>
                                <div style="font-size: 0.85rem; color: #94a3b8;">{insight['message']}</div>
                            </div>
                            """),
                            unsafe_allow_html=True
                        )
                
                recommendations = SleepInsights.get_recommendations(sleep_score, latest_7)
                if recommendations:
                    with st.expander("📋 Personalized Recommendations", expanded=sleep_score < 75):
                        for i, rec in enumerate(recommendations, 1):
                            st.write(f"{i}. {rec}")
                
                st.divider()
                
                st.markdown("### 📈 Sleep Trends & Analysis")
                
                col_trend_left, col_trend_right = st.columns(2)
                
                with col_trend_left:
                    st.markdown("#### Duration Trend")
                    trend = SleepTrendAnalysis.detect_trend(sleep_data, "sleep_duration", time_col)
                    trend_text = f"{trend['direction']} " + {
                        "improving": "Improving - Keep it up! 🚀",
                        "declining": "Declining - Address sleep issues",
                        "stable": "Stable - Consistent sleep",
                        "insufficient_data": "Need more data"
                    }.get(trend["trend"], "")
                    
                    st.markdown(f"**Trend:** {trend_text}")
                    st.markdown(f"**Daily Change:** {trend['change_per_day']:.1f} min/night")
                
                with col_trend_right:
                    st.markdown("#### Week-over-Week Comparison")
                    wow = SleepTrendAnalysis.weekly_comparison(sleep_data, "sleep_duration", time_col)
                    if wow and "current" in wow:
                        if wow["improvement"]:
                            st.success(f"✅ **+{wow['pct_change']:.1f}%** from last week")
                        else:
                            st.warning(f"⚠️ **{wow['pct_change']:.1f}%** from last week")
                    else:
                        st.info("Insufficient data for comparison")
                
                st.markdown("### 📅 Weekly Sleep Pattern")
                
                fig_macro = make_subplots(specs=[[{"secondary_y": True}]])
                duration_hrs = sleep_data["sleep_duration"] / 60
                
                fig_macro.add_trace(
                    go.Bar(
                        x=sleep_data[time_col],
                        y=duration_hrs,
                        name="Duration (hrs)",
                        marker_color="#8b5cf6",
                        marker_opacity=0.7
                    ),
                    secondary_y=False,
                )
                
                if "efficiency" in sleep_data.columns:
                    fig_macro.add_trace(
                        go.Scatter(
                            x=sleep_data[time_col],
                            y=sleep_data["efficiency"],
                            name="Efficiency (%)",
                            mode="lines+markers",
                            line=dict(color="#10b981", width=3),
                            marker=dict(size=8)
                        ),
                        secondary_y=True,
                    )
                
                fig_macro.update_layout(
                    title="Sleep Duration vs Efficiency Trend",
                    height=450,
                    margin=dict(l=20, r=20, t=40, b=20),
                    template="plotly_dark" if dark_mode else "plotly_white",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig_macro.update_yaxes(title_text="Duration (hours)", secondary_y=False)
                if "efficiency" in sleep_data.columns:
                    fig_macro.update_yaxes(title_text="Efficiency (%)", secondary_y=True, range=[0, 100])
                
                st.plotly_chart(fig_macro, use_container_width=True)
                
                st.markdown("### 🧬 Sleep Architecture")
                
                if sleep_stage_df is not None and not sleep_stage_df.empty:
                    stage_stats = SleepPatterns.get_sleep_cycle_stats(sleep_stage_df)
                    
                    col_cycle_left, col_cycle_right = st.columns(2)
                    
                    with col_cycle_left:
                        st.markdown("#### Sleep Stage Distribution")
                        stages_df = pd.DataFrame({
                            'Stage': ['REM', 'Deep Sleep', 'Light Sleep', 'Awake'],
                            'Percentage': [
                                stage_stats['rem_percentage'],
                                stage_stats['deep_sleep_percentage'],
                                stage_stats['light_sleep_percentage'],
                                stage_stats['awake_percentage']
                            ]
                        })
                        
                        fig_pie = px.pie(
                            stages_df,
                            values='Percentage',
                            names='Stage',
                            color_discrete_map={
                                'REM': '#10b981',
                                'Deep Sleep': '#8b5cf6',
                                'Light Sleep': '#3b82f6',
                                'Awake': '#ef4444'
                            }
                        )
                        fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col_cycle_right:
                        st.markdown("#### Sleep Quality Indicators")
                        
                        metrics_cols = st.columns(2)
                        with metrics_cols[0]:
                            st.metric(
                                "REM Sleep",
                                f"{stage_stats['rem_percentage']:.1f}%",
                                "Essential for memory & emotion"
                            )
                            st.metric(
                                "Deep Sleep",
                                f"{stage_stats['deep_sleep_percentage']:.1f}%",
                                "Physical recovery & growth"
                            )
                        
                        with metrics_cols[1]:
                            st.metric(
                                "Light Sleep",
                                f"{stage_stats['light_sleep_percentage']:.1f}%",
                                "Sleep transitions"
                            )
                            st.metric(
                                "Awake Time",
                                f"{stage_stats['awake_percentage']:.1f}%",
                                f"Ideal: <5% of night"
                            )
                else:
                    st.info("🔍 Detailed sleep stage data is not available in this export.")
                
                st.divider()
                
                st.markdown("### 🔬 Individual Night Analysis")
                
                if sleep_stage_df is None or sleep_stage_df.empty:
                    st.info("Sleep stage data is not available for detailed night analysis.")
                else:
                    stage_df = sleep_stage_df.copy()
                    start_col_stage = "start_datetime" if "start_datetime" in stage_df.columns else "start_time"
                    end_col_stage = "end_datetime" if "end_datetime" in stage_df.columns else "end_time"
                    
                    if start_col_stage in stage_df.columns and end_col_stage in stage_df.columns:
                        if not pd.api.types.is_datetime64_any_dtype(stage_df[start_col_stage]):
                            stage_df[start_col_stage] = pd.to_datetime(stage_df[start_col_stage], errors="coerce")
                        if not pd.api.types.is_datetime64_any_dtype(stage_df[end_col_stage]):
                            stage_df[end_col_stage] = pd.to_datetime(stage_df[end_col_stage], errors="coerce")
                        
                        stage_df = stage_df.dropna(subset=[start_col_stage, end_col_stage]).sort_values(start_col_stage)
                        stage_df["night_date"] = (stage_df[start_col_stage] - pd.Timedelta(hours=12)).dt.date
                        available_dates = sorted(stage_df["night_date"].unique(), reverse=True)
                        
                        if available_dates:
                            selected_date = st.selectbox("Select a night to analyze:", available_dates, key="night_selector")
                            night_stages = stage_df[stage_df["night_date"] == selected_date]
                            
                            if not night_stages.empty:
                                st.markdown(f"**Sleep Architecture for {selected_date.strftime('%A, %b %d, %Y')}**")
                                
                                stage_map = {
                                    40001: ("Awake", "#ef4444", 4),
                                    40002: ("Light", "#3b82f6", 3),
                                    40003: ("Deep", "#8b5cf6", 1),
                                    40004: ("REM", "#10b981", 2)
                                }
                                
                                hypno_x = []
                                hypno_y = []
                                hypno_texts = []
                                
                                for _, row in night_stages.iterrows():
                                    stage_code = row.get("stage", 0)
                                    stage_info = stage_map.get(stage_code, ("Unknown", "#94a3b8", 0))
                                    stage_name, color, y_val = stage_info
                                    hypno_x.extend([row[start_col_stage], row[end_col_stage]])
                                    hypno_y.extend([y_val, y_val])
                                    hypno_texts.extend([stage_name, stage_name])
                                
                                fig_micro = go.Figure()
                                fig_micro.add_trace(go.Scatter(
                                    x=hypno_x, y=hypno_y,
                                    mode="lines",
                                    line=dict(color="#ffffff", width=3, shape="vh"),
                                    text=hypno_texts,
                                    hoverinfo="x+text",
                                    name="Sleep Stage",
                                    fill=None
                                ))
                                
                                for _, row in night_stages.iterrows():
                                    stage_code = row.get("stage", 0)
                                    stage_name, color, y_val = stage_map.get(stage_code, ("Unknown", "#94a3b8", 0))
                                    fig_micro.add_shape(
                                        type="rect",
                                        x0=row[start_col_stage], x1=row[end_col_stage],
                                        y0=y_val-0.4, y1=y_val+0.4,
                                        fillcolor=color, opacity=0.8, line_width=0
                                    )
                                
                                fig_micro.update_layout(
                                    title=f"Hypnogram - {selected_date.strftime('%B %d, %Y')}",
                                    height=400,
                                    margin=dict(l=20, r=20, t=40, b=20),
                                    template="plotly_dark" if dark_mode else "plotly_white",
                                    yaxis=dict(
                                        tickmode="array",
                                        tickvals=[1, 2, 3, 4],
                                        ticktext=["Deep", "REM", "Light", "Awake"],
                                        range=[0.5, 4.5]
                                    ),
                                    xaxis_title="Time",
                                    yaxis_title="Sleep Stage",
                                    showlegend=False,
                                    hovermode="x unified"
                                )
                                
                                st.plotly_chart(fig_micro, use_container_width=True)
                                
                                sleep_data["night_date"] = (sleep_data[time_col] - pd.Timedelta(hours=12)).dt.date
                                night_macro = sleep_data[sleep_data["night_date"] == selected_date]
                                if not night_macro.empty:
                                    nm = night_macro.iloc[0]
                                    m1, m2, m3, m4 = st.columns(4)
                                    
                                    score = nm.get("sleep_score", "N/A")
                                    m1.metric("Sleep Score", f"{int(score)}/100" if pd.notna(score) else "N/A", "AI-calculated quality")
                                    
                                    eff = nm.get("efficiency", "N/A")
                                    m2.metric("Efficiency", f"{int(eff)}%" if pd.notna(eff) else "N/A", "Time asleep in bed")
                                    
                                    dur = nm.get("sleep_duration", 0)
                                    m3.metric("Duration", f"{int(dur//60)}h {int(dur%60)}m" if pd.notna(dur) else "N/A", "Total sleep time")
                                    
                                    rem = nm.get("total_rem_duration", 0)
                                    m4.metric("REM Time", f"{int(rem)} mins" if pd.notna(rem) else "N/A", "Dreams & memory")

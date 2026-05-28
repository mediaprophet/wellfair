from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from .styling import HEALTH_COLORS


def plot_dataset_chart(dtype: str, df: pd.DataFrame, display_name: str, dark_mode: bool = False) -> None:
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

    # World-class transparent Plotly styling
    font_color = "#f1f5f9" if dark_mode else "#0f172a"
    grid_color = "rgba(255,255,255,0.05)" if dark_mode else "rgba(0,0,0,0.05)"
    
    # Neon palettes for dark mode
    neon_primary = "#00f0ff" if dark_mode else HEALTH_COLORS["primary"]
    neon_secondary = "#ff00e5" if dark_mode else HEALTH_COLORS["secondary"]
    neon_accent = "#ffaa00" if dark_mode else HEALTH_COLORS["accent"]
    neon_clinical = "#b026ff" if dark_mode else HEALTH_COLORS["clinical"]

    layout_args = dict(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color, family="Inter, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor=grid_color, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=grid_color, zeroline=False),
    )

    if "weight" in dtype.lower() and "weight" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y="weight",
            markers=True,
            title=f"{display_name} Trend (kg)",
            color_discrete_sequence=[neon_primary]
        )
        fig.update_layout(**layout_args)
        # Add glow effect in dark mode
        if dark_mode:
            fig.update_traces(line=dict(width=3), marker=dict(size=6, line=dict(width=2, color=neon_primary)))
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
                color_discrete_sequence=[neon_accent]
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
                color_discrete_sequence=[neon_secondary]
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
                    color_discrete_sequence=["#ef4444", neon_primary, neon_accent]
                )
                if dark_mode:
                    fig.update_traces(line=dict(width=2))
            else:
                fig = px.scatter(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=hr_col,
                    title=f"{display_name} (BPM)",
                    color_discrete_sequence=["#ef4444"],
                    opacity=0.8 if dark_mode else 0.6
                )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)

    elif "blood_pressure" in dtype.lower() and "systolic" in df.columns and "diastolic" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y=["systolic", "diastolic"],
            title=f"{display_name} (mmHg)",
            color_discrete_sequence=["#ef4444", neon_primary]
        )
        if dark_mode:
            fig.update_traces(line=dict(width=3))
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "oxygen_saturation" in dtype.lower() and "spo2" in df.columns:
        fig = px.line(
            df_sorted,
            x=time_col or df_sorted.index,
            y="spo2",
            markers=True,
            title=f"{display_name} (%)",
            color_discrete_sequence=[neon_primary]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "stress" in dtype.lower() and "score" in df.columns:
        fig = px.bar(
            df_sorted,
            x=time_col or df_sorted.index,
            y="score",
            title=f"{display_name} (Stress Score)",
            color_discrete_sequence=[neon_clinical]
        )
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

    elif "water_intake" in dtype.lower() and "amount" in df.columns:
        fig = px.bar(
            df_sorted,
            x=time_col or df_sorted.index,
            y="amount",
            title=f"{display_name} (mL)",
            color_discrete_sequence=[neon_primary]
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
                    color_discrete_sequence=[neon_primary]
                )
            else:
                fig = px.line(
                    df_sorted,
                    x=time_col or df_sorted.index,
                    y=selected_num_col,
                    title=f"{display_name} - {selected_num_col}",
                    color_discrete_sequence=[neon_primary]
                )
            fig.update_layout(**layout_args)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numerical fields available to plot.")

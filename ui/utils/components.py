import streamlit as st


def render_info_banner(title: str, body: str, accent_color: str = "#0d9488", icon: str = "ℹ️", dark_mode: bool = False) -> None:
    bg = "rgba(0,0,0,0.2)" if dark_mode else "rgba(255,255,255,0.6)"
    text_color = "#f1f5f9" if dark_mode else "#1e293b"
    st.markdown(f"""
    <div style="background:{bg};border-left:4px solid {accent_color};border-radius:8px;
                padding:14px 18px;margin-bottom:16px;color:{text_color};">
        <div style="font-size:1.05rem;font-weight:700;margin-bottom:4px;">{icon} {title}</div>
        <div style="font-size:0.88rem;line-height:1.55;">{body}</div>
    </div>""", unsafe_allow_html=True)


def render_premium_card(title: str, value: str, subtitle: str = "", color: str = "#3b82f6", dark_mode: bool = False) -> str:
    bg = "rgba(30,41,59,0.7)" if dark_mode else "rgba(255,255,255,0.85)"
    text = "#f1f5f9" if dark_mode else "#0f172a"
    sub = "#94a3b8" if dark_mode else "#64748b"
    return f"""
    <div style="background:{bg};border-top:3px solid {color};border-radius:10px;padding:16px 18px;margin-bottom:10px;">
        <div style="font-size:0.78rem;font-weight:600;color:{sub};text-transform:uppercase;letter-spacing:.06em;">{title}</div>
        <div style="font-size:1.6rem;font-weight:800;color:{color};margin:4px 0;">{value}</div>
        <div style="font-size:0.78rem;color:{sub};">{subtitle}</div>
    </div>
    """


def render_kpi_row(kpis: list, dark_mode: bool = False):
    if not kpis:
        return
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        color = kpi.get("color", "#3b82f6")
        emoji = kpi.get("emoji", "")
        with col:
            st.markdown(
                render_premium_card(
                    title=f"{emoji} {kpi.get('title', '')}",
                    value=kpi.get("value", "—"),
                    subtitle=kpi.get("subtitle", ""),
                    color=color,
                    dark_mode=dark_mode,
                ),
                unsafe_allow_html=True,
            )


def render_section_header(title: str, subtitle: str = "", dark_mode: bool = False):
    color = "#f1f5f9" if dark_mode else "#0f172a"
    sub_color = "#94a3b8" if dark_mode else "#64748b"
    st.markdown(
        f"<h2 style='color:{color};margin-bottom:2px;'>{title}</h2>"
        f"<p style='color:{sub_color};margin-top:0;font-size:0.9rem;'>{subtitle}</p>",
        unsafe_allow_html=True,
    )


def render_simple_metric_card(title: str, value: str, subtitle: str = "", dark_mode: bool = False):
    bg = "rgba(30,41,59,0.6)" if dark_mode else "#f8fafc"
    border = "#334155" if dark_mode else "#e2e8f0"
    text = "#f1f5f9" if dark_mode else "#0f172a"
    sub = "#94a3b8" if dark_mode else "#64748b"
    st.markdown(
        f"""<div style="background:{bg};border:1px solid {border};border-radius:8px;padding:14px 16px;margin-bottom:8px;">
            <div style="font-size:0.78rem;font-weight:600;color:{sub};text-transform:uppercase;">{title}</div>
            <div style="font-size:1.4rem;font-weight:700;color:{text};margin:4px 0;">{value}</div>
            <div style="font-size:0.78rem;color:{sub};">{subtitle}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_alert_card(title: str, body: str, accent_color: str = "#ef4444", icon: str = "⚠️", dark_mode: bool = False):
    bg = "rgba(239,68,68,0.12)" if dark_mode else "rgba(239,68,68,0.07)"
    text = "#fecaca" if dark_mode else "#7f1d1d"
    st.markdown(
        f"""<div style="background:{bg};border-left:4px solid {accent_color};border-radius:8px;padding:14px 18px;margin-bottom:12px;">
            <div style="font-size:1rem;font-weight:700;color:{accent_color};margin-bottom:6px;">{icon} {title}</div>
            <div style="font-size:0.88rem;color:{text};line-height:1.55;">{body}</div>
        </div>""",
        unsafe_allow_html=True,
    )

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.phr_models.life_events import LifeEventCategory, SeverityLevel, PrivacyMode, DocumentCategory, RecoveryStatus

def render_life_events(dark_mode: bool):
    st.markdown("## 🏛️ Life Events & Socioeconomic Wellbeing")

    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #f59e0b; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #f59e0b;">🌐 Personal Welfare Informatics Vault</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Life events are pivotal transitions — job loss, separation, housing instability — that cascade across financial, legal, relational, and health domains.
                This section tracks events holistically using the <b>OECD Well-being Framework</b>, linking to your clinical records, supporting documents, and recovery pathways.
                All records default to <b>Strict Privacy (Mode A)</b> given their sensitive nature.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    events = st.session_state.life_events

    if not events:
        st.info("No life events have been recorded yet.")
        return

    total_events = len(events)
    ongoing = sum(1 for e in events if e["end_date"] is None)
    resolved = total_events - ongoing
    critical_count = sum(1 for e in events if e["severity"] == SeverityLevel.CRITICAL)

    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "Total Events", str(total_events), "📊", "#3b82f6"),
        (k2, "Ongoing", str(ongoing), "🔄", "#f59e0b"),
        (k3, "Resolved", str(resolved), "✅", "#10b981"),
        (k4, "Critical", str(critical_count), "🚨", "#ef4444"),
    ]
    for col, title, value, emoji, color in kpi_data:
        with col:
            st.markdown(
                f"""
                <div class="premium-card" style="border-left: 5px solid {color};">
                    <div class="flex-center">
                        <div class="icon-circle" style="background: {color}22; color: {color};">{emoji}</div>
                        <div>
                            <div class="metric-title">{title}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 📅 Life Event Timeline")

    severity_color_map = {
        SeverityLevel.LOW: "#10b981",
        SeverityLevel.MODERATE: "#f59e0b",
        SeverityLevel.HIGH: "#f97316",
        SeverityLevel.CRITICAL: "#ef4444",
    }

    timeline_data = []
    for ev in events:
        end = ev["end_date"] if ev["end_date"] else datetime.now()
        timeline_data.append({
            "Event": ev["title"],
            "Category": ev["event_category"].value.replace("-", " ").title(),
            "Start": ev["trigger_date"],
            "End": end,
            "Severity": ev["severity"].value.title(),
            "Status": "Resolved" if ev["end_date"] else "Ongoing",
        })

    tl_df = pd.DataFrame(timeline_data)
    fig_tl = px.timeline(
        tl_df,
        x_start="Start",
        x_end="End",
        y="Event",
        color="Severity",
        color_discrete_map={
            "Low": "#10b981",
            "Moderate": "#f59e0b",
            "High": "#f97316",
            "Critical": "#ef4444",
        },
        hover_data=["Category", "Status"],
    )
    fig_tl.update_layout(
        height=max(200, 80 * len(events)),
        margin=dict(l=20, r=20, t=30, b=20),
        template="plotly_dark" if dark_mode else "plotly_white",
        xaxis_title="",
        yaxis_title="",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_tl.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tl, use_container_width=True)

    st.divider()

    st.markdown("### 🎯 Aggregate Wellbeing Impact")
    st.caption("Which OECD wellbeing dimensions are most affected across all life events.")

    severity_score = {SeverityLevel.LOW: 1, SeverityLevel.MODERATE: 2, SeverityLevel.HIGH: 3, SeverityLevel.CRITICAL: 4}
    dim_scores = {}
    for ev in events:
        for wi in ev["wellbeing_impacts"]:
            dim = wi["dimension"]
            score = severity_score.get(wi["severity"], 1)
            dim_key = dim.value.replace("-", " ").title()
            dim_scores[dim_key] = dim_scores.get(dim_key, 0) + score

    if dim_scores:
        sorted_dims = sorted(dim_scores.items(), key=lambda x: x[1], reverse=True)
        dim_names = [d[0] for d in sorted_dims]
        dim_vals = [d[1] for d in sorted_dims]

        fig_bar = go.Figure(go.Bar(
            x=dim_vals,
            y=dim_names,
            orientation="h",
            marker=dict(
                color=dim_vals,
                colorscale=[[0, "#10b981"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            ),
        ))
        fig_bar.update_layout(
            height=max(250, 35 * len(dim_names)),
            margin=dict(l=20, r=20, t=10, b=20),
            template="plotly_dark" if dark_mode else "plotly_white",
            xaxis_title="Cumulative Impact Score",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    st.markdown("### 📋 Event Details")

    for ev in events:
        sev = ev["severity"]
        sev_color = severity_color_map.get(sev, "#64748b")
        privacy_color_map = {
            PrivacyMode.MODE_A_STRICT: "#ef4444",
            PrivacyMode.MODE_B_PRIVILEGED: "#f59e0b",
            PrivacyMode.MODE_C_SHARED: "#10b981",
        }
        p_color = privacy_color_map.get(ev["privacy_mode"], "#64748b")
        status_label = "Resolved ✅" if ev["end_date"] else "Ongoing 🔄"
        maslow_label = ev["maslow_layer"].value.title() if ev.get("maslow_layer") else "Not tagged"
        category_icon_map = {
            LifeEventCategory.JOB_LOSS: "💼",
            LifeEventCategory.DIVORCE_SEPARATION: "💔",
            LifeEventCategory.BANKRUPTCY: "📉",
            LifeEventCategory.HOMELESSNESS: "🏚️",
            LifeEventCategory.HEALTH_CRISIS: "🏥",
            LifeEventCategory.INCARCERATION: "⚖️",
            LifeEventCategory.BEREAVEMENT: "🕊️",
            LifeEventCategory.DOMESTIC_VIOLENCE: "🛡️",
            LifeEventCategory.DISABILITY_ONSET: "♿",
            LifeEventCategory.MIGRATION: "✈️",
            LifeEventCategory.NATURAL_DISASTER: "🌊",
            LifeEventCategory.EDUCATION_TRANSITION: "🎓",
            LifeEventCategory.RETIREMENT: "🌅",
            LifeEventCategory.OTHER: "📌",
        }
        cat_icon = category_icon_map.get(ev["event_category"], "📌")

        with st.expander(f"{cat_icon} {ev['title']} — {ev['event_category'].value.replace('-', ' ').title()} ({status_label})", expanded=False):
            st.markdown(
                f"""
                <div class="premium-card" style="border-left: 5px solid {sev_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-size: 1.3rem;">{cat_icon}</span>
                            <strong style="font-size: 1.1rem;">{ev['title']}</strong>
                        </div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span style="font-size: 0.7rem; background: {sev_color}22; color: {sev_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                {sev.value.upper()}
                            </span>
                            <span style="font-size: 0.7rem; background: {p_color}22; color: {p_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                {ev['privacy_mode'].name.replace('MODE_', '').replace('_', ' ')}
                            </span>
                            <span style="font-size: 0.7rem; background: #8b5cf622; color: #8b5cf6; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                Maslow: {maslow_label}
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px;">
                        Triggered: {ev['trigger_date'].strftime('%d %b %Y')} |
                        {f"Resolved: {ev['end_date'].strftime('%d %b %Y')}" if ev['end_date'] else 'Status: Ongoing'}
                    </div>
                    <p style="font-size: 0.9rem; margin-top: 8px;">{ev['description']}</p>
                    {f'<p style="font-size: 0.85rem; color: #64748b; font-style: italic; margin-top: 4px;">📝 {ev["notes"]}</p>' if ev.get('notes') else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_left, c_right = st.columns([1, 1])

            with c_left:
                st.markdown("#### 🎯 Wellbeing Impact Radar")
                impacts = ev["wellbeing_impacts"]
                if impacts:
                    radar_dims = [wi["dimension"].value.replace("-", " ").title() for wi in impacts]
                    radar_vals = [severity_score.get(wi["severity"], 1) for wi in impacts]
                    radar_dims_closed = radar_dims + [radar_dims[0]]
                    radar_vals_closed = radar_vals + [radar_vals[0]]

                    hex_clean = sev_color.lstrip('#')
                    r_val, g_val, b_val = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
                    rgba_fillcolor = f"rgba({r_val}, {g_val}, {b_val}, 0.2)"

                    fig_radar = go.Figure(go.Scatterpolar(
                        r=radar_vals_closed,
                        theta=radar_dims_closed,
                        fill="toself",
                        fillcolor=rgba_fillcolor,
                        line=dict(color=sev_color, width=2),
                        marker=dict(size=6),
                    ))
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 4], tickvals=[1, 2, 3, 4], ticktext=["Low", "Mod", "High", "Crit"]),
                        ),
                        height=300,
                        margin=dict(l=40, r=40, t=30, b=30),
                        template="plotly_dark" if dark_mode else "plotly_white",
                        showlegend=False,
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                    for wi in impacts:
                        wi_color = severity_color_map.get(wi["severity"], "#64748b")
                        st.markdown(
                            f'<div style="font-size: 0.8rem; margin: 2px 0;">'
                            f'<span style="color: {wi_color}; font-weight: bold;">●</span> '
                            f'<b>{wi["dimension"].value.replace("-", " ").title()}</b> — '
                            f'{wi.get("description", "No details")}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No wellbeing impacts recorded.")

            with c_right:
                st.markdown("#### 🛤️ Recovery Pathway")
                recovery = ev["recovery_indicators"]
                if recovery:
                    status_icons = {
                        RecoveryStatus.NOT_STARTED: ("⬜", "#94a3b8"),
                        RecoveryStatus.IN_PROGRESS: ("🔵", "#3b82f6"),
                        RecoveryStatus.STABLE: ("🟡", "#f59e0b"),
                        RecoveryStatus.RESOLVED: ("🟢", "#10b981"),
                    }
                    total_r = len(recovery)
                    completed_r = sum(1 for r in recovery if r["status"] in [RecoveryStatus.RESOLVED, RecoveryStatus.STABLE])
                    progress_pct = int((completed_r / total_r) * 100) if total_r else 0

                    st.progress(progress_pct / 100, text=f"Recovery Progress: {progress_pct}% ({completed_r}/{total_r} milestones)")

                    for rec in recovery:
                        icon, r_color = status_icons.get(rec["status"], ("⬜", "#94a3b8"))
                        svc = f" — <i style='color: #8b5cf6;'>{rec['linked_service']}</i>" if rec.get("linked_service") else ""
                        st.markdown(
                            f'<div style="font-size: 0.8rem; margin: 4px 0; padding: 4px 8px; '
                            f'background: {r_color}11; border-left: 3px solid {r_color}; border-radius: 4px;">'
                            f'{icon} {rec["description"]}{svc}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No recovery milestones defined.")

                st.markdown("#### 📎 Supporting Documents")
                docs = ev["supporting_documents"]
                if docs:
                    doc_cat_icons = {
                        DocumentCategory.LEGAL: "⚖️",
                        DocumentCategory.PROFESSIONAL: "💼",
                        DocumentCategory.FINANCIAL: "💰",
                        DocumentCategory.HOUSING: "🏠",
                        DocumentCategory.RELATIONAL: "👥",
                        DocumentCategory.GOVERNMENT: "🏛️",
                        DocumentCategory.MEDICAL: "🏥",
                    }
                    for doc in docs:
                        d_icon = doc_cat_icons.get(doc["category"], "📄")
                        jur = f" | <span style='color: #06b6d4;'>{doc.get('jurisdiction', 'N/A')}</span>" if doc.get("jurisdiction") else ""
                        st.markdown(
                            f'<div style="font-size: 0.8rem; margin: 4px 0; padding: 4px 8px; '
                            f'background: #1e293b22; border-left: 3px solid #64748b; border-radius: 4px;">'
                            f'{d_icon} <b>{doc["title"]}</b> '
                            f'<span style="color: #94a3b8;">({doc["category"].value.title()}){jur}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No documents attached.")

            linked_psych = ev.get("linked_psych_observation_ids", [])
            linked_meds = ev.get("linked_medication_ids", [])
            if linked_psych or linked_meds:
                st.markdown("#### 🔗 Clinical Cross-References")
                ref_cols = st.columns(2)
                with ref_cols[0]:
                    if linked_psych:
                        for pid in linked_psych:
                            obs_name = pid
                            for obs in st.session_state.psychiatric_observations:
                                if obs["id"] == pid:
                                    obs_name = f"{obs['symptom_name']} ({obs['date_recorded'].strftime('%d %b')})"
                                    break
                            st.markdown(
                                f'<div style="font-size: 0.8rem;">🧠 Psychiatric: <b>{obs_name}</b> '
                                f'<span style="color: #94a3b8;">({pid})</span></div>',
                                unsafe_allow_html=True,
                            )
                with ref_cols[1]:
                    if linked_meds:
                        for mid in linked_meds:
                            med_name = mid
                            for med in st.session_state.medication_administrations:
                                if med["id"] == mid:
                                    med_name = med["medication_name"]
                                    break
                            st.markdown(
                                f'<div style="font-size: 0.8rem;">💊 Medication: <b>{med_name}</b> '
                                f'<span style="color: #94a3b8;">({mid})</span></div>',
                                unsafe_allow_html=True,
                            )

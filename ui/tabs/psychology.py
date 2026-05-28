"""Psychology UI tab – Therapy, Formulation, Sub Rosa & Timeline.

Renders the top-level **🧪 Psychology** page with four sub-tabs:
1. Therapy & Formulation
2. Sub Rosa (Confessional)
3. Semantic Tripwires
4. Psychological Timeline
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, date, timedelta

import streamlit as st

from src.phr_models.psychology import (
    TherapyModality,
    AttachmentStyle,
    SubRosaCategory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _card(title: str, body: str, accent: str = "#8b5cf6") -> str:
    return f"""
<div class="premium-card" style="border-left: 5px solid {accent}; margin-bottom: 16px;">
<h4 style="margin: 0; color: {accent};">{title}</h4>
<div style="font-size: 0.88rem; color: #94a3b8; margin-top: 6px;">{body}</div>
</div>"""


SUB_ROSA_COLORS = {
    SubRosaCategory.SUBSTANCE_USE: "#ef4444",
    SubRosaCategory.SEXUAL_HEALTH: "#ec4899",
    SubRosaCategory.ENVIRONMENTAL_EXPOSURE: "#f59e0b",
    SubRosaCategory.DOMESTIC_SITUATION: "#dc2626",
    SubRosaCategory.PROFESSIONAL_CONFLICT: "#6366f1",
    SubRosaCategory.LEGAL_ENTANGLEMENT: "#7c3aed",
    SubRosaCategory.FINANCIAL_DURESS: "#0ea5e9",
    SubRosaCategory.DEVELOPMENTAL_TRAUMA: "#e11d48",
    SubRosaCategory.OTHER: "#64748b",
}


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state():
    if "therapy_sessions" not in st.session_state:
        now = datetime.now()
        st.session_state.therapy_sessions = [
            {
                "id": "ts-demo-1",
                "date": now - timedelta(days=14),
                "modality": TherapyModality.CBT.value,
                "therapist": "Dr. Amara Chen (Clinical Psychologist)",
                "summary": "Explored cognitive distortions around workplace conflict. "
                           "Identified catastrophising pattern linked to childhood authority dynamics.",
                "homework": "Daily thought record – 3 column format",
                "mood_pre": 3,
                "mood_post": 6,
            },
            {
                "id": "ts-demo-2",
                "date": now - timedelta(days=7),
                "modality": TherapyModality.EMDR.value,
                "therapist": "Dr. Amara Chen (Clinical Psychologist)",
                "summary": "Bilateral stimulation targeting index trauma memory (age 12). "
                           "SUD score reduced from 8 to 4. Session emotionally intense but contained.",
                "homework": "Safe-place visualisation before sleep",
                "mood_pre": 4,
                "mood_post": 5,
            },
        ]

    if "psych_formulation" not in st.session_state:
        st.session_state.psych_formulation = {
            "presenting": ["Persistent anxiety in professional settings", "Difficulty trusting authority figures"],
            "predisposing": ["Childhood emotional neglect", "Early parentification"],
            "precipitating": ["Workplace restructure (March 2026)", "Relationship breakdown"],
            "perpetuating": ["Avoidance of difficult conversations", "Social isolation", "Poor sleep hygiene"],
            "protective": ["Strong intellectual capability", "Engaged with therapy", "Creative outlets (music)"],
            "narrative": "",
        }

    if "attachment_record" not in st.session_state:
        st.session_state.attachment_record = {
            "style": AttachmentStyle.FEARFUL_AVOIDANT.value,
            "confidence": "Medium",
            "assessor": "Self + Clinician-Guided",
            "notes": "Pattern of approach-avoidance in close relationships. Hypervigilance around perceived rejection.",
        }

    if "sub_rosa_records" not in st.session_state:
        st.session_state.sub_rosa_records = []

    if "tripwire_simulations" not in st.session_state:
        st.session_state.tripwire_simulations = []


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_psychology(dark_mode: bool):
    _init_state()

    st.markdown("## 🧪 Psychology")
    st.markdown(
        _card(
            "🧪 Clinical Psychology Vault",
            "Therapy session tracking, psychological formulation, attachment mapping, "
            "and the <b>Sub Rosa</b> confessional for clinically-relevant sensitive records. "
            "All data defaults to <b>Mode A (Strict Privacy)</b> and is never shared without explicit consent.",
            "#8b5cf6",
        ),
        unsafe_allow_html=True,
    )

    tab_therapy, tab_subrosa, tab_tripwire, tab_timeline = st.tabs([
        "🗣️ Therapy & Formulation",
        "🌹 Sub Rosa (Confessional)",
        "⚡ Semantic Tripwires",
        "📊 Psychological Timeline",
    ])

    # ==================================================================
    # TAB 1 – THERAPY & FORMULATION
    # ==================================================================
    with tab_therapy:
        _render_therapy_tab(dark_mode)

    # ==================================================================
    # TAB 2 – SUB ROSA
    # ==================================================================
    with tab_subrosa:
        _render_subrosa_tab(dark_mode)

    # ==================================================================
    # TAB 3 – SEMANTIC TRIPWIRES
    # ==================================================================
    with tab_tripwire:
        _render_tripwire_tab(dark_mode)

    # ==================================================================
    # TAB 4 – PSYCHOLOGICAL TIMELINE
    # ==================================================================
    with tab_timeline:
        _render_timeline_tab(dark_mode)


# ---------------------------------------------------------------------------
# TAB 1 – Therapy & Formulation
# ---------------------------------------------------------------------------

def _render_therapy_tab(dark_mode: bool):
    col_form, col_history = st.columns([1, 1])

    # ---- Left: Log session + Formulation + Attachment ----
    with col_form:
        st.markdown("### 📝 Log Therapy Session")
        with st.form("therapy_session_form", clear_on_submit=True):
            modality = st.selectbox("Modality", [m.value for m in TherapyModality])
            therapist = st.text_input("Therapist / Psychologist", placeholder="e.g., Dr. Amara Chen")
            summary = st.text_area("Session Summary", placeholder="Key themes, insights, breakthroughs...")
            homework = st.text_input("Homework / Between-Session Tasks (optional)")
            sc1, sc2 = st.columns(2)
            with sc1:
                mood_pre = st.slider("Mood Before (0-10)", 0, 10, 5)
            with sc2:
                mood_post = st.slider("Mood After (0-10)", 0, 10, 5)

            if st.form_submit_button("💾 Save Session Note", type="primary") and summary:
                st.session_state.therapy_sessions.append({
                    "id": f"ts-{uuid.uuid4().hex[:8]}",
                    "date": datetime.now(),
                    "modality": modality,
                    "therapist": therapist,
                    "summary": summary,
                    "homework": homework,
                    "mood_pre": mood_pre,
                    "mood_post": mood_post,
                })
                st.success("Session note saved.")
                st.rerun()

        # ---- Psychological Formulation (5 Ps) ----
        st.markdown("### 🧩 Psychological Formulation (5 Ps)")
        form = st.session_state.psych_formulation

        ps_labels = [
            ("presenting", "Presenting Problems", "#ef4444"),
            ("predisposing", "Predisposing Factors", "#f59e0b"),
            ("precipitating", "Precipitating Factors", "#3b82f6"),
            ("perpetuating", "Perpetuating Factors", "#e11d48"),
            ("protective", "Protective Factors", "#10b981"),
        ]
        for key, label, color in ps_labels:
            items = form.get(key, [])
            st.markdown(
                f"<div style='margin:8px 0 4px 0;'>"
                f"<span style='font-size:0.72rem; font-weight:700; text-transform:uppercase; "
                f"letter-spacing:0.05em; color:{color};'>{label}</span></div>",
                unsafe_allow_html=True,
            )
            for item in items:
                st.markdown(f"<div style='font-size:0.85rem; padding:2px 0 2px 12px; "
                            f"border-left:3px solid {color}; margin:3px 0;'>{item}</div>",
                            unsafe_allow_html=True)

        with st.expander("✏️ Edit Formulation"):
            with st.form("edit_formulation", clear_on_submit=False):
                for key, label, _ in ps_labels:
                    current = "\n".join(form.get(key, []))
                    new_val = st.text_area(label, value=current, height=80, key=f"form_{key}")
                    form[key] = [line.strip() for line in new_val.split("\n") if line.strip()]
                if st.form_submit_button("Save Formulation"):
                    st.session_state.psych_formulation = form
                    st.success("Formulation updated.")
                    st.rerun()

        # ---- Attachment Style ----
        st.markdown("### 🔗 Attachment Style")
        att = st.session_state.attachment_record
        att_colors = {
            AttachmentStyle.SECURE.value: "#10b981",
            AttachmentStyle.ANXIOUS_PREOCCUPIED.value: "#f59e0b",
            AttachmentStyle.DISMISSIVE_AVOIDANT.value: "#3b82f6",
            AttachmentStyle.FEARFUL_AVOIDANT.value: "#e11d48",
            AttachmentStyle.DISORGANISED.value: "#7c3aed",
        }
        att_color = att_colors.get(att["style"], "#64748b")
        st.markdown(
            f"""<div class="premium-card" style="border-left: 4px solid {att_color}; padding: 14px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1rem; font-weight:700; color:{att_color};">{att['style'].replace('-', ' ').title()}</span>
<span style="font-size:0.72rem; background:{att_color}1a; color:{att_color}; padding:2px 8px; border-radius:4px;">
Confidence: {att['confidence']}</span>
</div>
<p style="font-size:0.82rem; color:#94a3b8; margin:6px 0 0 0;">{att.get('notes', '')}</p>
<p style="font-size:0.72rem; color:#64748b; margin:4px 0 0 0;">Assessor: {att['assessor']}</p>
</div>""",
            unsafe_allow_html=True,
        )

    # ---- Right: Session history ----
    with col_history:
        st.markdown("### 📋 Session History")
        sessions = st.session_state.therapy_sessions
        if not sessions:
            st.info("No therapy sessions logged yet.")
        else:
            for s in reversed(sessions):
                dt = s["date"]
                date_str = dt.strftime("%b %d, %Y %H:%M") if isinstance(dt, datetime) else str(dt)
                delta = s["mood_post"] - s["mood_pre"]
                delta_icon = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
                delta_color = "#10b981" if delta > 0 else ("#ef4444" if delta < 0 else "#64748b")

                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid #8b5cf6; padding: 14px; margin-bottom: 10px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:#8b5cf6;">{s['modality']}</span>
<span style="font-size:0.72rem; color:#64748b;">{date_str}</span>
</div>
<p style="font-size:0.85rem; color:#cbd5e1; margin:8px 0 4px 0;">{s['summary']}</p>
<div style="display:flex; gap:16px; font-size:0.78rem; color:#94a3b8; margin-top:6px;">
<span>Mood: {s['mood_pre']} → {s['mood_post']} <span style="color:{delta_color};">{delta_icon} {delta:+d}</span></span>
{'<span>📌 ' + s['homework'] + '</span>' if s.get('homework') else ''}
</div>
<p style="font-size:0.72rem; color:#64748b; margin:4px 0 0 0;">🩺 {s.get('therapist', 'Unspecified')}</p>
</div>""",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# TAB 2 – Sub Rosa (Confessional)
# ---------------------------------------------------------------------------

def _render_subrosa_tab(dark_mode: bool):
    st.markdown("### 🌹 Sub Rosa – Confessional Vault")
    st.markdown(
        _card(
            "🌹 The Veiled Graph",
            "Record clinically-relevant but socially-sensitive information that must remain "
            "<b>computationally active</b> (can trigger drug interaction warnings, contraindication "
            "alerts) yet <b>socially invisible</b> to external agents. "
            "Each record is SHA-256 hashed for immutable provenance anchoring.",
            "#e11d48",
        ),
        unsafe_allow_html=True,
    )

    col_entry, col_records = st.columns([1, 1])

    with col_entry:
        st.markdown("#### New Sub Rosa Entry")
        with st.form("subrosa_form", clear_on_submit=True):
            category = st.selectbox(
                "Category",
                [c.value for c in SubRosaCategory],
                help="Choose the domain of sensitivity",
            )
            narrative = st.text_area(
                "Narrative (encrypted at rest)",
                placeholder="Describe the situation, substance, event, or exposure...",
                height=120,
            )
            clinical_relevance = st.text_area(
                "Clinical Relevance",
                placeholder="Why does this matter medically? E.g., 'Cocaine use contraindicates beta-blockers'",
                height=80,
            )
            semantic_tags = st.text_input(
                "Semantic Tags (comma-separated)",
                placeholder="e.g., cardiovascular, hepatotoxicity, STI-screening",
            )
            tripwire_rules = st.text_input(
                "Tripwire Query Patterns (comma-separated)",
                placeholder="e.g., prescribe:beta-blocker, test:liver-function",
            )
            is_hypothesis = st.checkbox(
                "This is a hypothesis / suspicion (not a confirmed fact)",
                value=False,
            )

            submitted = st.form_submit_button("🔒 Seal & Anchor Record", type="primary")

        if submitted and narrative:
            ts = datetime.now()
            record_id = f"sr-{uuid.uuid4().hex[:8]}"
            payload = f"{record_id}|{category}|{narrative}|{ts.isoformat()}"
            prov_hash = hashlib.sha256(payload.encode()).hexdigest()

            tags = [t.strip() for t in semantic_tags.split(",") if t.strip()] if semantic_tags else []
            rules = [r.strip() for r in tripwire_rules.split(",") if r.strip()] if tripwire_rules else []

            new_record = {
                "id": record_id,
                "timestamp": ts,
                "category": category,
                "narrative": narrative,
                "clinical_relevance": clinical_relevance,
                "semantic_tags": tags,
                "tripwire_rules": rules,
                "hypothesis_flag": is_hypothesis,
                "provenance_hash": prov_hash,
            }
            st.session_state.sub_rosa_records.append(new_record)
            st.success(f"✅ Sub Rosa record sealed. Provenance hash: `sha256:{prov_hash[:16]}…`")
            st.rerun()

    with col_records:
        st.markdown("#### Sealed Records")
        records = st.session_state.sub_rosa_records
        if not records:
            st.markdown(
                _card(
                    "No records yet",
                    "Use the form on the left to create your first Sub Rosa entry. "
                    "Records are stored locally and never transmitted without your explicit consent.",
                    "#475569",
                ),
                unsafe_allow_html=True,
            )
        else:
            for rec in reversed(records):
                cat_enum = SubRosaCategory(rec["category"])
                accent = SUB_ROSA_COLORS.get(cat_enum, "#64748b")
                hyp_badge = ('<span style="font-size:0.65rem; background:#f59e0b22; color:#f59e0b; '
                             'padding:1px 6px; border-radius:3px; margin-left:6px;">HYPOTHESIS</span>'
                             if rec.get("hypothesis_flag") else "")
                tripwire_count = len(rec.get("tripwire_rules", []))
                tripwire_badge = (f'<span style="font-size:0.65rem; background:#ef444422; color:#ef4444; '
                                  f'padding:1px 6px; border-radius:3px; margin-left:6px;">'
                                  f'⚡ {tripwire_count} tripwire(s)</span>' if tripwire_count else "")

                ts = rec["timestamp"]
                ts_str = ts.strftime("%b %d, %Y %H:%M") if isinstance(ts, datetime) else str(ts)

                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {accent}; padding: 14px; margin-bottom: 10px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
<span style="font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:{accent};">{rec['category']}</span>
<span style="font-size:0.68rem; color:#64748b;">{ts_str}{hyp_badge}{tripwire_badge}</span>
</div>
<p style="font-size:0.85rem; color:#cbd5e1; margin:8px 0 4px 0;">{rec['narrative']}</p>
{'<p style="font-size:0.78rem; color:#94a3b8; margin:4px 0;"><b>Clinical:</b> ' + rec['clinical_relevance'] + '</p>' if rec.get('clinical_relevance') else ''}
{'<p style="font-size:0.72rem; color:#64748b; margin:2px 0;">Tags: ' + ', '.join(rec['semantic_tags']) + '</p>' if rec.get('semantic_tags') else ''}
<div style="font-family:monospace; font-size:0.62rem; color:#a855f7; margin-top:6px;">Provenance: sha256:{rec['provenance_hash']}</div>
</div>""",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# TAB 3 – Semantic Tripwires
# ---------------------------------------------------------------------------

def _render_tripwire_tab(dark_mode: bool):
    st.markdown("### ⚡ Semantic Tripwires")
    st.markdown(
        _card(
            "⚡ Opaque Collision Detection",
            "Semantic Tripwires intercept external queries that would produce unsafe results "
            "due to hidden Sub Rosa records. The system alerts you without revealing the secret itself. "
            "For full threat analysis, access the <b>Synthesis Engine</b> in Sanctuary Mode.",
            "#f43f5e",
        ),
        unsafe_allow_html=True,
    )

    # ---- Active tripwire rules from Sub Rosa records ----
    st.markdown("#### 🕸️ Active Tripwire Rules")
    records = st.session_state.sub_rosa_records
    active_rules = []
    for rec in records:
        for rule in rec.get("tripwire_rules", []):
            active_rules.append({
                "rule": rule,
                "source_category": rec["category"],
                "source_id": rec["id"],
            })

    if not active_rules:
        st.info("No tripwire rules defined. Add tripwire query patterns when creating Sub Rosa records.")
    else:
        for r in active_rules:
            cat_enum = SubRosaCategory(r["source_category"])
            accent = SUB_ROSA_COLORS.get(cat_enum, "#64748b")
            st.markdown(
                f"""<div class="premium-card" style="border-left: 3px solid {accent}; padding: 10px; margin-bottom: 8px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<code style="font-size:0.85rem; color:#ef4444;">{r['rule']}</code>
<span style="font-size:0.65rem; color:{accent}; text-transform:uppercase;">{r['source_category']}</span>
</div>
<p style="font-size:0.7rem; color:#64748b; margin:4px 0 0 0;">Source: {r['source_id']}</p>
</div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ---- Collision Simulator ----
    st.markdown("#### 🔬 Collision Simulator")
    st.markdown(
        "<p style='font-size:0.85rem; color:#94a3b8;'>"
        "Test what would happen if an external agent (doctor, pharmacist, insurer) "
        "submitted a specific query to your vault.</p>",
        unsafe_allow_html=True,
    )

    with st.form("collision_sim_form"):
        sim_query = st.text_input(
            "Simulated External Query",
            placeholder="e.g., 'Prescribe propranolol (beta-blocker)' or 'Request full substance history'",
        )
        sim_agent = st.text_input(
            "Requesting Agent",
            placeholder="e.g., 'Dr. Sarah Jenkins (GP)' or 'Insurance Assessor'",
        )
        run_sim = st.form_submit_button("⚡ Run Collision Check")

    if run_sim and sim_query:
        # Check against active tripwire rules
        collisions = []
        for rec in records:
            for rule in rec.get("tripwire_rules", []):
                # Simple substring match for demo
                if any(keyword in sim_query.lower() for keyword in rule.lower().split(":")):
                    collisions.append({
                        "rule": rule,
                        "category": rec["category"],
                        "clinical_relevance": rec.get("clinical_relevance", ""),
                    })

        if collisions:
            st.markdown(
                f"""<div class="premium-card" style="border-left: 5px solid #ef4444; background: rgba(239, 68, 68, 0.04); padding: 16px;">
<h4 style="margin: 0; color: #ef4444;">🚨 OPAQUE COLLISION DETECTED</h4>
<p style="font-size: 0.9rem; color: #ef4444; margin-top: 6px;">
<b>Agent:</b> {sim_agent or 'Unknown'}<br>
<b>Query:</b> {sim_query}<br>
<b>Collisions:</b> {len(collisions)} Veiled Assertion(s) triggered<br>
</p>
<p style="font-size:0.85rem; color:#f87171; margin-top:8px;">
<b>System Response to Agent:</b> "Warning: Query has triggered an Opaque Collision within the user's Veiled Graph.
The logical conclusion regarding this query cannot be guaranteed safe without user intervention."
</p>
</div>""",
                unsafe_allow_html=True,
            )
            for c in collisions:
                accent = SUB_ROSA_COLORS.get(SubRosaCategory(c["category"]), "#64748b")
                st.markdown(
                    f"""<div style="border-left:3px solid {accent}; padding:8px 12px; margin:6px 0; font-size:0.82rem;">
<b>Rule:</b> <code>{c['rule']}</code> |
<b>Domain:</b> <span style="color:{accent};">{c['category']}</span><br>
<b>Clinical Impact:</b> {c['clinical_relevance'] or 'Not specified'}
</div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """<div class="premium-card" style="border-left: 5px solid #10b981; padding: 16px;">
<h4 style="margin: 0; color: #10b981;">✅ No Collisions Detected</h4>
<p style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
This query does not intersect with any active Veiled Assertions. The standard response can be returned safely.
</p>
</div>""",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("#### 🤫 Full Threat Analysis")
    st.markdown(
        _card(
            "🔗 Sanctuary Mode Integration",
            "For full Synthesis Engine access (Contradiction Audits, Incoherence Reports, "
            "Sentinel Rulesets, Evidentiary Export, and Contingency Protocols), "
            "unlock <b>Sanctuary Mode</b> from the sidebar.",
            "#a855f7",
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# TAB 4 – Psychological Timeline
# ---------------------------------------------------------------------------

def _render_timeline_tab(dark_mode: bool):
    st.markdown("### 📊 Psychological Timeline")

    sessions = st.session_state.therapy_sessions
    sub_rosa = st.session_state.sub_rosa_records

    if not sessions and not sub_rosa:
        st.info("No data to display yet. Log therapy sessions or Sub Rosa records to populate the timeline.")
        return

    # ---- Mood trajectory ----
    if sessions:
        st.markdown("#### 🎯 Therapy Mood Trajectory")
        import plotly.graph_objects as go

        sorted_sessions = sorted(sessions, key=lambda x: x["date"])
        dates = [s["date"].strftime("%b %d") if isinstance(s["date"], datetime) else str(s["date"])
                 for s in sorted_sessions]
        mood_pre = [s["mood_pre"] for s in sorted_sessions]
        mood_post = [s["mood_post"] for s in sorted_sessions]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=mood_pre, name="Pre-Session",
            mode="lines+markers",
            line=dict(color="#ef4444", dash="dot"),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=mood_post, name="Post-Session",
            mode="lines+markers",
            line=dict(color="#10b981"),
            marker=dict(size=8),
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            template="plotly_dark" if dark_mode else "plotly_white",
            yaxis=dict(range=[0, 10], title="Mood (0-10)"),
            legend=dict(orientation="h", y=1.15),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---- Sub Rosa density ----
    if sub_rosa:
        st.markdown("#### 🌹 Sub Rosa Record Density")
        st.markdown(
            "<p style='font-size:0.82rem; color:#94a3b8;'>"
            "Shows the count of sealed records by category. Content is never revealed here.</p>",
            unsafe_allow_html=True,
        )

        cat_counts = {}
        for rec in sub_rosa:
            cat = rec["category"]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        cols = st.columns(min(len(cat_counts), 4))
        for i, (cat, count) in enumerate(cat_counts.items()):
            cat_enum = SubRosaCategory(cat)
            accent = SUB_ROSA_COLORS.get(cat_enum, "#64748b")
            with cols[i % len(cols)]:
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {accent}; padding: 12px; text-align: center;">
<div style="font-size:2rem; font-weight:800; color:{accent};">{count}</div>
<div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em; color:{accent};">{cat}</div>
</div>""",
                    unsafe_allow_html=True,
                )

    # ---- Combined event timeline ----
    st.markdown("#### 📅 Combined Event Log")

    events = []
    for s in sessions:
        events.append({
            "date": s["date"],
            "type": "Therapy",
            "icon": "🗣️",
            "label": f"{s['modality']} with {s.get('therapist', 'Unknown')}",
            "accent": "#8b5cf6",
        })
    for r in sub_rosa:
        events.append({
            "date": r["timestamp"],
            "type": "Sub Rosa",
            "icon": "🌹",
            "label": f"{r['category']} record sealed",
            "accent": SUB_ROSA_COLORS.get(SubRosaCategory(r["category"]), "#64748b"),
        })

    events.sort(key=lambda e: e["date"], reverse=True)

    for ev in events[:20]:
        dt = ev["date"]
        dt_str = dt.strftime("%b %d, %Y %H:%M") if isinstance(dt, datetime) else str(dt)
        st.markdown(
            f"""<div style="display:flex; align-items:center; gap:12px; padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.1);">
<span style="font-size:1.2rem;">{ev['icon']}</span>
<div>
<span style="font-size:0.82rem; color:{ev['accent']}; font-weight:600;">{ev['type']}</span>
<span style="font-size:0.78rem; color:#64748b; margin-left:8px;">{dt_str}</span>
<div style="font-size:0.78rem; color:#94a3b8;">{ev['label']}</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

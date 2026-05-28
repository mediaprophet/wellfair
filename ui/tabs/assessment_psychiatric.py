"""Assessments hub – Psychiatric screening forms, PDF upload, and RDF conversion.

This module renders the top-level **📝 Assessments** page.  The first sub-tab
is *Psychiatric* which surfaces the screening questionnaires found in the
``instructions/SCREENING FORMS PLS COMPLETE ALL/`` directory and any user-uploaded
PDFs.  Future sub-tabs (e.g. Neuropsychological, Physical) can be added here.
"""

import uuid
from datetime import date, datetime
from pathlib import Path

import streamlit as st

import src.utils as utils

# ---------------------------------------------------------------------------
# Known screening-form catalogue (from instructions folder)
# ---------------------------------------------------------------------------
KNOWN_FORMS = [
    {"code": "AAQoL",    "full_name": "Adult ADHD Quality of Life",          "category": "ADHD"},
    {"code": "ADRS",     "full_name": "ADHD Rating Scale (Other-Report)",    "category": "ADHD"},
    {"code": "AQ-10",    "full_name": "Autism Spectrum Quotient (10-item)",   "category": "Autism"},
    {"code": "ATTACHMENT","full_name": "Attachment Style Questionnaire",      "category": "Developmental"},
    {"code": "BDI-II",   "full_name": "Beck Depression Inventory II",        "category": "Depression"},
    {"code": "BIS-II",   "full_name": "Barratt Impulsiveness Scale II",      "category": "Impulsivity"},
    {"code": "CCSM",     "full_name": "Clinical Case Summary Measure",       "category": "General"},
    {"code": "DAST",     "full_name": "Drug Abuse Screening Test",           "category": "Substance Use"},
    {"code": "DES",      "full_name": "Dissociative Experiences Scale",       "category": "Dissociation"},
    {"code": "DIVA5.0",  "full_name": "Diagnostic Interview for ADHD (5.0)", "category": "ADHD"},
    {"code": "ETI-SR-SF","full_name": "Early Trauma Inventory (Self-Report Short Form)", "category": "Trauma"},
    {"code": "HSP",      "full_name": "Highly Sensitive Person Scale",        "category": "Sensory"},
    {"code": "MAIA-2",   "full_name": "Multidimensional Assessment of Interoceptive Awareness 2", "category": "Interoception"},
    {"code": "MAST",     "full_name": "Michigan Alcohol Screening Test",     "category": "Substance Use"},
    {"code": "MDQ",      "full_name": "Mood Disorder Questionnaire",          "category": "Bipolar"},
    {"code": "OCI-R",    "full_name": "Obsessive-Compulsive Inventory – Revised", "category": "OCD"},
    {"code": "SLEEP",    "full_name": "Sleep Quality Assessment",             "category": "Sleep"},
    {"code": "WFIRS-S",  "full_name": "Weiss Functional Impairment Rating Scale – Self-Report", "category": "ADHD"},
    {"code": "WRAADDS",  "full_name": "Wender-Reimherr Adult ADD Scale",     "category": "ADHD"},
    {"code": "WURS",     "full_name": "Wender Utah Rating Scale",             "category": "ADHD"},
    {"code": "ZAN-BPD",  "full_name": "Zanarini Rating Scale for BPD",        "category": "Personality"},
]

SCREENING_DIR = utils.PROJECT_ROOT / "instructions" / "SCREENING FORMS PLS COMPLETE ALL"


def _card(title: str, body: str, accent: str = "#6366f1") -> str:
    """Return an HTML premium-card snippet."""
    return f"""
<div class="premium-card" style="border-left: 5px solid {accent}; margin-bottom: 16px;">
    <h4 style="margin: 0; color: {accent};">{title}</h4>
    <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 6px;">{body}</div>
</div>"""


def render_psychiatric_assessments(dark_mode: bool):
    """Top-level Assessments page with sub-tabs."""

    st.markdown("## 📝 Assessments")
    st.markdown(
        _card(
            "🛡️ Assessment Vault",
            "Upload completed screening forms (PDF), review results over time, and "
            "prepare structured RDF data for your Personal Health Record.  "
            "All data stays under your sovereign control.",
            "#6366f1",
        ),
        unsafe_allow_html=True,
    )

    # ---- Sub-tabs ----
    tab_psych, tab_upload, tab_history = st.tabs([
        "🧠 Psychiatric Screening Forms",
        "📤 Upload & Process PDF",
        "📊 Assessment History",
    ])

    # ------------------------------------------------------------------
    # TAB 1 – Catalogue of known psychiatric forms
    # ------------------------------------------------------------------
    with tab_psych:
        st.markdown("### Known Screening Instruments")
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.85rem;'>"
            "The following questionnaires were identified from the clinical intake pack.  "
            "Click <b>View PDF</b> to open the original form (if available locally).</p>",
            unsafe_allow_html=True,
        )

        # Collect unique categories for filtering
        categories = sorted({f["category"] for f in KNOWN_FORMS})
        selected_cats = st.multiselect(
            "Filter by category",
            options=categories,
            default=categories,
            key="assess_cat_filter",
        )

        filtered = [f for f in KNOWN_FORMS if f["category"] in selected_cats]

        # Render in a 3-column grid
        cols = st.columns(3)
        for i, form in enumerate(filtered):
            col = cols[i % 3]
            pdf_path = SCREENING_DIR / f"{form['code']}.pdf"
            pdf_exists = pdf_path.is_file()

            cat_colors = {
                "ADHD": "#f59e0b", "Autism": "#06b6d4", "Depression": "#6366f1",
                "Impulsivity": "#ec4899", "General": "#64748b", "Substance Use": "#ef4444",
                "Dissociation": "#8b5cf6", "Trauma": "#f43f5e", "Sensory": "#14b8a6",
                "Interoception": "#0ea5e9", "Bipolar": "#a855f7", "OCD": "#d946ef",
                "Sleep": "#3b82f6", "Personality": "#e11d48", "Developmental": "#10b981",
            }
            accent = cat_colors.get(form["category"], "#64748b")

            with col:
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {accent}; padding: 12px 16px; min-height: 110px;">
<span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: {accent};">{form['category']}</span>
<h4 style="margin: 4px 0 2px 0; font-size: 1rem;">{form['code']}</h4>
<p style="font-size: 0.8rem; color: #94a3b8; margin: 0;">{form['full_name']}</p>
{'<p style="margin:6px 0 0 0;font-size:0.75rem;">📄 PDF available locally</p>' if pdf_exists else '<p style="margin:6px 0 0 0;font-size:0.75rem;color:#475569;">⬜ PDF not found locally</p>'}
</div>""",
                    unsafe_allow_html=True,
                )

    # ------------------------------------------------------------------
    # TAB 2 – Upload & process a PDF
    # ------------------------------------------------------------------
    with tab_upload:
        st.markdown("### Upload a Completed Assessment PDF")
        st.markdown(
            _card(
                "📤 PDF → Structured Data Pipeline",
                "Upload a completed screening form.  The system will store the PDF, "
                "extract the questionnaire type from the filename, and create a "
                "structured record ready for RDF serialisation.",
                "#0ea5e9",
            ),
            unsafe_allow_html=True,
        )

        # Initialise session state container
        if "psychiatric_assessments" not in st.session_state:
            st.session_state.psychiatric_assessments = []

        with st.form("upload_assessment_form", clear_on_submit=True):
            uploaded = st.file_uploader(
                "Select PDF file",
                type=["pdf"],
                key="psych_pdf_upload",
            )
            assess_date = st.date_input("Date assessment was completed", value=date.today())
            notes = st.text_area("Notes (optional)", placeholder="e.g. completed during intake session with Dr. X")
            submitted = st.form_submit_button("Upload & Create Record", type="primary")

        if submitted and uploaded is not None:
            uri = utils.save_uploaded_pdf(uploaded)
            raw_name = uploaded.name.rsplit(".", 1)[0]
            # Try to match against known forms
            matched = next((f for f in KNOWN_FORMS if f["code"].upper() == raw_name.upper()), None)
            display_name = matched["full_name"] if matched else raw_name
            category = matched["category"] if matched else "Uncategorised"

            new_record = {
                "id": str(uuid.uuid4()),
                "code": matched["code"] if matched else raw_name,
                "name": display_name,
                "category": category,
                "date_taken": assess_date.isoformat(),
                "pdf_uri": uri,
                "notes": notes,
                "scores": {},
                "rdf_status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            st.session_state.psychiatric_assessments.append(new_record)
            st.success(f"✅ Created assessment record: **{display_name}** ({category})")
            st.rerun()

    # ------------------------------------------------------------------
    # TAB 3 – Assessment History & Score Entry
    # ------------------------------------------------------------------
    with tab_history:
        st.markdown("### Assessment History")

        assessments = st.session_state.get("psychiatric_assessments", [])

        if not assessments:
            st.info("No assessments uploaded yet.  Use the **Upload & Process PDF** tab to add one.")
        else:
            st.markdown(
                f"<p style='color:#94a3b8;font-size:0.85rem;'>"
                f"Showing <b>{len(assessments)}</b> assessment record(s).</p>",
                unsafe_allow_html=True,
            )

            for idx, rec in enumerate(assessments):
                accent = "#6366f1" if rec.get("rdf_status") == "pending" else "#10b981"
                rdf_badge = (
                    "🟡 RDF Pending" if rec.get("rdf_status") == "pending"
                    else "🟢 RDF Generated"
                )
                with st.expander(
                    f"{rec['code']} – {rec['name']}  |  {rec['date_taken']}  |  {rdf_badge}",
                    expanded=False,
                ):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Category:** {rec.get('category', '—')}")
                        st.markdown(f"**Date Taken:** {rec['date_taken']}")
                        if rec.get("notes"):
                            st.markdown(f"**Notes:** {rec['notes']}")
                    with c2:
                        st.markdown(f"**RDF Status:** {rdf_badge}")
                        st.markdown(f"**Record ID:** `{rec['id'][:8]}…`")

                    st.divider()

                    # Score entry
                    st.markdown("#### Scores / Responses")
                    scores = rec.get("scores", {})
                    if scores:
                        st.table([{"Item": k, "Value": v} for k, v in scores.items()])

                    with st.form(f"score_form_{idx}", clear_on_submit=True):
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            new_key = st.text_input("Item / Question ID", key=f"skey_{idx}")
                        with sc2:
                            new_val = st.text_input("Score / Response", key=f"sval_{idx}")
                        if st.form_submit_button("Add / Update Score") and new_key:
                            try:
                                scores[new_key] = float(new_val) if new_val else None
                            except ValueError:
                                scores[new_key] = new_val
                            rec["scores"] = scores
                            st.success(f"Updated **{new_key}**")
                            st.rerun()

                    # Actions row
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        if st.button("🗑️ Delete Record", key=f"del_{idx}"):
                            del st.session_state.psychiatric_assessments[idx]
                            st.rerun()
                    with ac2:
                        if rec.get("rdf_status") == "pending":
                            if st.button("🔄 Generate RDF", key=f"rdf_{idx}"):
                                rec["rdf_status"] = "generated"
                                st.success("RDF stub generated (placeholder)")
                                st.rerun()
                    with ac3:
                        st.markdown(f"[📄 Open PDF]({rec.get('pdf_uri', '#')})")

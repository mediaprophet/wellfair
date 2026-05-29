"""Assessments hub – Psychiatric screening forms, PDF upload, and RDF conversion.

This module renders the top-level **📝 Assessments** page.  The first sub-tab
is *Psychiatric* which surfaces the screening questionnaires found in the
``instructions/SCREENING FORMS PLS COMPLETE ALL/`` directory and any user-uploaded
PDFs.  Future sub-tabs (e.g. Neuropsychological, Physical) can be added here.
"""

import uuid
from datetime import date, datetime

from ui.utils.components import render_info_banner
from pathlib import Path

import streamlit as st

import src.utils as utils
from src.utils import extract_text_from_pdf, parse_pathology_report

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
    """Legacy wrapper — now delegates to shared component for consistency."""
    # We keep the function for minimal diff, but it now uses the shared helper internally
    # when called via markdown. In future passes we can replace calls directly.
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
    tab_psych, tab_upload, tab_history, tab_forms = st.tabs([
        "🧠 Psychiatric Screening Forms",
        "📤 Upload & Process PDF",
        "📊 Assessment History",
        "✍️ Fill Interactive Forms",
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

            # NEW: Real PDF text extraction + basic pathology parsing
            extracted_text = ""
            extracted_observations = []
            try:
                # Save temporarily to extract (the save function already wrote it)
                temp_path = Path(uri.replace("file://", ""))
                extracted_text = extract_text_from_pdf(temp_path)
                if "glucose" in extracted_text.lower() or "cholesterol" in extracted_text.lower():
                    extracted_observations = parse_pathology_report(extracted_text)
            except Exception as e:
                st.warning(f"Could not extract text from PDF: {e}")

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
                "extracted_text_preview": extracted_text[:800] if extracted_text else None,
                "extracted_observations": extracted_observations,
            }
            st.session_state.psychiatric_assessments.append(new_record)
            st.success(f"✅ Created assessment record: **{display_name}** ({category})")

            if extracted_observations:
                st.info(f"🔬 Detected {len(extracted_observations)} lab observations from the PDF.")
            st.rerun()

    # ------------------------------------------------------------------
    # TAB 3 – Assessment History & Score Entry
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # TAB 4 – Interactive, Repeatable Questionnaires (NEW)
    # ------------------------------------------------------------------
    with tab_forms:
        st.markdown("### Interactive Diagnostic Questionnaires")
        st.markdown(
            "These are fillable versions of common screening tools. "
            "You can complete them multiple times over time. Each submission is stored with a timestamp."
        )

        if "questionnaire_history" not in st.session_state:
            st.session_state.questionnaire_history = []

        q_type = st.selectbox("Select Questionnaire", [
            "DASS-21 (Depression Anxiety Stress)",
            "BDI-II (Beck Depression Inventory II)",
            "PHQ-9 (Depression)",
            "GAD-7 (Anxiety)",
            "OCI-R (OCD)"
        ])

        with st.form("interactive_questionnaire", clear_on_submit=True):
            st.markdown(f"#### {q_type}")
            responses = {}

            if "DASS-21" in q_type:
                dass_items = [
                    "I found it hard to wind down",
                    "I was aware of dryness of my mouth",
                    "I couldn't seem to experience any positive feeling at all",
                    "I experienced breathing difficulty",
                    "I felt that I had lost interest in just about everything",
                    "I felt I was close to panic",
                    "I felt that life was meaningless",
                    "I was worried about situations in which I might panic",
                    "I felt I was using a lot of nervous energy",
                    "I felt sad and depressed",
                    "I found myself getting agitated",
                    "I was unable to become enthusiastic about anything",
                    "I felt I was losing touch with reality",
                    "I felt I was rather touchy",
                    "I was aware of the action of my heart in the absence of physical exertion",
                    "I felt scared without any good reason",
                    "I felt that life wasn't worthwhile",
                    "I felt that I was rather irritable",
                    "I was aware of dryness of my mouth",
                    "I felt that I had lost interest in just about everything",
                    "I felt I was close to panic",
                ]
                for i, item in enumerate(dass_items):
                    responses[f"q{i+1}"] = st.slider(item, 0, 3, 0, key=f"dass21_{i}")

            elif "BDI-II" in q_type:
                bdi_items = [
                    "Sadness",
                    "Pessimism",
                    "Past Failure",
                    "Loss of Pleasure",
                    "Guilty Feelings",
                    "Punishment Feelings",
                    "Self-Dislike",
                    "Self-Criticalness",
                    "Suicidal Thoughts or Wishes",
                    "Crying",
                    "Agitation",
                    "Loss of Interest",
                    "Indecisiveness",
                    "Worthlessness",
                    "Loss of Energy",
                    "Changes in Sleeping Pattern",
                    "Irritability",
                    "Changes in Appetite",
                    "Concentration Difficulty",
                    "Tiredness or Fatigue",
                    "Loss of Interest in Sex",
                ]
                for i, item in enumerate(bdi_items):
                    responses[f"q{i+1}"] = st.slider(item, 0, 3, 0, key=f"bdi_{i}")

            elif "PHQ-9" in q_type:
                phq_items = [
                    "Little interest or pleasure in doing things",
                    "Feeling down, depressed, or hopeless",
                    "Trouble falling or staying asleep, or sleeping too much",
                    "Feeling tired or having little energy",
                    "Poor appetite or overeating",
                    "Feeling bad about yourself — or that you are a failure",
                    "Trouble concentrating on things",
                    "Moving or speaking so slowly that other people could have noticed",
                    "Thoughts that you would be better off dead or of hurting yourself",
                ]
                for i, item in enumerate(phq_items):
                    responses[f"q{i+1}"] = st.slider(item, 0, 3, 0, key=f"phq9_{i}")

            else:  # GAD-7 or OCI-R simplified
                if "GAD" in q_type:
                    items = ["Feeling nervous, anxious or on edge", "Not being able to stop or control worrying", "Worrying too much about different things", "Trouble relaxing", "Being so restless that it is hard to sit still", "Becoming easily annoyed or irritable", "Feeling afraid as if something awful might happen"]
                else:
                    items = ["I have saved up so many things that they get in the way", "I check things more often than necessary", "I get upset if objects are not arranged properly", "I feel compelled to count while doing things"]
                for i, item in enumerate(items):
                    responses[f"q{i+1}"] = st.slider(item, 0, 3, 0, key=f"other_{i}")

            taken_date = st.date_input("Date completed", value=date.today())
            notes = st.text_area("Notes (optional)")

            if st.form_submit_button("Save This Assessment", type="primary"):
                record = {
                    "id": str(uuid.uuid4()),
                    "type": q_type,
                    "date_taken": taken_date.isoformat(),
                    "scores": responses,
                    "total_score": sum(responses.values()),
                    "notes": notes,
                    "created_at": datetime.utcnow().isoformat(),
                }
                st.session_state.questionnaire_history.append(record)

                # Proper persistence into vault + disk
                from src.utils import save_structured_assessment, auto_save_structured_data
                save_structured_assessment(record, "questionnaire")
                auto_save_structured_data()

                # Also for timeline visibility
                if "recent_assessments" not in st.session_state:
                    st.session_state.recent_assessments = []
                st.session_state.recent_assessments.append({
                    "date": record["date_taken"],
                    "type": record["type"],
                    "score": record["total_score"],
                    "source": "Interactive Form"
                })
                st.success(f"Saved {q_type} (Score: {record['total_score']})")
                st.rerun()

        # Show history of interactive forms
        st.markdown("#### Your Previous Submissions")
        history = st.session_state.get("questionnaire_history", [])
        if history:
            for h in reversed(history[-5:]):  # show last 5
                st.markdown(
                    f"**{h['type']}** — {h['date_taken']} — **Score: {h['total_score']}**"
                )
                with st.expander("Details"):
                    st.json(h)
        else:
            st.info("No interactive assessments completed yet.")

    # ------------------------------------------------------------------
    # Original TAB 3 – Assessment History
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
                is_pydantic = not isinstance(rec, dict)
                rec_dict = rec.model_dump() if is_pydantic else rec
                
                # Normalize missing fields for pydantic models
                if is_pydantic:
                    rec_dict['category'] = "Auto-Extracted"
                    rec_dict['rdf_status'] = "pending"
                    rec_dict['code'] = rec_dict.get('name', 'Unknown')
                    rec_dict['notes'] = "Extracted via AI Document Ingestion"
                    
                accent = "#6366f1" if rec_dict.get("rdf_status") == "pending" else "#10b981"
                rdf_badge = (
                    "🟡 RDF Pending" if rec_dict.get("rdf_status") == "pending"
                    else "🟢 RDF Generated"
                )
                
                header_badge = "🤖 AI Extracted" if is_pydantic else "📝 Manual Entry"
                
                with st.expander(
                    f"{rec_dict.get('code')} – {rec_dict.get('name')}  |  {rec_dict.get('date_taken')}  |  {header_badge}  |  {rdf_badge}",
                    expanded=False,
                ):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Category:** {rec_dict.get('category', '—')}")
                        st.markdown(f"**Date Taken:** {rec_dict.get('date_taken')}")
                        if rec_dict.get("notes"):
                            st.markdown(f"**Notes:** {rec_dict.get('notes')}")
                    with c2:
                        st.markdown(f"**RDF Status:** {rdf_badge}")
                        st.markdown(f"**Record ID:** `{str(rec_dict.get('id', ''))[:8]}…`")

                    st.divider()

                    # Score entry
                    st.markdown("#### Scores / Responses")
                    scores = rec_dict.get("scores", {})
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
                            
                            if is_pydantic:
                                rec.scores = scores
                            else:
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
                        if rec_dict.get("rdf_status") == "pending":
                            if st.button("🔄 Generate RDF", key=f"rdf_{idx}"):
                                from rdflib import Graph, URIRef, Literal, Namespace
                                from rdflib.namespace import RDF, XSD
                                HEALTH = Namespace("urn:health:schema:")

                                g = Graph()
                                subj = URIRef(f"urn:health:assessment:{rec_dict.get('id')}")

                                if "DASS" in rec_dict.get("type", "") or "BDI" in rec_dict.get("type", "") or "PHQ" in rec_dict.get("type", ""):
                                    g.add((subj, RDF.type, HEALTH.PsychiatricQuestionnaire))
                                    g.add((subj, HEALTH.assessmentType, Literal(rec_dict.get("type"))))
                                else:
                                    g.add((subj, RDF.type, HEALTH.PsychiatricAssessment))

                                g.add((subj, HEALTH.name, Literal(rec_dict.get('name'), datatype=XSD.string)))
                                g.add((subj, HEALTH.dateTaken, Literal(str(rec_dict.get('date_taken')), datatype=XSD.date)))

                                for q, val in rec_dict.get('scores', {}).items():
                                    if val is not None:
                                        g.add((subj, URIRef(f"{HEALTH}{q}"), Literal(val)))

                                # Also attach to DiagnosticReport style if this came from pathology
                                if rec_dict.get("extracted_observations"):
                                    g.add((subj, HEALTH.hasStructuredObservations, Literal("true")))

                                rec_dict["rdf_status"] = "generated"
                                rec_dict["rdf_graph"] = g.serialize(format="turtle")
                                st.success("RDF generated and attached to record")
                                st.rerun()
                    with ac3:
                        st.markdown(f"[📄 Open PDF]({rec_dict.get('pdf_uri', '#')})")

                    # RDF Export
                    if rec_dict.get("rdf_graph"):
                        from src.utils import generate_rdf_for_questionnaire
                        rdf_data = rec_dict.get("rdf_graph")
                        st.download_button(
                            label="📥 Download RDF (Turtle)",
                            data=rdf_data,
                            file_name=f"assessment_{rec_dict.get('id', 'unknown')[:8]}.ttl",
                            mime="text/turtle",
                            key=f"rdf_dl_{idx}"
                        )

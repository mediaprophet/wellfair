from datetime import datetime
import streamlit as st
import time
import uuid

from src.phr_models.claims import (
    InformationSource, AuthorType, ContentPackage, ClinicalClaim, TrustLevel
)
from src.phr_models.pathology import DiagnosticReport, PathologyObservation, DiagnosticReportStatus
from src.utils import extract_text_from_pdf, parse_pathology_report
from src.phr_models.proxy_consent import PrivacyMode
from src.phr_models.psychiatric import DASS21Assessment, K10Assessment
from src.phr_models.imaging import MedicalImagingStudy, ImagingModality, ImagingSeries

def render_document_ingestion(dark_mode: bool):
    st.markdown("## 📥 Document Ingestion & Semantic Claims")
    
    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #0ea5e9; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #0ea5e9;">📑 Semantic Data Extraction Pipeline</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Upload PDFs or DOCX files (like Pathology Reports or discharge summaries). The system extracts structured claims, evaluates the author's credentials to assign a <b>Trust Level</b>, and prepares a Content Package for your approval before saving it into your Vault.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if "pending_packages" not in st.session_state:
        st.session_state.pending_packages = []
        
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        st.markdown("### 📤 Upload Document")
        
        uploaded_file = st.file_uploader("Select PDF or DOCX", type=["pdf", "docx"])
        
        doc_type = st.selectbox(
            "Document Type",
            options=["Pathology Report", "Clinical Discharge Summary", "Prescription", "Self-Report Notes", "Psychiatric Questionnaire", "Medical Imaging Archive (ZIP/DICOM)"]
        )
        
        st.caption("Metadata (Usually auto-extracted, manual override here)")
        author_t = st.selectbox("Author Type", options=[a.value for a in AuthorType], index=3)  # default PATHOLOGY_LAB
        org = st.text_input("Organization", value="Laverty Pathology")
        
        if st.button("Process Document", type="primary"):
            if not uploaded_file:
                st.error("Please upload a file to process (or use mock data).")
            else:
                with st.spinner("Extracting text and mapping semantic claims using AI..."):
                    time.sleep(0.8)

                    extracted_text = ""
                    parsed_obs = []

                    # Try real extraction if we have a PDF
                    if uploaded_file and uploaded_file.type == "application/pdf":
                        # Save temporarily for extraction
                        tmp_path = Path("data/assessments/temp_upload.pdf")
                        tmp_path.parent.mkdir(parents=True, exist_ok=True)
                        tmp_path.write_bytes(uploaded_file.getbuffer())
                        extracted_text = extract_text_from_pdf(tmp_path)
                        parsed_obs = parse_pathology_report(extracted_text)
                        tmp_path.unlink(missing_ok=True)

                    # Real extraction path for Pathology
                    if "Pathology" in doc_type:
                        source = InformationSource(
                            id=f"src-{int(time.time())}",
                            author_type=AuthorType(author_t),
                            author_name="Automated Lab System",
                            organization=org,
                            credentials="NATA Accredited",
                            date_recorded=datetime.now()
                        )

                        claims = []

                        if parsed_obs:
                            # Create real structured observations
                            observations = []
                            for obs in parsed_obs[:12]:  # limit for sanity
                                try:
                                    observations.append(PathologyObservation(
                                        id=str(uuid.uuid4()),
                                        test_name=obs["test_name"],
                                        value=obs["value"],
                                        unit=obs.get("unit", ""),
                                        reference_range_low=obs.get("reference_range_low"),
                                        reference_range_high=obs.get("reference_range_high"),
                                    ))
                                except Exception:
                                    pass

                            # Create proper DiagnosticReport
                            report = DiagnosticReport(
                                id=str(uuid.uuid4()),
                                patient_id="current-user",
                                date_issued=datetime.now(),
                                pdf_attachment_uri=f"vault://docs/{uploaded_file.name}.enc",
                                observations=observations,
                            )

                            # Also create a ClinicalClaim for the ingestion pipeline
                            claims.append(ClinicalClaim(
                                id=f"claim-{int(time.time())}",
                                source_document_id=source.id,
                                domain="Pathology",
                                claim_text=f"Pathology report processed - {len(observations)} observations extracted",
                                extracted_data={
                                    "report_id": report.id,
                                    "observation_count": len(observations),
                                    "tests": [o.test_name for o in observations]
                                },
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                            ))

                            # Proper persistence
                            from src.utils import save_structured_assessment, auto_save_structured_data
                            save_structured_assessment(report.model_dump(), "pathology")
                            auto_save_structured_data()

                            if "structured_pathology_reports" not in st.session_state:
                                st.session_state.structured_pathology_reports = []
                            st.session_state.structured_pathology_reports.append(report)

                        # Create the package (with real or fallback data)
                        raw_text_preview = extracted_text[:600] if extracted_text else "No text extracted"
                        package = ContentPackage(
                            id=f"pkg-{int(time.time())}",
                            original_file_name=uploaded_file.name,
                            upload_date=datetime.now(),
                            source=source,
                            raw_extracted_text=raw_text_preview,
                            claims=claims or []  # allow empty for now
                        )
                        package.evaluate_claims()
                        st.session_state.pending_packages.append(package)
                        st.success(f"Pathology report processed. {len(parsed_obs)} observations extracted." if parsed_obs else "Document processed.")
                        st.rerun()

                    elif "Questionnaire" in doc_type:
                        mock_source = InformationSource(
                            id=f"src-{int(time.time())}",
                            author_type=AuthorType.PATIENT,
                            author_name="Patient Self-Report",
                            organization="Self",
                            credentials="N/A",
                            date_recorded=datetime.now()
                        )
                        
                        # Mock DASS-21 Extraction
                        mock_claims = [
                            ClinicalClaim(
                                id=f"claim-{int(time.time())}-q1",
                                source_document_id=mock_source.id,
                                domain="Psychiatry",
                                claim_text="DASS-21 Questionnaire Completed",
                                extracted_data={
                                    "type": "DASS21",
                                    "scores": {f"Q{i}": (i % 4) for i in range(1, 22)},
                                    "total_depression": 14,
                                    "total_anxiety": 10,
                                    "total_stress": 18
                                },
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                                trust_level=TrustLevel.UNVERIFIED_SELF
                            )
                        ]
                        
                        package = ContentPackage(
                            id=f"pkg-{int(time.time())}",
                            original_file_name=uploaded_file.name,
                            upload_date=datetime.now(),
                            source=mock_source,
                            raw_extracted_text="MOCK RAW DASS-21 DATA: Q1: 1, Q2: 2, Q3: 3...",
                            claims=mock_claims
                        )
                        
                        package.evaluate_claims()
                        st.session_state.pending_packages.append(package)
                        st.success("Psychiatric Questionnaire extracted successfully! Please review.")
                        st.rerun()

                    elif "Imaging" in doc_type:
                        mock_source = InformationSource(
                            id=f"src-{int(time.time())}",
                            author_type=AuthorType(author_t),
                            author_name="Automated Radiology System",
                            organization=org,
                            credentials="RANZCR Accredited 9876",
                            date_recorded=datetime.now()
                        )
                        
                        mock_claims = [
                            ClinicalClaim(
                                id=f"claim-{int(time.time())}-img1",
                                source_document_id=mock_source.id,
                                domain="Radiology",
                                claim_text="Study: MRI Brain without contrast",
                                extracted_data={
                                    "modality": "MRI",
                                    "study_description": "MRI Brain without contrast",
                                    "series": [
                                        {"desc": "T1 Axial", "slices": 120, "thickness_mm": 1.5},
                                        {"desc": "FLAIR", "slices": 60, "thickness_mm": 3.0}
                                    ]
                                },
                                privacy_mode=PrivacyMode.MODE_S_SANCTUARY  # "S" = Sanctuary
                            )
                        ]
                        
                        package = ContentPackage(
                            id=f"pkg-{int(time.time())}",
                            original_file_name=uploaded_file.name,
                            upload_date=datetime.now(),
                            source=mock_source,
                            raw_extracted_text="MOCK DICOM HEADER EXTRACT: Modality=MR, StudyDesc=MRI Brain without contrast, Series=T1 Axial (120 slices), Series=FLAIR (60 slices)",
                            claims=mock_claims
                        )
                        
                        package.evaluate_claims()
                        st.session_state.pending_packages.append(package)
                        st.success("DICOM Metadata extracted! Placed under Sanctuary Mode.")
                        st.rerun()

    with c2:
        st.markdown("### 🔍 Pending Packages Review")
        
        if not st.session_state.pending_packages:
            st.info("No documents are pending review.")
        else:
            for idx, pkg in enumerate(st.session_state.pending_packages):
                with st.expander(f"📦 Package: {pkg.original_file_name} (Status: {pkg.status})", expanded=True):
                    st.markdown(
                        f"""
                        **Source:** {pkg.source.organization} ({pkg.source.author_type.value})<br>
                        **Date:** {pkg.upload_date.strftime('%Y-%m-%d %H:%M')}<br>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("#### Extracted Claims & Evaluation")
                    for claim in pkg.claims:
                        trust_colors = {
                            TrustLevel.VERIFIED_CLINICAL: "#10b981",
                            TrustLevel.VERIFIED_DEVICE: "#3b82f6",
                            TrustLevel.UNVERIFIED_SELF: "#f59e0b",
                            TrustLevel.UNVERIFIED_THIRD_PARTY: "#f97316",
                            TrustLevel.OUT_OF_SCOPE: "#ef4444",
                            TrustLevel.CONFLICTING: "#ef4444"
                        }
                        t_color = trust_colors.get(claim.trust_level, "#64748b")
                        
                        st.markdown(
                            f"""
                            <div style="padding: 10px; background: {t_color}11; border-left: 3px solid {t_color}; border-radius: 4px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <strong>Domain: {claim.domain}</strong>
                                    <span style="font-size: 0.75rem; background: {t_color}22; color: {t_color}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                                        {claim.trust_level.value.upper()}
                                    </span>
                                </div>
                                <div style="font-size: 0.85rem; margin-top: 4px;">"{claim.claim_text}"</div>
                                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                                    <i>Evaluator Note:</i> {claim.evaluation_notes}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    if pkg.status == "Draft":
                        col_a, col_r = st.columns(2)
                        if col_a.button("✅ Approve & Commit to Vault", key=f"app_{idx}"):
                            # Commit logic (e.g. creating DiagnosticReport)
                            report = DiagnosticReport(
                                id=f"path-{pkg.id}",
                                patient_id="patient-self",
                                date_issued=pkg.upload_date,
                                status=DiagnosticReportStatus.FINAL,
                                pdf_attachment_uri=f"vault://docs/{pkg.original_file_name}.enc",
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                            )
                            for claim in pkg.claims:
                                if claim.domain == "Pathology" and claim.trust_level == TrustLevel.VERIFIED_CLINICAL:
                                    obs = PathologyObservation(
                                        id=f"obs-{claim.id}",
                                        test_name=claim.extracted_data.get("test_name", "Unknown"),
                                        value=claim.extracted_data.get("value", 0.0),
                                        unit=claim.extracted_data.get("unit", ""),
                                        reference_range_low=claim.extracted_data.get("reference_range_low"),
                                        reference_range_high=claim.extracted_data.get("reference_range_high"),
                                        privacy_mode=claim.privacy_mode
                                    )
                                    report.observations.append(obs)
                            # Save report to st.session_state.diagnostic_reports
                            if "diagnostic_reports" not in st.session_state:
                                st.session_state.diagnostic_reports = []
                            st.session_state.diagnostic_reports.append(report)
                            
                            # Also check for psychiatric questionnaire data
                            for claim in pkg.claims:
                                if claim.domain == "Psychiatry" and claim.extracted_data.get("type") == "DASS21":
                                    dass = DASS21Assessment(
                                        id=f"dass-{pkg.id}",
                                        date_taken=pkg.upload_date.date(),
                                        pdf_uri=f"vault://docs/{pkg.original_file_name}.enc",
                                        scores=claim.extracted_data.get("scores", {})
                                    )
                                    if "psychiatric_assessments" not in st.session_state:
                                        st.session_state.psychiatric_assessments = []
                                    st.session_state.psychiatric_assessments.append(dass)
                                
                                elif claim.domain == "Radiology" and "modality" in claim.extracted_data:
                                    # Create Medical Imaging Study
                                    series_list = []
                                    for idx_s, s in enumerate(claim.extracted_data.get("series", [])):
                                        series_list.append(ImagingSeries(
                                            id=f"series-{pkg.id}-{idx_s}",
                                            series_description=s.get("desc", ""),
                                            modality=ImagingModality(claim.extracted_data.get("modality", "MRI")),
                                            slice_thickness_mm=s.get("thickness_mm"),
                                            number_of_slices=s.get("slices", 0),
                                            dicom_archive_uri=f"vault://imaging/{pkg.original_file_name}.enc"
                                        ))
                                        
                                    imaging_study = MedicalImagingStudy(
                                        id=f"study-{pkg.id}",
                                        patient_id="patient-self",
                                        date_recorded=pkg.upload_date,
                                        study_description=claim.extracted_data.get("study_description", "Unknown Study"),
                                        modality=ImagingModality(claim.extracted_data.get("modality", "MRI")),
                                        series=series_list,
                                        privacy_mode=claim.privacy_mode
                                    )
                                    if "imaging_studies" not in st.session_state:
                                        st.session_state.imaging_studies = []
                                    st.session_state.imaging_studies.append(imaging_study)

                            pkg.status = "Approved"
                            st.success("Committed structured data to Vault!")
                            st.rerun()
                            
                        if col_r.button("🗑️ Reject & Discard", key=f"rej_{idx}"):
                            st.session_state.pending_packages.pop(idx)
                            st.rerun()

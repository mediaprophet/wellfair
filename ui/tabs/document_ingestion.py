from datetime import datetime
import streamlit as st
import time

from src.phr_models.claims import (
    InformationSource, AuthorType, ContentPackage, ClinicalClaim, TrustLevel
)
from src.phr_models.pathology import DiagnosticReport, PathologyObservation, DiagnosticReportStatus
from src.phr_models.proxy_consent import PrivacyMode

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
            options=["Pathology Report", "Clinical Discharge Summary", "Prescription", "Self-Report Notes"]
        )
        
        st.caption("Metadata (Usually auto-extracted, manual override here)")
        author_t = st.selectbox("Author Type", options=[a.value for a in AuthorType], index=3)  # default PATHOLOGY_LAB
        org = st.text_input("Organization", value="Laverty Pathology")
        
        if st.button("Process Document", type="primary"):
            if not uploaded_file:
                st.error("Please upload a file to process (or use mock data).")
            else:
                with st.spinner("Extracting text and mapping semantic claims using AI..."):
                    time.sleep(1.5)  # Simulate processing delay
                    
                    # Mocking the extraction pipeline based on standard Pathology
                    if "Pathology" in doc_type:
                        mock_source = InformationSource(
                            id=f"src-{int(time.time())}",
                            author_type=AuthorType(author_t),
                            author_name="Automated Lab System",
                            organization=org,
                            credentials="NATA Accredited 12345",
                            date_recorded=datetime.now()
                        )
                        
                        mock_claims = [
                            ClinicalClaim(
                                id=f"claim-{int(time.time())}-1",
                                source_document_id=mock_source.id,
                                domain="Pathology",
                                claim_text="Fasting Blood Glucose: 5.4 mmol/L (Range 3.0-5.4)",
                                extracted_data={
                                    "test_name": "Blood Glucose (Fasting)",
                                    "value": 5.4,
                                    "unit": "mmol/L",
                                    "reference_range_low": 3.0,
                                    "reference_range_high": 5.4
                                },
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                            ),
                            ClinicalClaim(
                                id=f"claim-{int(time.time())}-2",
                                source_document_id=mock_source.id,
                                domain="Pathology",
                                claim_text="Total Cholesterol: 6.1 mmol/L (Range < 5.5)",
                                extracted_data={
                                    "test_name": "Total Cholesterol",
                                    "value": 6.1,
                                    "unit": "mmol/L",
                                    "reference_range_high": 5.5
                                },
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                            ),
                            ClinicalClaim(
                                id=f"claim-{int(time.time())}-3",
                                source_document_id=mock_source.id,
                                domain="Psychiatry",  # Out of scope for a lab
                                claim_text="Patient exhibits signs of severe depression.",
                                extracted_data={"symptom": "Depression"},
                                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                            )
                        ]
                        
                        package = ContentPackage(
                            id=f"pkg-{int(time.time())}",
                            original_file_name=uploaded_file.name,
                            upload_date=datetime.now(),
                            source=mock_source,
                            raw_extracted_text="MOCK RAW TEXT: Fasting Blood Glucose 5.4 mmol/L. Total Cholesterol 6.1 mmol/L. Patient exhibits signs of severe depression.",
                            claims=mock_claims
                        )
                        
                        package.evaluate_claims()
                        st.session_state.pending_packages.append(package)
                        st.success("Extraction complete! See pending packages to review and commit.")
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
                            
                            pkg.status = "Approved"
                            st.success("Committed structured pathology data to Vault!")
                            st.rerun()
                            
                        if col_r.button("🗑️ Reject & Discard", key=f"rej_{idx}"):
                            st.session_state.pending_packages.pop(idx)
                            st.rerun()

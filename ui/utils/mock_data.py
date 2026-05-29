from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from src.phr_models.agents import Actor, ActorType, DelegationRule, VerificationStatus
from src.phr_models.cases import CaseCategory, CaseFile, CaseStatus, CaseTask
from src.phr_models.life_events import (
    DocumentCategory,
    LifeEventCategory,
    DataQualityTag,
    MaslowLayer,
    RecoveryStatus,
    SeverityLevel,
    WellbeingDimension,
)
from src.phr_models.location import SemanticCategory
from src.phr_models.medications import AdherenceStatus
from src.phr_models.medications import DataQualityTag as MedDataQualityTag
from src.phr_models.pathology import DiagnosticReport, DiagnosticReportStatus, PathologyObservation
from src.phr_models.proxy_consent import LegalBasis, PrivacyMode, ProxyConsent, ProxyRelationship, RelatedPerson
from src.phr_models.psychiatry import ObservationContext


def init_mock_data():
    profile = st.query_params.get("profile", "gemini").lower()
    
    if "patient_profile" not in st.session_state or st.session_state.get("_mock_data_profile") != profile:
        karyotype_map = {
            "margaret": "XX",
            "elena": "XX",
            "rebecca": "XX",
            "michael": "XY",
            "robert": "XY",
            "jordan": "XY",
            "gemini": "XY",
        }
        full_name_map = {
            "gemini": "John Doe",
            "michael": "Michael Chen",
            "elena": "Elena Vasquez",
            "rebecca": "Rebecca Hart",
            "margaret": "Margaret O'Brien",
            "robert": "Robert Nguyen",
            "jordan": "Jordan Smith",
        }
        expressed_map = {
            "XX": "Female",
            "XY": "Male",
        }
        karyotype = karyotype_map.get(profile, "XY")
        st.session_state.patient_profile = {
            "full_name": full_name_map.get(profile, profile.capitalize()),
            "date_of_birth": datetime(1980, 5, 20).date(),
            "chromosomal_sex": karyotype,
            "sex_expressed_as": expressed_map.get(karyotype, "Male"),
            "sex_expressed_custom": "",
            "pronouns": "She/Her" if karyotype == "XX" else "He/Him",
            "gender_identity": expressed_map.get(karyotype, "Male"),
            "ancestry_lineage": "Anglo-Celtic / Western European",
            "primary_language": "English",
            "medicare_number": "1234 56789 1",
            "insurance_provider": "Medibank Private",
            "insurance_policy_number": "MP987654321",
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact_phone": "+61 400 123 456"
        }
        st.session_state._mock_data_profile = profile

    if "related_persons" not in st.session_state:
        st.session_state.related_persons = [
            RelatedPerson(
                id="rp-doctor-jenkins",
                patient_id="patient-self",
                relationship=ProxyRelationship.CARER,
                is_anonymous=False,
                description="Dr. Sarah Jenkins (GP, Sydney Medical Centre)"
            ),
            RelatedPerson(
                id="rp-carer-john",
                patient_id="patient-self",
                relationship=ProxyRelationship.GUARDIAN,
                is_anonymous=False,
                description="John Doe (Designated Carer / Father)"
            ),
            RelatedPerson(
                id="rp-partner-safety",
                patient_id="patient-self",
                relationship=ProxyRelationship.PARTNER,
                is_anonymous=True,
                description="Partner (Anonymous Contact for safety planning)"
            )
        ]
        
    if "proxy_consents" not in st.session_state:
        st.session_state.proxy_consents = [
            ProxyConsent(
                id="consent-gp",
                patient_id="patient-self",
                proxy_id="rp-doctor-jenkins",
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                audit_silenced=False
            ),
            ProxyConsent(
                id="consent-carer-mha",
                patient_id="patient-self",
                proxy_id="rp-carer-john",
                legal_basis=LegalBasis.MHA_NOMINATED,
                privacy_mode=PrivacyMode.MODE_C_SHARED,
                audit_silenced=False
            ),
            ProxyConsent(
                id="consent-partner-safety",
                patient_id="patient-self",
                proxy_id="rp-partner-safety",
                legal_basis=LegalBasis.SAFETY_OVERRIDE,
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                audit_silenced=True
            )
        ]
        
    if "psychiatric_observations" not in st.session_state:
        st.session_state.psychiatric_observations = [
            {
                "id": "psych-obs-1",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=5, hours=3),
                "context": ObservationContext.SELF_REPORTED,
                "recorded_by_proxy_id": None,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "symptom_code": "48694002",
                "symptom_name": "Anxiety / Panic Attack",
                "notes": "Felt sudden chest tightness and racing thoughts during project standup.",
                "linked_medication_id": None
            },
            {
                "id": "psych-obs-2",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=3, hours=1),
                "context": ObservationContext.CARER_OBSERVED,
                "recorded_by_proxy_id": "rp-carer-john",
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "symptom_code": "58596002",
                "symptom_name": "Agitation / Pacing",
                "notes": "Observed significant pacing and irritability in the evening after work.",
                "linked_medication_id": None
            },
            {
                "id": "psych-obs-3",
                "patient_id": "patient-self",
                "date_recorded": datetime.now() - timedelta(days=1, hours=4),
                "context": ObservationContext.CLINICIAN_OBSERVED,
                "recorded_by_proxy_id": "rp-doctor-jenkins",
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "symptom_code": "366979004",
                "symptom_name": "Depressed mood",
                "notes": "Patient reports flat affect and low energy. Adjusted dosage of sertraline.",
                "linked_medication_id": "med-sertraline"
            }
        ]
        
    if "location_events" not in st.session_state:
        st.session_state.location_events = [
            {
                "id": "geo-1",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=5, hours=8),
                "latitude": -33.8688,
                "longitude": 151.2093,
                "category": SemanticCategory.HOME,
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "linked_symptom_id": None
            },
            {
                "id": "geo-2",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=5, hours=3),
                "latitude": -33.8568,
                "longitude": 151.2153,
                "category": SemanticCategory.WORK,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "linked_symptom_id": "psych-obs-1"
            },
            {
                "id": "geo-3",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=3, hours=4),
                "latitude": -33.8824,
                "longitude": 151.2012,
                "category": SemanticCategory.MEDICAL_FACILITY,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "linked_symptom_id": "psych-obs-3"
            },
            {
                "id": "geo-4",
                "patient_id": "patient-self",
                "timestamp": datetime.now() - timedelta(days=1),
                "latitude": -33.8915,
                "longitude": 151.2767,
                "category": SemanticCategory.TRAVEL,
                "privacy_mode": PrivacyMode.MODE_C_SHARED,
                "linked_symptom_id": None
            }
        ]

    if "ons4_responses" not in st.session_state:
        st.session_state.ons4_responses = [
            {
                "date": datetime.now() - timedelta(days=5),
                "life_satisfaction": 6,
                "worthwhile": 7,
                "happiness": 5,
                "anxiety": 8
            },
            {
                "date": datetime.now() - timedelta(days=3),
                "life_satisfaction": 7,
                "worthwhile": 7,
                "happiness": 6,
                "anxiety": 5
            },
            {
                "date": datetime.now() - timedelta(days=1),
                "life_satisfaction": 8,
                "worthwhile": 8,
                "happiness": 7,
                "anxiety": 3
            }
        ]

    if "medication_administrations" not in st.session_state:
        st.session_state.medication_administrations = [
            {
                "id": "med-sertraline",
                "patient_id": "patient-self",
                "medication_name": "Sertraline 50mg",
                "status": AdherenceStatus.TAKEN,
                "effective_time": datetime.now() - timedelta(days=1, hours=8),
                "quality_tag": MedDataQualityTag.EXACT,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED
            },
            {
                "id": "med-sertraline-missed",
                "patient_id": "patient-self",
                "medication_name": "Sertraline 50mg",
                "status": AdherenceStatus.MISSED,
                "effective_time": datetime.now() - timedelta(days=2, hours=8),
                "quality_tag": MedDataQualityTag.SELF_REPORT,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "notes": "Forgot due to early morning meeting"
            }
        ]

    if "life_events" not in st.session_state:
        st.session_state.life_events = [
            {
                "id": "le-job-loss-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.JOB_LOSS,
                "title": "Redundancy from Employer",
                "description": "Made redundant after restructure. Position eliminated with 4 weeks notice. Unfair dismissal claim lodged with Fair Work Commission.",
                "trigger_date": datetime.now() - timedelta(days=90),
                "end_date": None,
                "severity": SeverityLevel.MODERATE,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "recorded_by_proxy_id": None,
                "involved_parties": [],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.EMPLOYMENT, "severity": SeverityLevel.HIGH, "description": "Loss of stable full-time employment"},
                    {"dimension": WellbeingDimension.INCOME_WEALTH, "severity": SeverityLevel.HIGH, "description": "Immediate 60% income reduction"},
                    {"dimension": WellbeingDimension.HEALTH_MENTAL, "severity": SeverityLevel.MODERATE, "description": "Increased anxiety and sleep disturbance"},
                    {"dimension": WellbeingDimension.SUBJECTIVE_WELLBEING, "severity": SeverityLevel.MODERATE, "description": "Reduced life satisfaction and self-worth"},
                ],
                "supporting_documents": [
                    {"id": "doc-1", "title": "Termination Letter", "category": DocumentCategory.PROFESSIONAL, "document_uri": "vault://docs/termination-letter.pdf.enc", "jurisdiction": "AU-NSW"},
                    {"id": "doc-2", "title": "Centrelink JobSeeker Claim", "category": DocumentCategory.GOVERNMENT, "document_uri": "vault://docs/centrelink-claim.pdf.enc", "jurisdiction": "AU-FED"},
                    {"id": "doc-3", "title": "Fair Work Commission Application", "category": DocumentCategory.LEGAL, "document_uri": "vault://docs/fwc-application.pdf.enc", "jurisdiction": "AU-FED"},
                ],
                "recovery_indicators": [
                    {"id": "rec-1", "description": "Register with Centrelink / JobSeeker", "status": RecoveryStatus.RESOLVED, "linked_service": "Services Australia"},
                    {"id": "rec-2", "description": "Lodge Fair Work Commission unfair dismissal claim", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "Fair Work Commission"},
                    {"id": "rec-3", "description": "Enrol in retraining program (TAFE Digital Skills)", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "TAFE NSW"},
                    {"id": "rec-4", "description": "Secure new employment or contract work", "status": RecoveryStatus.NOT_STARTED, "linked_service": None},
                ],
                "linked_psych_observation_ids": ["psych-obs-1"],
                "linked_medication_ids": [],
                "maslow_layer": MaslowLayer.SAFETY,
                "data_quality_tag": DataQualityTag.EXACT,
                "notes": "Discussing options with employment lawyer. GP has noted increased anxiety since redundancy."
            },
            {
                "id": "le-separation-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.DIVORCE_SEPARATION,
                "title": "Relationship Separation",
                "description": "Separation from long-term partner. Property settlement pending. Parenting orders being negotiated through mediation.",
                "trigger_date": datetime.now() - timedelta(days=60),
                "end_date": None,
                "severity": SeverityLevel.HIGH,
                "privacy_mode": PrivacyMode.MODE_A_STRICT,
                "recorded_by_proxy_id": None,
                "involved_parties": ["rp-partner-safety"],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.SOCIAL_CONNECTIONS, "severity": SeverityLevel.HIGH, "description": "Primary relationship breakdown; social network disruption"},
                    {"dimension": WellbeingDimension.HOUSING, "severity": SeverityLevel.MODERATE, "description": "Relocation required; temporary accommodation"},
                    {"dimension": WellbeingDimension.INCOME_WEALTH, "severity": SeverityLevel.MODERATE, "description": "Asset division and legal costs"},
                    {"dimension": WellbeingDimension.HEALTH_MENTAL, "severity": SeverityLevel.HIGH, "description": "Depressed mood and grief response"},
                    {"dimension": WellbeingDimension.RIGHTS_LEGAL, "severity": SeverityLevel.MODERATE, "description": "Parenting orders and property settlement negotiations"},
                ],
                "supporting_documents": [
                    {"id": "doc-4", "title": "Family Dispute Resolution Certificate", "category": DocumentCategory.LEGAL, "document_uri": "vault://docs/fdr-cert.pdf.enc", "jurisdiction": "AU-FED"},
                    {"id": "doc-5", "title": "Temporary Rental Agreement", "category": DocumentCategory.HOUSING, "document_uri": "vault://docs/rental-agreement.pdf.enc", "jurisdiction": "AU-NSW"},
                ],
                "recovery_indicators": [
                    {"id": "rec-5", "description": "Attend Family Dispute Resolution (mediation)", "status": RecoveryStatus.IN_PROGRESS, "linked_service": "Relationships Australia NSW"},
                    {"id": "rec-6", "description": "Secure stable housing", "status": RecoveryStatus.IN_PROGRESS, "linked_service": None},
                    {"id": "rec-7", "description": "Finalise property settlement", "status": RecoveryStatus.NOT_STARTED, "linked_service": "Legal Aid NSW"},
                    {"id": "rec-8", "description": "Establish regular counselling", "status": RecoveryStatus.STABLE, "linked_service": "Beyond Blue"},
                ],
                "linked_psych_observation_ids": ["psych-obs-3"],
                "linked_medication_ids": ["med-sertraline"],
                "maslow_layer": MaslowLayer.BELONGING,
                "data_quality_tag": DataQualityTag.SELF_REPORT,
                "notes": "Mediation progressing slowly. Counsellor reports patient is engaging well with sessions."
            },
            {
                "id": "le-housing-1",
                "patient_id": "patient-self",
                "event_category": LifeEventCategory.HOMELESSNESS,
                "title": "Housing Instability (Post-Separation)",
                "description": "Temporary accommodation after separation. Couch-surfing with family while seeking affordable rental in Sydney market.",
                "trigger_date": datetime.now() - timedelta(days=45),
                "end_date": datetime.now() - timedelta(days=15),
                "severity": SeverityLevel.CRITICAL,
                "privacy_mode": PrivacyMode.MODE_B_PRIVILEGED,
                "recorded_by_proxy_id": "rp-carer-john",
                "involved_parties": ["rp-carer-john"],
                "wellbeing_impacts": [
                    {"dimension": WellbeingDimension.HOUSING, "severity": SeverityLevel.CRITICAL, "description": "No permanent address for 30 days"},
                    {"dimension": WellbeingDimension.SAFETY, "severity": SeverityLevel.HIGH, "description": "Increased vulnerability without stable shelter"},
                    {"dimension": WellbeingDimension.HEALTH_PHYSICAL, "severity": SeverityLevel.MODERATE, "description": "Disrupted sleep and nutrition routines"},
                    {"dimension": WellbeingDimension.EMPLOYMENT, "severity": SeverityLevel.LOW, "description": "Difficulty attending interviews without stable address"},
                ],
                "supporting_documents": [
                    {"id": "doc-6", "title": "Tenancy Termination Notice", "category": DocumentCategory.HOUSING, "document_uri": "vault://docs/tenancy-termination.pdf.enc", "jurisdiction": "AU-NSW"},
                ],
                "recovery_indicators": [
                    {"id": "rec-9", "description": "Apply for emergency housing through DCJ Housing", "status": RecoveryStatus.RESOLVED, "linked_service": "DCJ Housing NSW"},
                    {"id": "rec-10", "description": "Secure private rental", "status": RecoveryStatus.RESOLVED, "linked_service": None},
                ],
                "linked_psych_observation_ids": ["psych-obs-2"],
                "linked_medication_ids": [],
                "maslow_layer": MaslowLayer.PHYSIOLOGICAL,
                "data_quality_tag": DataQualityTag.SELF_REPORT,
                "notes": "Resolved — secured rental. Father (John) provided support during this period."
            }
        ]

    if "case_files" not in st.session_state:
        st.session_state.case_files = [
            CaseFile(
                id="case-1",
                patient_id="patient-self",
                title="Suspected Sleep Apnea Evaluation",
                category=CaseCategory.SUSPECTED_CONDITION,
                status=CaseStatus.SUSPECTED,
                hypothesis_or_claim="Patient experiences excessive daytime sleepiness, chronic loud snoring, and witnessed breathing pauses during sleep.",
                date_created=datetime.now() - timedelta(days=14),
                date_updated=datetime.now() - timedelta(days=2),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                linked_datatypes=["com.samsung.shealth.sleep", "com.samsung.shealth.sleep_snoring"],
                tasks=[
                    CaseTask(id="task-1-1", title="Log sleep & snoring data for 14 nights", description="Gather evidence using Samsung Health wearable sensors", is_completed=True),
                    CaseTask(id="task-1-2", title="Schedule GP appointment for review", description="Discuss symptoms and snoring log with GP", is_completed=False),
                    CaseTask(id="task-1-3", title="Obtain a referral for an overnight Sleep Study", description="Get a referral to a specialist sleep clinic", is_completed=False),
                ],
                notes="Snoring events have been steadily rising over the last month according to wearable data."
            ),
            CaseFile(
                id="case-2",
                patient_id="patient-self",
                title="Routine Sexual Health / STD Screening",
                category=CaseCategory.ROUTINE_CHECK,
                status=CaseStatus.ACTIVE,
                hypothesis_or_claim="Annual routine sexual health screening/check-up.",
                date_created=datetime.now() - timedelta(days=3),
                date_updated=datetime.now() - timedelta(days=3),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                tasks=[
                    CaseTask(id="task-2-1", title="Book clinic appointment", description="Sydney Sexual Health Centre or local GP", is_completed=False),
                    CaseTask(id="task-2-2", title="Undergo pathology tests", description="Complete blood and urine collection", is_completed=False),
                ]
            ),
            CaseFile(
                id="case-3",
                patient_id="patient-self",
                title="Interval Blood Test Monitoring (Lipids & Vit D)",
                category=CaseCategory.INTERVAL_TEST,
                status=CaseStatus.MONITORING,
                hypothesis_or_claim="Quarterly lipid panel and Vitamin D test to monitor cholesterol levels and supplementation efficacy.",
                date_created=datetime.now() - timedelta(days=60),
                date_updated=datetime.now() - timedelta(days=1),
                privacy_mode=PrivacyMode.MODE_A_STRICT,
                tasks=[
                    CaseTask(id="task-3-1", title="Obtain pathology request form from GP", description="Ensure lipids and 25-hydroxyvitamin D are ticked", is_completed=True),
                    CaseTask(id="task-3-2", title="Attend Laverty Pathology collection centre", description="Fast for 12 hours prior to lipid panel", is_completed=False),
                ]
            )
        ]

    if "diagnostic_reports" not in st.session_state:
        st.session_state.diagnostic_reports = [
            DiagnosticReport(
                id="report-lipid-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=14),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/laverty-lipid-panel-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-chol-1",
                        test_name="Total Cholesterol",
                        value=6.1,
                        unit="mmol/L",
                        reference_range_high=5.5,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-trig-1",
                        test_name="Triglycerides",
                        value=1.8,
                        unit="mmol/L",
                        reference_range_high=2.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-hdl-1",
                        test_name="HDL Cholesterol",
                        value=1.2,
                        unit="mmol/L",
                        reference_range_low=1.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-ldl-1",
                        test_name="LDL Cholesterol",
                        value=4.1,
                        unit="mmol/L",
                        reference_range_high=3.5,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    )
                ]
            ),
            DiagnosticReport(
                id="report-biochem-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=1),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/dhm-glucose-hba1c-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_B_PRIVILEGED,
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-glucose-1",
                        test_name="Fasting Blood Glucose",
                        value=5.4,
                        unit="mmol/L",
                        reference_range_low=3.0,
                        reference_range_high=5.4,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    ),
                    PathologyObservation(
                        id="obs-hba1c-1",
                        test_name="HbA1c (Glycated Hb)",
                        value=5.6,
                        unit="%",
                        reference_range_high=6.0,
                        privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                    )
                ]
            ),
            DiagnosticReport(
                id="report-std-1",
                patient_id="patient-self",
                date_issued=datetime.now() - timedelta(days=3),
                status=DiagnosticReportStatus.FINAL,
                pdf_attachment_uri="vault://docs/sshc-screen-2026.pdf.enc",
                privacy_mode=PrivacyMode.MODE_A_STRICT, # Default Strict Privacy
                recorded_by_proxy_id=None,
                observations=[
                    PathologyObservation(
                        id="obs-hiv-1",
                        test_name="HIV Ag/Ab Screen",
                        value=0.08,
                        unit="Index",
                        reference_range_high=0.90,
                        privacy_mode=PrivacyMode.MODE_A_STRICT
                    ),
                    PathologyObservation(
                        id="obs-chlamydia-1",
                        test_name="Chlamydia Ur PCR",
                        value=0.0,
                        unit="PCR",
                        reference_range_high=0.0,
                        privacy_mode=PrivacyMode.MODE_A_STRICT
                    )
                ]
            )
        ]

    if "directory_actors" not in st.session_state:
        st.session_state.directory_actors = [
            Actor(
                id="actor-laverty-pathology",
                actor_type=ActorType.ORGANIZATION,
                name="Laverty Pathology",
                qualifications=["NATA Accredited Lab #12345", "ISO 15189 Accreditation"],
                roles=["Diagnostic Provider", "Pathology Laboratory"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:laverty.com.au:labs"
            ),
            Actor(
                id="actor-gp-sarah",
                actor_type=ActorType.PRACTITIONER,
                name="Dr. Sarah Jenkins",
                organization="Sydney Medical Centre",
                qualifications=["M.B.B.S.", "AHPRA Registration MED00012", "FRACGP"],
                roles=["Primary Care Physician", "General Practitioner"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:sydneymedical.com.au:practitioners:sjenkins"
            ),
            Actor(
                id="actor-carer-john",
                actor_type=ActorType.DELEGATE,
                name="John Doe",
                qualifications=["Nominated Guardian Authority (MHA NSW)"],
                roles=["Designated Carer", "Guardian"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:key:z6MkpTHR8VNsBxazR24z168m"
            ),
            Actor(
                id="actor-audit-ai",
                actor_type=ActorType.SYNTHETIC_AGENT,
                name="Clinical Compliance Auditor v1",
                qualifications=["AI Audit Model: Claude-3.5-Sonnet-v2", "ISO 27001 Compliant Agent Profile"],
                roles=["Clinical Claims Auditor", "Automated Validation Engine"],
                verification_status=VerificationStatus.VERIFIED,
                did_uri="did:web:episteme.health:agents:audit-ai"
            )
        ]

    if "delegation_rules" not in st.session_state:
        st.session_state.delegation_rules = [
            DelegationRule(
                id="rule-laverty-1",
                patient_id="patient-self",
                actor_id="actor-laverty-pathology",
                granted_roles=["log_pathology", "publish_observations"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                allowed_record_types=["PathologyObservation", "DiagnosticReport"],
                is_active=True
            ),
            DelegationRule(
                id="rule-gp-1",
                patient_id="patient-self",
                actor_id="actor-gp-sarah",
                granted_roles=["read_clinical_records", "verify_claims", "write_referrals"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                linked_case_ids=["case-1", "case-3"], # Referral evaluation cases
                is_active=True
            ),
            DelegationRule(
                id="rule-carer-1",
                patient_id="patient-self",
                actor_id="actor-carer-john",
                granted_roles=["view_wellbeing", "view_timeline", "receive_alerts"],
                legal_basis=LegalBasis.MHA_NOMINATED,
                privacy_mode_limit=PrivacyMode.MODE_C_SHARED,
                restricted_records=["PsychiatricObservation", "MedicationAdministration"], # restricted for patient safety/privacy
                is_active=True
            ),
            DelegationRule(
                id="rule-audit-1",
                patient_id="patient-self",
                actor_id="actor-audit-ai",
                granted_roles=["read_diagnostics", "audit_clinical_claims"],
                legal_basis=LegalBasis.EXPLICIT_CONSENT,
                privacy_mode_limit=PrivacyMode.MODE_B_PRIVILEGED,
                restricted_records=["PsychiatricObservation"], # Explicitly block AI agent from psychiatric logs
                is_active=True
            )
        ]

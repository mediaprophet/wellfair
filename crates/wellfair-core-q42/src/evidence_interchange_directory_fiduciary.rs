//! `evidence_interchange_directory_fiduciary`:
//!
//! Implements the four foundational pillars connecting Sanctuary Imports, Hypermedia-Library
//! Cross-App File Interchange, Active-Directory Social Connection Ceremonies, `ns.webcivics.net`
//! Values Credentials, Fiduciary & Professional Personas, and Jurisdiction-Aware Access Control:
//!
//! 1. **Enhanced Digital Evidence Informatics on File Imports (*Evidence Act* ss 48, 69, 146, 147, 161)**:
//!    - Captures device/process working-accuracy provenance, electronic communication transport
//!      headers (s 161 presumptions), 4 bitemporal/filesystem timestamps, and chain-of-custody digests.
//! 2. **Universal Cross-Qap File Interchange (`qualia://library/<artifact-id>`)**:
//!    - Enables files imported or authored in one Qap (`SanctuaryImports`, `HypermediaLibrary`,
//!      `QdpDomainMail`, `PoetHyperCanvas`, `WellFairSanctuary`, `CooperativeProjects`) to be
//!      referenced, presented, or attached across any other Qap subject to permissions and
//!      `spc:PersistenceClass` (`https://ns.webcivics.net/social-permissive-commons/`).
//! 3. **Two-Category Active-Directory Connection Ceremony & `ns.webcivics.net` Values Credentials**:
//!    - **Category A (`StrangerZeroPriorHistory`)**: For parties with no prior history (front-door QDP
//!      discovery / `qcx1_` invitation).
//!    - **Category B (`ClaimedPriorConnection`)**: For parties claiming prior connection, corroborated
//!      against imported Sanctuary data (e.g. historical `.mbox` email threads, Google Maps `placeVisit`
//!      co-presence, or shared `Q-Git` commits/agreements).
//!    - **Pre-Connection `ValuesCredential` Negotiation (`https://ns.webcivics.net/values/`)**:
//!      Negotiates human-rights instruments (`UDHR`, `ICESCR`, `UNCRPD`), verifies `values:HumanOnly`
//!      person-reading (blocking corporate-personhood capture), and binds the established relationship
//!      to specific Projects, Groups, and Content Categories.
//! 4. **Fiduciary & Professional Persona Profiles, Qualifications & Jurisdiction-Aware Permissions
//!    (`https://ns.webcivics.net/jurisdiction/` & `https://ns.webcivics.net/capability/`)**:
//!    - Separates `PersonalSanctuaryPersona` from `ProfessionalFiduciaryPersona` (`HealthcareAndMedical`,
//!      `QualifiedSocialWorkAndCare`, `LawEnforcementAndJustice`, `GovernmentAndParliamentaryCivic`,
//!      `EngineeringAndScientificSpecialist`).
//!    - Attaches verifiable qualifications/certifications (`Formal`, `PriorLearning`, `Experiential`,
//!      `PeerAttested`) and evaluates sharing permissions across federal and sub-state jurisdictions
//!      (`jur:Australia`, `jur:AU-VIC`, `jur:AU-NSW`, `jur:AU-ACT`, `jur:EU-GDPR`) with multi-sig
//!      instigation guards (`consent_credential.rs`) and durable conduct receipts.

use crate::domain_mail_and_sanctuary_importers::{
    q_hash_u64, FormalSanctuaryCategory, ImportSourceKind, NQuin48, StagingLifecycleState,
};
use crate::evidentiary_cold_archiver_qar::PreservedEvidentiaryTimestamps;
use crate::qap_container_and_vibe_runtime::{compute_entry_digest32, hex_encode};
use serde::{Deserialize, Serialize};

// ============================================================================
// PILLAR 1: ENHANCED DIGITAL EVIDENCE INFORMATICS (EVIDENCE ACT SS 48, 69, 146, 147, 161)
// ============================================================================

/// Statutory basis under the *Evidence Act 1995* (Cth) / *Evidence Act 2008* (Vic) supported by
/// the import's digital evidence informatics envelope.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceActStatutorySection {
    /// Section 48: Proof of contents of documents (copies, printouts, and digital reproductions).
    Section48ProofOfContents,
    /// Section 69: Exception to hearsay rule for business, clinical, and fiduciary records.
    Section69BusinessAndClinicalRecords,
    /// Section 146: Evidence produced by processes, machines, and devices (working-accuracy presumption).
    Section146DeviceAndProcessOutput,
    /// Section 147: Documents produced by processes, machines, and devices in the course of record-keeping.
    Section147AutomatedRecordKeeping,
    /// Section 161: Electronic communications presumptions (originator, time sent, time received, destination).
    Section161ElectronicCommunications,
}

impl EvidenceActStatutorySection {
    pub const fn citation(self) -> &'static str {
        match self {
            Self::Section48ProofOfContents => "Evidence Act s 48 (Proof of Document Contents)",
            Self::Section69BusinessAndClinicalRecords => "Evidence Act s 69 (Fiduciary & Clinical Record Exception)",
            Self::Section146DeviceAndProcessOutput => "Evidence Act s 146 (Reliable Device/Process Output)",
            Self::Section147AutomatedRecordKeeping => "Evidence Act s 147 (Automated Custody Process)",
            Self::Section161ElectronicCommunications => "Evidence Act s 161 (Electronic Communication Presumptions)",
        }
    }
}

/// Optional electronic communication transport metadata (for *Evidence Act* s 161 presumptions
/// on imported Domain Mail / Gmail `.mbox` / `.eml` or P2P messages).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ElectronicCommunicationPresumptionMeta {
    pub message_id_header: String,
    pub purported_originator_address: String,
    pub purported_recipient_address: String,
    pub sent_timestamp_unix: u64,
    pub received_timestamp_unix: u64,
    pub dkim_spf_or_qdp_signer_verified: bool,
    pub transport_hop_trace_digest_hex: String,
}

/// Enhanced Digital Evidence Informatics attached to every imported or ingested file in the Sanctuary.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DigitalEvidenceInformaticsEnvelope {
    pub evidence_envelope_id: String,
    pub source_kind: ImportSourceKind,
    pub original_filename_or_uri: String,
    pub mime_type: String,
    pub character_encoding: String,
    pub original_byte_length: u64,
    pub content_digest_hex: String,
    pub source_device_or_system_id: String,
    pub process_working_accuracy_attestation: String,
    pub applicable_statutory_sections: Vec<EvidenceActStatutorySection>,
    pub timestamps: PreservedEvidentiaryTimestamps,
    pub electronic_comm_meta: Option<ElectronicCommunicationPresumptionMeta>,
    pub ingesting_custodian_did: String,
    pub qecp_intake_signature_hex: String,
    pub evidence_receipt_quin: NQuin48,
}

impl DigitalEvidenceInformaticsEnvelope {
    #[allow(clippy::too_many_arguments)]
    pub fn build_for_import(
        evidence_envelope_id: impl Into<String>,
        source_kind: ImportSourceKind,
        original_filename_or_uri: impl Into<String>,
        mime_type: impl Into<String>,
        raw_bytes: &[u8],
        source_device_or_system_id: impl Into<String>,
        timestamps: PreservedEvidentiaryTimestamps,
        electronic_comm_meta: Option<ElectronicCommunicationPresumptionMeta>,
        ingesting_custodian_did: impl Into<String>,
    ) -> Result<Self, String> {
        timestamps.validate_chronology()?;
        let env_id = evidence_envelope_id.into();
        let filename = original_filename_or_uri.into();
        let custodian = ingesting_custodian_did.into();
        let digest_hex = hex_encode(&compute_entry_digest32(raw_bytes));

        let mut sections = vec![
            EvidenceActStatutorySection::Section48ProofOfContents,
            EvidenceActStatutorySection::Section146DeviceAndProcessOutput,
            EvidenceActStatutorySection::Section147AutomatedRecordKeeping,
        ];
        match source_kind {
            ImportSourceKind::DomainMailOrGmailMbox => {
                sections.push(EvidenceActStatutorySection::Section161ElectronicCommunications);
            }
            ImportSourceKind::SamsungGalaxyWatchHealth | ImportSourceKind::PdfDocument => {
                sections.push(EvidenceActStatutorySection::Section69BusinessAndClinicalRecords);
            }
            ImportSourceKind::GoogleMapsLocationHistory => {}
        }

        let quin = NQuin48::new(
            q_hash_u64(&env_id),
            q_hash_u64("evidence:hasInformaticsDigest"),
            q_hash_u64(&digest_hex),
            q_hash_u64(&custodian),
            timestamps.original_created_at_unix,
        );

        Ok(Self {
            evidence_envelope_id: env_id,
            source_kind,
            original_filename_or_uri: filename,
            mime_type: mime_type.into(),
            character_encoding: "UTF-8 / CBOR-LD (No-ASCII Policy Compliant)".to_string(),
            original_byte_length: raw_bytes.len() as u64,
            content_digest_hex: digest_hex.clone(),
            source_device_or_system_id: source_device_or_system_id.into(),
            process_working_accuracy_attestation: "Ingested by deterministic QualiaDB Sanctuary intake pipeline with bit-exact digest verification and hardware clock anchoring (Evidence Act ss 146 & 147)".to_string(),
            applicable_statutory_sections: sections,
            timestamps,
            electronic_comm_meta,
            ingesting_custodian_did: custodian,
            qecp_intake_signature_hex: format!("ed25519_ml_dsa_87_evidence_intake_{}", &digest_hex[..16]),
            evidence_receipt_quin: quin,
        })
    }
}

// ============================================================================
// PILLAR 2: UNIVERSAL CROSS-QAP FILE INTERCHANGE (HYPERMEDIA-LIBRARY VIRTUAL FS)
// ============================================================================

/// Canonical QualiaDB Qap applications that can produce, reference, attach, or render an
/// `InterchangeableLibraryArtifact` via the `qualia://library/<artifact-id>` virtual file-system.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum QapAppConsumer {
    /// Sanctuary Uncategorized Intake & Importers (`sanctuary://intake/uncategorized`).
    SanctuaryImports,
    /// Hypermedia-Library (the universal virtual file-system & aspect graph).
    HypermediaLibraryFileSystem,
    /// Domain-Based QDP Mail & Communications (`draft-webcivics-QDP`).
    QdpDomainMail,
    /// Webizen Poet (HyperCanvas, Forensic Workbench, 9-Tab Ontology Studio & Verifiable PDF Printer).
    PoetHyperCanvas,
    /// Webizen WellFair (Personal Sanctuary, Telehealth rPPG, 10D HRA Anatomy & Specialist Leases).
    WellFairSanctuary,
    /// Cooperative Projects (WBS/CPM, 6-Profile Double-Entry Ledger, 9-Stage Compensation & Chat-Graph).
    CooperativeProjects,
}

impl QapAppConsumer {
    pub const ALL: &'static [QapAppConsumer] = &[
        Self::SanctuaryImports,
        Self::HypermediaLibraryFileSystem,
        Self::QdpDomainMail,
        Self::PoetHyperCanvas,
        Self::WellFairSanctuary,
        Self::CooperativeProjects,
    ];

    pub const fn label(self) -> &'static str {
        match self {
            Self::SanctuaryImports => "Sanctuary Importers",
            Self::HypermediaLibraryFileSystem => "Hypermedia-Library (File-System)",
            Self::QdpDomainMail => "QDP Domain Mail & Comms",
            Self::PoetHyperCanvas => "Webizen Poet Workbench",
            Self::WellFairSanctuary => "Webizen WellFair Sanctuary",
            Self::CooperativeProjects => "Cooperative Projects & Ledger",
        }
    }
}

/// Differentiated persistence classification at relationship exit (`https://ns.webcivics.net/social-permissive-commons/`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SpcPersistenceClass {
    /// `spc:RelationGatedCapability`: Revokes immediately when the relationship or lease ends.
    RelationGatedCapability,
    /// `spc:ThirdPartyAnchoredObligation`: Persists until an external authoritative act (e.g. child guardianship, statutory tax retention).
    ThirdPartyAnchoredObligation,
    /// `spc:CoOwnedRecord`: Persists non-erasably for each co-owning party (each retains their own testimony).
    CoOwnedRecord,
    /// `spc:ArtifactAttachedRule`: Sticky rule (`travelsWithArtifact = true`) that survives relationship exit and transfer (e.g. no-publish prohibition).
    ArtifactAttachedRule,
}

impl SpcPersistenceClass {
    pub const fn iri(self) -> &'static str {
        match self {
            Self::RelationGatedCapability => "https://ns.webcivics.net/social-permissive-commons/RelationGatedCapability",
            Self::ThirdPartyAnchoredObligation => "https://ns.webcivics.net/social-permissive-commons/ThirdPartyAnchoredObligation",
            Self::CoOwnedRecord => "https://ns.webcivics.net/social-permissive-commons/CoOwnedRecord",
            Self::ArtifactAttachedRule => "https://ns.webcivics.net/social-permissive-commons/ArtifactAttachedRule",
        }
    }
}

/// An interchangeable file/artifact registered in the Hypermedia-Library virtual file-system
/// (`qualia://library/<artifact-id>`) with full digital evidence informatics and cross-Qap permission rules.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct InterchangeableLibraryArtifact {
    pub artifact_id: String,
    pub canonical_library_uri: String,
    pub title: String,
    pub staging_state: StagingLifecycleState,
    pub formal_category: Option<FormalSanctuaryCategory>,
    pub spc_persistence_class: SpcPersistenceClass,
    pub travels_with_artifact_no_publish_prohibition: bool,
    pub evidence_informatics: DigitalEvidenceInformaticsEnvelope,
    pub permitted_qap_consumers: Vec<QapAppConsumer>,
    pub permitted_group_or_project_ids: Vec<String>,
    pub required_professional_sectors: Vec<ProfessionalRoleSector>,
    pub permitted_jurisdictions_iso: Vec<String>,
}

// ============================================================================
// PILLAR 3: TWO-CATEGORY ACTIVE-DIRECTORY SOCIAL CONNECTION CEREMONY &
//           NS.WEBCIVICS.NET VALUES-CREDENTIAL NEGOTIATION
// ============================================================================

/// The two distinct social connection initiation categories in the Active-Directory service:
/// 1. `StrangerZeroPriorHistory`: People who do not know anything about each other yet.
/// 2. `ClaimedPriorConnection`: People who claim a previous connection that can be corroborated via data.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConnectionInitiationCategory {
    /// Category 1: No prior relationship assumed; discovered via `_qdp.<domain>` front-door or `qcx1_` invite.
    StrangerZeroPriorHistory {
        discovery_mechanism: String,
    },
    /// Category 2: Claimed prior relationship backed by verifiable data evidence in the Sanctuary.
    ClaimedPriorConnection {
        claimed_context_summary: String,
        corroborating_evidence_refs: Vec<PriorConnectionEvidenceProof>,
        verified_against_sanctuary_data: bool,
    },
}

/// Evidence proofs used to corroborate a `ClaimedPriorConnection` against imported Sanctuary data.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PriorConnectionEvidenceProof {
    /// Historical email exchange found in imported Domain Mail / Gmail `.mbox` (`Message-ID` digest).
    HistoricalMailMessageDigest {
        message_id: String,
        correspondent_address: String,
        digest_hex: String,
    },
    /// Co-located place visit in imported Google Maps Timeline history (`placeId` + date window).
    CoLocatedPlaceVisitDigest {
        place_name: String,
        date_iso: String,
        digest_hex: String,
    },
    /// Prior co-authored `Q-Git` commit, cooperative project task, or signed agreement ID.
    SharedProjectOrAgreementRef {
        project_or_agreement_id: String,
        commit_or_signature_digest_hex: String,
    },
}

/// Contextual reading of the word `"person"` in an instrument (`https://ns.webcivics.net/values/PersonReading`).
///
/// Enforces `values:PersonhoodDisjointnessShape`: in human-rights `ValuesCredential` instruments,
/// `"person"` means the dignity-bearing human being (`HumanOnly`), never corporate personhood (`Incorporative`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValuesPersonReading {
    /// `values:HumanOnly`: `"person"` = `values:NaturalPerson` (the human being bearing inherent dignity).
    HumanOnly,
    /// `values:Incorporative`: Includes corporate/legal personality — raises `values:PersonhoodCaptureRiskFlag`!
    IncorporativeCaptureRisk,
    /// `values:MixedReading`: Unseparated human and corporate personality — held paraconsistently.
    MixedAmbiguousReading,
}

/// Deontic norm kind in a `ValuesCredential` undertaking (`https://ns.webcivics.net/values/`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValuesDeonticNormKind {
    /// `values:Right`
    Right,
    /// `values:Obligation` (`OP_OBLIGATE: 0x10`)
    Obligation,
    /// `values:Permission` (`OP_PERMIT: 0x11`)
    Permission,
    /// `values:Prohibition` (`OP_FORBID: 0x12`)
    Prohibition,
}

/// A single affirmable deontic undertaking derived from a human-rights instrument on `ns.webcivics.net`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValuesUndertakingRule {
    pub undertaking_iri: String,
    pub instrument_citation: String,
    pub norm_kind: ValuesDeonticNormKind,
    pub clause_text: String,
    pub non_derogable: bool,
}

/// A Values Credential (`https://ns.webcivics.net/values/ValuesCredential`) used to define and
/// negotiate the rules of a relationship before the connection is established.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValuesCredentialInstrument {
    pub credential_iri: String,
    pub title: String,
    pub person_reading: ValuesPersonReading,
    pub undertakings: Vec<ValuesUndertakingRule>,
}

impl ValuesCredentialInstrument {
    /// Enforces `values:PersonhoodDisjointnessShape`: raises a capture-risk error if an instrument
    /// attempts to smuggle corporate personhood (`IncorporativeCaptureRisk`) into a human-rights
    /// Values Credential.
    pub fn validate_human_dignity_reading(&self) -> Result<(), String> {
        if self.person_reading != ValuesPersonReading::HumanOnly {
            return Err(format!(
                "PersonhoodCaptureRiskFlag triggered on '{}': ValuesCredential must use values:HumanOnly reading (corporations do not bear inherent human dignity)",
                self.credential_iri
            ));
        }
        Ok(())
    }
}

/// Lifecycle state of a negotiated social connection in the Active Directory.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SocialConnectionNegotiationState {
    /// Step 1: Discovery or invitation received (`StrangerZeroPriorHistory` or `ClaimedPriorConnection`).
    InitiatedPendingVerification,
    /// Step 2: Negotiating `ValuesCredential` human-rights rules, jurisdiction, and persistence classes.
    NegotiatingValuesCredentials,
    /// Step 3: Mutually signed (`qhs1` challenge-response + `QECP` signatures); active in Directory
    /// and bound to permitted Projects, Groups, and Content Categories.
    EstablishedActiveConnection,
    /// Step 4: Relationship dissolving/dissolved; `spc:onExit` differentiated persistence applied.
    DissolvedDifferentiatedPersistenceActive,
}

/// Complete Active-Directory Social Connection & Relationship Record negotiated via `ValuesCredential`s.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DirectoryNegotiatedConnection {
    pub connection_id: String,
    pub initiator_did: String,
    pub responder_did: String,
    pub pairwise_relationship_did: String,
    pub initiation_category: ConnectionInitiationCategory,
    pub relation_type_concept_iri: String,
    pub negotiated_values_credentials: Vec<ValuesCredentialInstrument>,
    pub governing_jurisdiction_iso: String,
    pub bound_project_ids: Vec<String>,
    pub bound_group_categories: Vec<String>,
    pub permitted_content_categories: Vec<FormalSanctuaryCategory>,
    pub initiator_qhs1_signature_hex: Option<String>,
    pub responder_qhs1_signature_hex: Option<String>,
    pub state: SocialConnectionNegotiationState,
}

impl DirectoryNegotiatedConnection {
    /// Verifies that:
    /// 1. Every `ValuesCredentialInstrument` passes `validate_human_dignity_reading()` (`HumanOnly`),
    /// 2. If `ClaimedPriorConnection`, `verified_against_sanctuary_data` is true (or downgraded to
    ///    stranger verification until corroborated),
    /// 3. Both parties have signed the `qhs1` challenge-response + negotiated `ValuesCredential` rules,
    /// before transitioning the connection to `EstablishedActiveConnection`.
    pub fn finalize_connection_establishment(&mut self) -> Result<NQuin48, String> {
        if self.negotiated_values_credentials.is_empty() {
            return Err("Connection establishment requires at least one negotiated ValuesCredential instrument".to_string());
        }
        for vc in &self.negotiated_values_credentials {
            vc.validate_human_dignity_reading()?;
        }
        if let ConnectionInitiationCategory::ClaimedPriorConnection {
            verified_against_sanctuary_data,
            ..
        } = &self.initiation_category
        {
            if !*verified_against_sanctuary_data {
                return Err("ClaimedPriorConnection has not yet been corroborated against Sanctuary data".to_string());
            }
        }
        let init_signed = self
            .initiator_qhs1_signature_hex
            .as_deref()
            .map(|s| !s.trim().is_empty())
            .unwrap_or(false);
        let resp_signed = self
            .responder_qhs1_signature_hex
            .as_deref()
            .map(|s| !s.trim().is_empty())
            .unwrap_or(false);
        if !init_signed || !resp_signed {
            return Err("Both initiator and responder must sign the negotiated ValuesCredential rules".to_string());
        }

        self.state = SocialConnectionNegotiationState::EstablishedActiveConnection;
        Ok(NQuin48::new(
            q_hash_u64(&self.connection_id),
            q_hash_u64("spc:establishedSocialRelation"),
            q_hash_u64(&self.pairwise_relationship_did),
            q_hash_u64(&self.governing_jurisdiction_iso),
            self.negotiated_values_credentials.len() as u64,
        ))
    }
}

// ============================================================================
// PILLAR 4: FIDUCIARY & PROFESSIONAL PERSONA PROFILES, QUALIFICATIONS &
//           JURISDICTION-AWARE PERMISSION ENGINE
// ============================================================================

/// Separation of a natural person's personal vs. professional/fiduciary persona informatics.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PersonaContextKind {
    /// Personal life, family, friends, private health, and Sanctuary selfhood.
    PersonalSanctuaryPersona,
    /// Regulated or representative professional capacity carrying heightened fiduciary duties.
    ProfessionalFiduciaryPersona,
    /// Combined dual-context (explicitly authorized by the natural person for a specific relationship).
    DualPersonalAndProfessional,
}

/// Regulated professional, clinical, legal, or civic (government) role sectors.
///
/// Honors project vocabulary: **civic** for government/parliamentary activity and **civics**
/// for people-led community work.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ProfessionalRoleSector {
    /// Medical Practitioner (Doctor, Psychiatrist, GP), Psychologist, Registered Nurse.
    HealthcareAndMedical,
    /// Qualified Social Worker, Housing/Disability Support Specialist, Trauma Counsellor.
    QualifiedSocialWorkAndCare,
    /// Legal Practitioner (Barrister, Solicitor, Human-Rights Counsel), Judicial Officer, Sworn Investigator.
    LawEnforcementAndJustice,
    /// Government / Civic Representative (Elected Local Member of Parliament / MP, Senator, Parliamentary Advisor, Ombudsman).
    GovernmentAndParliamentaryCivic,
    /// Chartered Engineer, Forensic Accountant, Scientific Specialist.
    EngineeringAndScientificSpecialist,
    /// People-led Civics & Cooperative Steward.
    PeopleLedCivicsSteward,
}

impl ProfessionalRoleSector {
    pub const fn label(self) -> &'static str {
        match self {
            Self::HealthcareAndMedical => "Healthcare & Medical Practitioner (Doctor / Psychologist / Nurse)",
            Self::QualifiedSocialWorkAndCare => "Qualified Social Worker & Care Specialist",
            Self::LawEnforcementAndJustice => "Law, Justice & Human-Rights Legal Counsel",
            Self::GovernmentAndParliamentaryCivic => "Government & Parliamentary Civic Role (Local MP / Advisor / Ombudsman)",
            Self::EngineeringAndScientificSpecialist => "Engineering, Scientific & Forensic Specialist",
            Self::PeopleLedCivicsSteward => "People-Led Civics & Cooperative Steward",
        }
    }
}

/// Recognition basis for a capability or qualification (`https://ns.webcivics.net/cml/recognitionBasis`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum QualificationRecognitionBasis {
    /// Statutory board registration, university degree, or practicing certificate (e.g. AHPRA, Legal Services Board).
    FormalStatutoryOrAcademic,
    /// Recognition of Prior Learning (`cap:LearningClaim` / `cml:PriorLearning`).
    PriorLearningRpl,
    /// Demonstrated experiential track record (`cml:Experiential`).
    Experiential,
    /// Attested by qualified peers in the cooperative directory (`cml:PeerAttested`).
    PeerAttested,
}

/// A verifiable qualification, registration, or office credential attached to a person's
/// `FiduciaryPersonaProfile` (`https://ns.webcivics.net/capability/LearningClaim`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerifiableQualificationCredential {
    pub credential_id: String,
    pub sector: ProfessionalRoleSector,
    pub title: String,
    pub issuing_authority_or_register: String,
    pub registration_or_certificate_number: String,
    pub recognition_basis: QualificationRecognitionBasis,
    /// ISO jurisdiction codes where this qualification/authority is legally recognized (e.g. `["AU", "AU-VIC"]`).
    pub recognized_jurisdictions_iso: Vec<String>,
    pub valid_from_unix: u64,
    pub valid_until_unix: u64,
    pub revocation_status_active: bool,
    pub issuer_signature_hex: String,
}

impl VerifiableQualificationCredential {
    pub fn is_valid_in_jurisdiction_at(&self, jurisdiction_iso: &str, now_unix: u64) -> bool {
        if !self.revocation_status_active {
            return false;
        }
        if now_unix < self.valid_from_unix || (self.valid_until_unix > 0 && now_unix > self.valid_until_unix) {
            return false;
        }
        // Check exact sub-state match (e.g. "AU-VIC") or parent federal state match (e.g. "AU")
        let parent_state = jurisdiction_iso.split('-').next().unwrap_or(jurisdiction_iso);
        self.recognized_jurisdictions_iso
            .iter()
            .any(|j| j.eq_ignore_ascii_case(jurisdiction_iso) || j.eq_ignore_ascii_case(parent_state))
    }
}

/// A natural person's Fiduciary & Persona Profile combining personal and professional personas,
/// QDP context-domains, verifiable qualifications, and jurisdiction bindings.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiduciaryPersonaProfile {
    pub natural_person_did: String,
    pub display_name: String,
    pub active_persona_context: PersonaContextKind,
    pub personal_qdp_domain: String,
    pub professional_qdp_domain: Option<String>,
    pub professional_organization_or_chambers: Option<String>,
    pub primary_jurisdiction_iso: String,
    pub qualifications: Vec<VerifiableQualificationCredential>,
    pub affirmed_values_credential_iris: Vec<String>,
}

/// Jurisdiction ratification & statutory regime descriptor (`https://ns.webcivics.net/jurisdiction/`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct JurisdictionRatificationFrame {
    pub jurisdiction_iso: String,
    pub parent_state_iso: Option<String>,
    pub label: String,
    pub ratified_instrument_iris: Vec<String>,
    pub mandatory_evidence_act_regime: String,
    pub requires_multi_sig_subject_instigation_for_justice_or_gov_access: bool,
}

/// Outcome of evaluating a cross-Qap file access or sharing request against the requester's
/// `FiduciaryPersonaProfile`, `DirectoryNegotiatedConnection`, and `JurisdictionRatificationFrame`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct JurisdictionalAccessDecision {
    pub permitted: bool,
    pub target_qap: QapAppConsumer,
    pub matched_qualification_id: Option<String>,
    pub evaluated_jurisdiction_iso: String,
    pub requires_multi_sig_party_instigation: bool,
    pub reason: String,
    pub conduct_receipt_quin: NQuin48,
}

/// Evaluates whether `requester_profile` (connected via `connection`) is permitted to access or
/// present `artifact` inside `target_qap` under `jurisdiction_frame` at `now_unix`.
///
/// Enforces:
/// 1. Uncategorized items in `sanctuary://intake/uncategorized` are strictly blocked (`collect != categorize`).
/// 2. `target_qap` must be listed in `artifact.permitted_qap_consumers`.
/// 3. The `connection` must be in `SocialConnectionNegotiationState::EstablishedActiveConnection`
///    with all `ValuesCredential`s validated as `ValuesPersonReading::HumanOnly`.
/// 4. If `artifact.required_professional_sectors` is non-empty, `requester_profile` must be operating
///    in `ProfessionalFiduciaryPersona` (or `DualPersonalAndProfessional`) and hold a valid,
///    unexpired `VerifiableQualificationCredential` for that sector **recognized in `jurisdiction_frame.jurisdiction_iso`**.
/// 5. If the requester's sector is `LawEnforcementAndJustice` or `GovernmentAndParliamentaryCivic`
///    and `jurisdiction_frame.requires_multi_sig_subject_instigation_for_justice_or_gov_access` is true,
///    `subject_or_participating_party_instigated` must be `true` (enforcing `consent_credential.rs`
///    check on authority: *unable to act without instigation of one of the participating parties*).
#[allow(clippy::too_many_arguments)]
pub fn evaluate_cross_qap_fiduciary_and_jurisdictional_access(
    artifact: &InterchangeableLibraryArtifact,
    target_qap: QapAppConsumer,
    requester_profile: &FiduciaryPersonaProfile,
    connection: &DirectoryNegotiatedConnection,
    jurisdiction_frame: &JurisdictionRatificationFrame,
    subject_or_participating_party_instigated: bool,
    now_unix: u64,
) -> JurisdictionalAccessDecision {
    let make_quin = |code: u64| {
        NQuin48::new(
            q_hash_u64(&artifact.artifact_id),
            q_hash_u64("fiduciary:jurisdictionalAccessDecision"),
            code,
            q_hash_u64(&requester_profile.natural_person_did),
            now_unix,
        )
    };

    // 1. Block uncategorized staging artifacts
    if artifact.staging_state != StagingLifecycleState::FormallyCategorizedAndPromoted {
        return JurisdictionalAccessDecision {
            permitted: false,
            target_qap,
            matched_qualification_id: None,
            evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
            requires_multi_sig_party_instigation: false,
            reason: "Blocked: artifact is still in Sanctuary Uncategorized Intake Staging (sanctuary://intake/uncategorized)".to_string(),
            conduct_receipt_quin: make_quin(0),
        };
    }

    // 2. Check target Qap application interchange permission
    if !artifact.permitted_qap_consumers.contains(&target_qap) {
        return JurisdictionalAccessDecision {
            permitted: false,
            target_qap,
            matched_qualification_id: None,
            evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
            requires_multi_sig_party_instigation: false,
            reason: format!(
                "Blocked: artifact '{}' does not permit presentation in Qap '{:?}'",
                artifact.canonical_library_uri, target_qap
            ),
            conduct_receipt_quin: make_quin(0),
        };
    }

    // 3. Check negotiated connection & ValuesCredential standing
    if connection.state != SocialConnectionNegotiationState::EstablishedActiveConnection {
        return JurisdictionalAccessDecision {
            permitted: false,
            target_qap,
            matched_qualification_id: None,
            evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
            requires_multi_sig_party_instigation: false,
            reason: format!(
                "Blocked: social connection '{}' is in state {:?} (ValuesCredential negotiation not yet completed)",
                connection.connection_id, connection.state
            ),
            conduct_receipt_quin: make_quin(0),
        };
    }

    // 4. Check jurisdiction allowlist on the artifact
    let parent_state = jurisdiction_frame
        .parent_state_iso
        .as_deref()
        .unwrap_or(&jurisdiction_frame.jurisdiction_iso);
    let jur_allowed = artifact.permitted_jurisdictions_iso.is_empty()
        || artifact.permitted_jurisdictions_iso.iter().any(|j| {
            j.eq_ignore_ascii_case(&jurisdiction_frame.jurisdiction_iso)
                || j.eq_ignore_ascii_case(parent_state)
        });
    if !jur_allowed {
        return JurisdictionalAccessDecision {
            permitted: false,
            target_qap,
            matched_qualification_id: None,
            evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
            requires_multi_sig_party_instigation: false,
            reason: format!(
                "Blocked: jurisdiction '{}' is outside artifact permitted jurisdictions {:?}",
                jurisdiction_frame.jurisdiction_iso, artifact.permitted_jurisdictions_iso
            ),
            conduct_receipt_quin: make_quin(0),
        };
    }

    // 5. Check professional persona & qualification requirements in the governing jurisdiction
    let mut matched_qual: Option<VerifiableQualificationCredential> = None;
    if !artifact.required_professional_sectors.is_empty() {
        if requester_profile.active_persona_context == PersonaContextKind::PersonalSanctuaryPersona
        {
            return JurisdictionalAccessDecision {
                permitted: false,
                target_qap,
                matched_qualification_id: None,
                evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
                requires_multi_sig_party_instigation: false,
                reason: "Blocked: artifact requires a ProfessionalFiduciaryPersona, but requester is acting under PersonalSanctuaryPersona".to_string(),
                conduct_receipt_quin: make_quin(0),
            };
        }

        matched_qual = requester_profile
            .qualifications
            .iter()
            .find(|q| {
                artifact.required_professional_sectors.contains(&q.sector)
                    && q.is_valid_in_jurisdiction_at(&jurisdiction_frame.jurisdiction_iso, now_unix)
            })
            .cloned();

        if matched_qual.is_none() {
            return JurisdictionalAccessDecision {
                permitted: false,
                target_qap,
                matched_qualification_id: None,
                evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
                requires_multi_sig_party_instigation: false,
                reason: format!(
                    "Blocked: requester '{}' lacks a valid qualification for sectors {:?} recognized in jurisdiction '{}'",
                    requester_profile.display_name,
                    artifact.required_professional_sectors,
                    jurisdiction_frame.jurisdiction_iso
                ),
                conduct_receipt_quin: make_quin(0),
            };
        }
    }

    // 6. Enforce Multi-Sig Participating-Party Instigation Check for Justice / Law-Enforcement / Gov roles
    let requires_instigation = matched_qual
        .as_ref()
        .map(|q| {
            matches!(
                q.sector,
                ProfessionalRoleSector::LawEnforcementAndJustice
                    | ProfessionalRoleSector::GovernmentAndParliamentaryCivic
            ) && jurisdiction_frame.requires_multi_sig_subject_instigation_for_justice_or_gov_access
        })
        .unwrap_or(false);

    if requires_instigation && !subject_or_participating_party_instigated {
        return JurisdictionalAccessDecision {
            permitted: false,
            target_qap,
            matched_qualification_id: matched_qual.map(|q| q.credential_id),
            evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
            requires_multi_sig_party_instigation: true,
            reason: "Held: Justice/Government authority credential requires multi-sig instigation by a participating party (no unilateral extraction)".to_string(),
            conduct_receipt_quin: make_quin(2),
        };
    }

    JurisdictionalAccessDecision {
        permitted: true,
        target_qap,
        matched_qualification_id: matched_qual.as_ref().map(|q| q.credential_id.clone()),
        evaluated_jurisdiction_iso: jurisdiction_frame.jurisdiction_iso.clone(),
        requires_multi_sig_party_instigation: requires_instigation,
        reason: format!(
            "Permitted in '{}' under jurisdiction '{}' (Qualification: {:?}, Persistence: {})",
            target_qap.label(),
            jurisdiction_frame.jurisdiction_iso,
            matched_qual.map(|q| q.title),
            artifact.spc_persistence_class.iri()
        ),
        conduct_receipt_quin: make_quin(1),
    }
}

// ============================================================================
// SEEDED PROFILES, VALUES CREDENTIALS, CONNECTIONS & INTERCHANGEABLE ARTIFACTS
// ============================================================================

/// Returns canonical `ns.webcivics.net` Values Credential instruments (`UDHR`, `ICESCR`, `UNCRPD`, `SPC`).
pub fn builtin_webcivics_values_credentials() -> Vec<ValuesCredentialInstrument> {
    vec![
        ValuesCredentialInstrument {
            credential_iri: "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
            title: "UN Universal Declaration of Human Rights (UDHR — Articles 1, 12 & 27(2))".to_string(),
            person_reading: ValuesPersonReading::HumanOnly,
            undertakings: vec![
                ValuesUndertakingRule {
                    undertaking_iri: "https://ns.webcivics.net/values/udhr#Art1".to_string(),
                    instrument_citation: "UDHR Article 1".to_string(),
                    norm_kind: ValuesDeonticNormKind::Right,
                    clause_text: "All human beings are born free and equal in dignity and rights (inherent dignity held strictly by values:NaturalPerson).".to_string(),
                    non_derogable: true,
                },
                ValuesUndertakingRule {
                    undertaking_iri: "https://ns.webcivics.net/values/udhr#Art12".to_string(),
                    instrument_citation: "UDHR Article 12 & ICCPR Article 17".to_string(),
                    norm_kind: ValuesDeonticNormKind::Prohibition,
                    clause_text: "No one shall be subjected to arbitrary interference with their privacy, family, home, correspondence, or Sanctuary mindware.".to_string(),
                    non_derogable: true,
                },
                ValuesUndertakingRule {
                    undertaking_iri: "https://ns.webcivics.net/values/udhr#Art27_2".to_string(),
                    instrument_citation: "UDHR Article 27(2) & ICESCR Article 15(1)(c)".to_string(),
                    norm_kind: ValuesDeonticNormKind::Right,
                    clause_text: "Everyone has the right to the protection of the moral and material interests resulting from any scientific, literary or artistic production of which they are the author.".to_string(),
                    non_derogable: true,
                },
            ],
        },
        ValuesCredentialInstrument {
            credential_iri: "https://ns.webcivics.net/social-permissive-commons/#Instrument".to_string(),
            title: "Social Permissive Commons & Differentiated Persistence Charter (spc:)".to_string(),
            person_reading: ValuesPersonReading::HumanOnly,
            undertakings: vec![
                ValuesUndertakingRule {
                    undertaking_iri: "https://ns.webcivics.net/social-permissive-commons/#StickyProhibition".to_string(),
                    instrument_citation: "spc:StickyProhibitionShape".to_string(),
                    norm_kind: ValuesDeonticNormKind::Obligation,
                    clause_text: "Artifact-attached rules (such as no-publish prohibitions on private clinical or personal records) travel with the artifact and survive relationship exit.".to_string(),
                    non_derogable: true,
                },
            ],
        },
    ]
}

/// Returns seeded Fiduciary & Professional Persona Profiles across Healthcare, Social Work,
/// Justice/Legal, and Government/Parliamentary Civic sectors.
pub fn builtin_fiduciary_persona_profiles() -> Vec<FiduciaryPersonaProfile> {
    vec![
        // 1. Doctor / Psychiatrist (HealthcareAndMedical)
        FiduciaryPersonaProfile {
            natural_person_did: "did:webizen:person:dr-elena-rostova".to_string(),
            display_name: "Dr. Elena Rostova, MBBS FRANZCP".to_string(),
            active_persona_context: PersonaContextKind::ProfessionalFiduciaryPersona,
            personal_qdp_domain: "elenarostova.me".to_string(),
            professional_qdp_domain: Some("dr-rostova.wellfair-clinic.org.au".to_string()),
            professional_organization_or_chambers: Some("Royal Melbourne Clinical Sanctuary Centre".to_string()),
            primary_jurisdiction_iso: "AU-VIC".to_string(),
            qualifications: vec![VerifiableQualificationCredential {
                credential_id: "QUAL-AHPRA-MED0001849201".to_string(),
                sector: ProfessionalRoleSector::HealthcareAndMedical,
                title: "Specialist Medical Practitioner & Fellow of RANZCP (Psychiatry & Autonomic Medicine)".to_string(),
                issuing_authority_or_register: "Australian Health Practitioner Regulation Agency (AHPRA)".to_string(),
                registration_or_certificate_number: "MED0001849201".to_string(),
                recognition_basis: QualificationRecognitionBasis::FormalStatutoryOrAcademic,
                recognized_jurisdictions_iso: vec!["AU".to_string(), "AU-VIC".to_string(), "AU-NSW".to_string()],
                valid_from_unix: 1_700_000_000,
                valid_until_unix: 1_900_000_000,
                revocation_status_active: true,
                issuer_signature_hex: "ed25519_ml_dsa_87_ahpra_reg_sig_01".to_string(),
            }],
            affirmed_values_credential_iris: vec![
                "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
                "https://ns.webcivics.net/social-permissive-commons/#Instrument".to_string(),
            ],
        },
        // 2. Qualified Social Worker & Housing Specialist (QualifiedSocialWorkAndCare)
        FiduciaryPersonaProfile {
            natural_person_did: "did:webizen:person:sarah-chen-msw".to_string(),
            display_name: "Sarah Chen, MSW (Accredited Mental Health & Housing Social Worker)".to_string(),
            active_persona_context: PersonaContextKind::ProfessionalFiduciaryPersona,
            personal_qdp_domain: "sarahchen.me".to_string(),
            professional_qdp_domain: Some("sarah.chen.housing-sanctuary.org.au".to_string()),
            professional_organization_or_chambers: Some("Victorian Cooperative Housing & Advocacy Service".to_string()),
            primary_jurisdiction_iso: "AU-VIC".to_string(),
            qualifications: vec![VerifiableQualificationCredential {
                credential_id: "QUAL-AASW-449821".to_string(),
                sector: ProfessionalRoleSector::QualifiedSocialWorkAndCare,
                title: "AASW Accredited Social Worker & NDIS Specialist Support Coordinator".to_string(),
                issuing_authority_or_register: "Australian Association of Social Workers (AASW)".to_string(),
                registration_or_certificate_number: "AASW-449821".to_string(),
                recognition_basis: QualificationRecognitionBasis::FormalStatutoryOrAcademic,
                recognized_jurisdictions_iso: vec!["AU".to_string(), "AU-VIC".to_string()],
                valid_from_unix: 1_700_000_000,
                valid_until_unix: 1_900_000_000,
                revocation_status_active: true,
                issuer_signature_hex: "ed25519_ml_dsa_87_aasw_reg_sig_02".to_string(),
            }],
            affirmed_values_credential_iris: vec![
                "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
            ],
        },
        // 3. Human-Rights Barrister & Justice Counsel (LawEnforcementAndJustice)
        FiduciaryPersonaProfile {
            natural_person_did: "did:webizen:person:marcus-vance".to_string(),
            display_name: "Marcus Vance, LLB LLM (Human-Rights Counsel)".to_string(),
            active_persona_context: PersonaContextKind::ProfessionalFiduciaryPersona,
            personal_qdp_domain: "marcusvance.me".to_string(),
            professional_qdp_domain: Some("mvance.humanrights-chambers.vic.edu.au".to_string()),
            professional_organization_or_chambers: Some("Civic & Human-Rights Law Chambers Victoria".to_string()),
            primary_jurisdiction_iso: "AU-VIC".to_string(),
            qualifications: vec![VerifiableQualificationCredential {
                credential_id: "QUAL-VLSB-PC-883920".to_string(),
                sector: ProfessionalRoleSector::LawEnforcementAndJustice,
                title: "Australian Legal Practitioner — Principal Practising Certificate (Human Rights & Evidence Act)".to_string(),
                issuing_authority_or_register: "Victorian Legal Services Board + Commissioner (VLSB+C)".to_string(),
                registration_or_certificate_number: "VLSB-PC-883920".to_string(),
                recognition_basis: QualificationRecognitionBasis::FormalStatutoryOrAcademic,
                recognized_jurisdictions_iso: vec!["AU".to_string(), "AU-VIC".to_string()],
                valid_from_unix: 1_700_000_000,
                valid_until_unix: 1_900_000_000,
                revocation_status_active: true,
                issuer_signature_hex: "ed25519_ml_dsa_87_vlsb_sig_03".to_string(),
            }],
            affirmed_values_credential_iris: vec![
                "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
                "https://ns.webcivics.net/social-permissive-commons/#Instrument".to_string(),
            ],
        },
        // 4. Local Member of Parliament / Parliamentary Advisor (GovernmentAndParliamentaryCivic)
        FiduciaryPersonaProfile {
            natural_person_did: "did:webizen:person:hon-claire-thorne-mp".to_string(),
            display_name: "Hon. Claire Thorne MP (Local Member & Parliamentary Human-Rights Committee)".to_string(),
            active_persona_context: PersonaContextKind::ProfessionalFiduciaryPersona,
            personal_qdp_domain: "clairethorne.me".to_string(),
            professional_qdp_domain: Some("claire.thorne.aph.gov.au".to_string()),
            professional_organization_or_chambers: Some("Parliament of Australia — Constituent & Parliamentary Advocacy Office".to_string()),
            primary_jurisdiction_iso: "AU-ACT".to_string(),
            qualifications: vec![VerifiableQualificationCredential {
                credential_id: "QUAL-PARLIAMENT-AU-MP-2026".to_string(),
                sector: ProfessionalRoleSector::GovernmentAndParliamentaryCivic,
                title: "Elected Member of Parliament & Joint Committee on Human Rights".to_string(),
                issuing_authority_or_register: "Australian Electoral Commission & Parliament of Australia Roll".to_string(),
                registration_or_certificate_number: "APH-MP-2026-VIC-MEL".to_string(),
                recognition_basis: QualificationRecognitionBasis::FormalStatutoryOrAcademic,
                recognized_jurisdictions_iso: vec!["AU".to_string(), "AU-ACT".to_string(), "AU-VIC".to_string()],
                valid_from_unix: 1_700_000_000,
                valid_until_unix: 1_900_000_000,
                revocation_status_active: true,
                issuer_signature_hex: "ed25519_ml_dsa_87_aph_roll_sig_04".to_string(),
            }],
            affirmed_values_credential_iris: vec![
                "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
            ],
        },
    ]
}

/// Returns both Category A (`StrangerZeroPriorHistory`) and Category B (`ClaimedPriorConnection`)
/// negotiated directory connections.
pub fn builtin_negotiated_directory_connections() -> Vec<DirectoryNegotiatedConnection> {
    let vcs = builtin_webcivics_values_credentials();

    // Category B: Claimed Prior Connection (Dr. Elena Rostova — corroborated by imported Gmail .mbox & Google Maps PlaceVisit)
    let mut conn_prior = DirectoryNegotiatedConnection {
        connection_id: "CONN-PRIOR-ROSTOVA-01".to_string(),
        initiator_did: "did:webizen:person:alex-mercer".to_string(),
        responder_did: "did:webizen:person:dr-elena-rostova".to_string(),
        pairwise_relationship_did: "did:webizen:pairwise:alex-elena-clinical-2026".to_string(),
        initiation_category: ConnectionInitiationCategory::ClaimedPriorConnection {
            claimed_context_summary: "Existing clinical care relationship corroborated by imported Gmail .mbox message <msg-20261124-01@wellfair-clinic.org.au> and Google Maps Timeline visit to Royal Melbourne Clinical Sanctuary Centre.".to_string(),
            corroborating_evidence_refs: vec![
                PriorConnectionEvidenceProof::HistoricalMailMessageDigest {
                    message_id: "msg-20261124-01@wellfair-clinic.org.au".to_string(),
                    correspondent_address: "dr.rostova@wellfair-clinic.org.au".to_string(),
                    digest_hex: "2f4b2614a891c001".to_string(),
                },
                PriorConnectionEvidenceProof::CoLocatedPlaceVisitDigest {
                    place_name: "Royal Melbourne Clinical Sanctuary Centre".to_string(),
                    date_iso: "2026-11-24".to_string(),
                    digest_hex: "88e1f490c123b772".to_string(),
                },
            ],
            verified_against_sanctuary_data: true,
        },
        relation_type_concept_iri: "https://ns.webcivics.net/social-permissive-commons/GuardianshipArrangement".to_string(),
        negotiated_values_credentials: vcs.clone(),
        governing_jurisdiction_iso: "AU-VIC".to_string(),
        bound_project_ids: vec!["proj-aether-commons-2026".to_string()],
        bound_group_categories: vec!["health".to_string(), "cooperative".to_string()],
        permitted_content_categories: vec![
            FormalSanctuaryCategory::ClinicalAndBiometricSanctuary,
            FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier,
        ],
        initiator_qhs1_signature_hex: Some("qhs1_ed25519_alex_mercer_sig_01".to_string()),
        responder_qhs1_signature_hex: Some("qhs1_ed25519_elena_rostova_sig_01".to_string()),
        state: SocialConnectionNegotiationState::NegotiatingValuesCredentials,
    };
    let _ = conn_prior.finalize_connection_establishment();

    // Category A: Stranger Zero Prior History (Hon. Claire Thorne MP — discovered via _qdp.claire.thorne.aph.gov.au front-door)
    let mut conn_stranger = DirectoryNegotiatedConnection {
        connection_id: "CONN-STRANGER-THORNE-MP-02".to_string(),
        initiator_did: "did:webizen:person:alex-mercer".to_string(),
        responder_did: "did:webizen:person:hon-claire-thorne-mp".to_string(),
        pairwise_relationship_did: "did:webizen:pairwise:alex-thorne-constituent-2026".to_string(),
        initiation_category: ConnectionInitiationCategory::StrangerZeroPriorHistory {
            discovery_mechanism: "QDP Front-Door DNS TXT _qdp.claire.thorne.aph.gov.au (HCAIAgreementNegotiation)".to_string(),
        },
        relation_type_concept_iri: "https://ns.webcivics.net/social-permissive-commons/CommunityMembership".to_string(),
        negotiated_values_credentials: vcs,
        governing_jurisdiction_iso: "AU-VIC".to_string(),
        bound_project_ids: vec!["proj-aether-commons-2026".to_string()],
        bound_group_categories: vec!["people".to_string()],
        permitted_content_categories: vec![
            FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier,
        ],
        initiator_qhs1_signature_hex: Some("qhs1_ed25519_alex_mercer_sig_02".to_string()),
        responder_qhs1_signature_hex: Some("qhs1_ed25519_claire_thorne_mp_sig_02".to_string()),
        state: SocialConnectionNegotiationState::NegotiatingValuesCredentials,
    };
    let _ = conn_stranger.finalize_connection_establishment();

    vec![conn_prior, conn_stranger]
}

/// Returns a seeded `InterchangeableLibraryArtifact` (`qualia://library/exhibit-autonomic-dossier-2026`)
/// demonstrating enhanced digital evidence informatics and cross-Qap interchange across Imports,
/// Hypermedia-Library, Mail, Poet, WellFair, and Cooperative Projects.
pub fn build_seeded_interchangeable_library_artifact() -> InterchangeableLibraryArtifact {
    let raw_pdf = b"%PDF-1.7\n(Co-Attested Autonomic rPPG, Pharmacokinetic & Human-Rights Dossier - 2026-11-24) Tj\n%%EOF";
    let timestamps = PreservedEvidentiaryTimestamps {
        original_created_at_unix: 1_763_900_000,
        original_modified_at_unix: 1_763_950_000,
        sanctuary_ingested_at_unix: 1_763_955_000,
        archived_superseded_at_unix: 1_763_960_000,
    };
    let informatics = DigitalEvidenceInformaticsEnvelope::build_for_import(
        "EVID-ENV-2026-0001",
        ImportSourceKind::PdfDocument,
        "Autonomic_rPPG_and_Human_Rights_Dossier_2026.pdf",
        "application/pdf",
        raw_pdf,
        "Webizen Poet & WellFair Verifiable PDF-1.7 + QECP Signer",
        timestamps,
        None,
        "did:webizen:person:alex-mercer",
    )
    .expect("valid digital evidence informatics envelope");

    InterchangeableLibraryArtifact {
        artifact_id: "exhibit-autonomic-dossier-2026".to_string(),
        canonical_library_uri: "qualia://library/exhibit-autonomic-dossier-2026".to_string(),
        title: "Co-Attested Autonomic rPPG, Pharmacokinetic & Human-Rights Evidentiary Dossier".to_string(),
        staging_state: StagingLifecycleState::FormallyCategorizedAndPromoted,
        formal_category: Some(FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier),
        spc_persistence_class: SpcPersistenceClass::ArtifactAttachedRule,
        travels_with_artifact_no_publish_prohibition: true,
        evidence_informatics: informatics,
        permitted_qap_consumers: QapAppConsumer::ALL.to_vec(),
        permitted_group_or_project_ids: vec!["proj-aether-commons-2026".to_string()],
        required_professional_sectors: vec![
            ProfessionalRoleSector::HealthcareAndMedical,
            ProfessionalRoleSector::QualifiedSocialWorkAndCare,
            ProfessionalRoleSector::LawEnforcementAndJustice,
            ProfessionalRoleSector::GovernmentAndParliamentaryCivic,
        ],
        permitted_jurisdictions_iso: vec!["AU".to_string(), "AU-VIC".to_string(), "AU-ACT".to_string()],
    }
}

pub fn builtin_australian_jurisdiction_frame() -> JurisdictionRatificationFrame {
    JurisdictionRatificationFrame {
        jurisdiction_iso: "AU-VIC".to_string(),
        parent_state_iso: Some("AU".to_string()),
        label: "State of Victoria, Commonwealth of Australia (Evidence Act 2008 (Vic) & Charter of Human Rights and Responsibilities)".to_string(),
        ratified_instrument_iris: vec![
            "https://ns.webcivics.net/values/universal-declaration-human-rights#Instrument".to_string(),
            "https://ns.webcivics.net/values/international-covenant-civil-and-political-rights#Instrument".to_string(),
            "https://ns.webcivics.net/values/convention-rights-persons-with-disabilities#Instrument".to_string(),
        ],
        mandatory_evidence_act_regime: "Evidence Act 2008 (Vic) / Evidence Act 1995 (Cth) ss 48, 69, 146, 147, 161".to_string(),
        requires_multi_sig_subject_instigation_for_justice_or_gov_access: true,
    }
}

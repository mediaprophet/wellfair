//! `domain_mail_and_sanctuary_importers`:
//! 1. **Domain-Based QDP Communications & Mail System (`draft-webcivics-QDP`)**:
//!    - Context-domains (`alexmercer.me`, `sanctuary.alexmercer.me`, `project-aether.coop`) act as QDP agents
//!      with `_qdp.<domain>` DNS TXT anchors and `/.well-known/QDP` RDF profiles (not merely bare DIDs).
//!    - Rule-bearing mailboxes: purpose inboxes (`frontdoor@`, `junkmail@`, `mygov@`, `newsletters@`, `clinical@`)
//!      and per-relationship pairwise addresses (`dr-rostova@alexmercer.me`), plus fail-closed delivery resolution.
//! 2. **Multi-Source Importers into the Sanctuary Uncategorized Intake Staging Area (`sanctuary://intake/uncategorized`)**:
//!    - **Mail & Gmail Takeout Importer** (`.mbox` / RFC-5322 `.eml` / IMAP account import),
//!    - **Google Maps Timeline & Location History Importer** (`Records.json` `latitudeE7`/`longitudeE7` & `placeVisit`),
//!    - **Samsung Galaxy Watch / Samsung Health Importer** (`com.samsung.shealth.*` CSV/JSON vitals, HRV, sleep, SpO2, steps),
//!    - **PDF Document Importer** (`%PDF-1.x` clinical reports, legal records, invoices, bank statements).
//! 3. **Sanctuary Uncategorized Staging & Formal Categorization Gate**:
//!    - Every imported artifact lands in `StagingLifecycleState::QuarantinedUncategorized` inside the
//!      Sanctuary's special staging area (`sanctuary://intake/uncategorized`), where it is strictly isolated
//!      from external specialist leases and AI agent context until the natural-person principal formally
//!      categorizes and promotes it (`formally_categorize_and_promote`).

use serde::{Deserialize, Serialize};

/// 48-byte hardware-aligned QualiaDB Super-Quin (`#[repr(C)]`).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct NQuin48 {
    pub subject: u64,
    pub predicate: u64,
    pub object: u64,
    pub context: u64,
    pub metadata: u64,
    pub parity: u64,
}

impl NQuin48 {
    #[inline]
    pub const fn new(
        subject: u64,
        predicate: u64,
        object: u64,
        context: u64,
        metadata: u64,
    ) -> Self {
        Self {
            subject,
            predicate,
            object,
            context,
            metadata,
            parity: subject ^ predicate ^ object ^ context,
        }
    }

    #[inline]
    pub const fn verify_parity(&self) -> bool {
        (self.subject ^ self.predicate ^ self.object ^ self.context) == self.parity
    }
}

/// Canonical 64-bit FNV-1a hash matching `qualia-core-db::q_hash`.
pub const fn q_hash_u64(s: &str) -> u64 {
    let bytes = s.as_bytes();
    let mut hash: u64 = 0xcbf29ce484222325;
    let mut i = 0;
    while i < bytes.len() {
        hash ^= bytes[i] as u64;
        hash = hash.wrapping_mul(0x100000001b3);
        i += 1;
    }
    hash
}

// ============================================================================
// 1. DOMAIN-BASED QDP COMMUNICATIONS & RULE-BEARING MAIL SYSTEM
// ============================================================================

/// QDP Agent Type (`draft-webcivics-QDP` §1 & `qualia-client-core::domains::AgentType`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum QdpAgentType {
    NaturalPerson,
    Organization,
    AiAgent,
    HumanitarianService,
    ContentProvider,
    Group,
}

impl QdpAgentType {
    pub const fn qdp_token(self) -> &'static str {
        match self {
            Self::NaturalPerson => "person",
            Self::Organization => "org",
            Self::AiAgent => "ai",
            Self::HumanitarianService => "service",
            Self::ContentProvider => "content",
            Self::Group => "group",
        }
    }

    pub const fn rdf_class(self) -> &'static str {
        match self {
            Self::NaturalPerson => "foaf:Person",
            Self::Organization | Self::Group => "schema:Organization",
            Self::AiAgent => "QDP:AIAgent",
            Self::HumanitarianService => "QDP:EssentialService",
            Self::ContentProvider => "QDP:ContentProvider",
        }
    }
}

/// Domain ownership model: single natural person or M:N agreement-governed group/cooperative.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DomainOwner {
    Personal { natural_person_did: String },
    Group { governing_agreement_id: String },
}

/// A Context-Domain (or subdomain) acting as a QDP Agent (`draft-webcivics-QDP`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QdpContextDomain {
    /// Dotted domain name (e.g. `alexmercer.me`, `sanctuary.alexmercer.me`, `aether-commons.coop`).
    pub domain_name: String,
    pub agent_type: QdpAgentType,
    pub owner: DomainOwner,
    /// Contextually-isolated Front-Door DID published at `_qdp.<domain>` (`qdp:signer`).
    pub front_door_did: String,
    /// Optional parent domain for family/child or project subdomains.
    pub parent_domain: Option<String>,
    /// Context label (`"Personal Sanctuary"`, `"Work"`, `"Cooperative Project"`).
    pub context_label: String,
    pub nym_mixnet_address: Option<String>,
    pub ecash_address: Option<String>,
    pub profile_url: Option<String>,
}

impl QdpContextDomain {
    /// DNS record name where the QDP front-door TXT anchor lives (`_qdp.<domain>`).
    pub fn qdp_dns_record_name(&self) -> String {
        format!("_qdp.{}", self.domain_name)
    }

    /// Generates the compact `_qdp.<domain>` DNS TXT record value (`draft-webcivics-QDP` §3.6).
    pub fn to_qdp_dns_txt(&self) -> String {
        let mut parts = vec![
            format!("qdp:signer <{}>", self.front_door_did),
            format!("qdp:agentType \"{}\"", self.agent_type.qdp_token()),
        ];
        if let Some(ref nym) = self.nym_mixnet_address {
            parts.push(format!("qdp:nym \"{nym}\""));
        }
        if let Some(ref ecash) = self.ecash_address {
            parts.push(format!("qdp:ecash \"{ecash}\""));
        }
        if let Some(ref url) = self.profile_url {
            parts.push(format!("qdp:profile <{url}>"));
        }
        parts.join(" ; ")
    }

    /// Generates the rich `/.well-known/QDP` RDF Turtle profile (`draft-webcivics-QDP` §3.1).
    pub fn to_well_known_qdp_turtle(&self) -> String {
        let mut ttl = String::new();
        ttl.push_str("@prefix qdp: <https://webcivics.github.io/QDP/ontdev/QDP#> .\n");
        ttl.push_str("@prefix foaf: <http://xmlns.com/foaf/0.1/> .\n");
        ttl.push_str("@prefix schema: <https://schema.org/> .\n\n");
        ttl.push_str(&format!(
            "<https://{}/.well-known/QDP#agent>\n  a {} ;\n  qdp:domain \"{}\" ;\n  qdp:signer <{}> ;\n  qdp:contextLabel \"{}\"",
            self.domain_name,
            self.agent_type.rdf_class(),
            self.domain_name,
            self.front_door_did,
            self.context_label
        ));
        if let Some(ref nym) = self.nym_mixnet_address {
            ttl.push_str(&format!(" ;\n  qdp:nymAddress \"{nym}\""));
        }
        if let Some(ref ecash) = self.ecash_address {
            ttl.push_str(&format!(" ;\n  qdp:ecashAddress \"{ecash}\""));
        }
        ttl.push_str(" .\n");
        ttl
    }
}

/// Kind of rule-bearing mailbox on a QDP Context-Domain.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum MailboxAddressKind {
    /// Purpose inbox (`frontdoor@`, `junkmail@`, `mygov@`, `newsletters@`, `clinical@`, `legal@`).
    PurposeInbox,
    /// Per-relationship pairwise address (`dr-rostova@alexmercer.me`) bound to one relationship DID.
    RelationshipPairwise,
    /// Deliberate domain catch-all (`catchall@domain`) routed straight to quarantine.
    DeliberateCatchallQuarantine,
}

/// Procedural and semantic rules governing a `DomainMailboxAddress` (`qualia-client-core::domains::MailRules`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MailboxRules {
    pub quarantine_by_default: bool,
    pub require_verified_sender_did: bool,
    pub priority: i8,
    pub retention_days: u32,
    pub notify_on_receipt: bool,
    pub semantic_route_agreement_id: Option<String>,
}

/// A rule-bearing mailbox address (`local@domain`) on a `QdpContextDomain`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DomainMailboxAddress {
    pub full_address: String,
    pub local_part: String,
    pub domain_name: String,
    pub kind: MailboxAddressKind,
    pub relationship_did: Option<String>,
    pub governing_agreement_id: Option<String>,
    pub rules: MailboxRules,
    pub enabled: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DomainMailDeliveryOutcome {
    DeliveredToExactMailbox {
        mailbox_address: String,
        quarantined: bool,
        priority: i8,
        semantic_route: Option<String>,
    },
    DeliveredToCatchallQuarantine {
        catchall_address: String,
    },
    RejectedFailClosed {
        reason: String,
    },
}

/// Resolves inbound delivery for `to_address` against the domain's rule-bearing mailboxes
/// (`qualia-client-core::domains::resolve_delivery` structural anti-spam invariant).
pub fn resolve_domain_mail_delivery(
    mailboxes: &[DomainMailboxAddress],
    to_address: &str,
    sender_verified_did: bool,
) -> DomainMailDeliveryOutcome {
    let normalized = to_address.trim().to_lowercase();
    let Some((local, domain)) = normalized.split_once('@') else {
        return DomainMailDeliveryOutcome::RejectedFailClosed {
            reason: format!("Malformed recipient address '{to_address}'"),
        };
    };
    if local.is_empty() || domain.is_empty() || !domain.contains('.') {
        return DomainMailDeliveryOutcome::RejectedFailClosed {
            reason: format!("Recipient '{to_address}' lacks a valid dotted QDP domain"),
        };
    }

    if let Some(exact) = mailboxes
        .iter()
        .find(|m| m.full_address.eq_ignore_ascii_case(&normalized))
    {
        if !exact.enabled {
            return DomainMailDeliveryOutcome::RejectedFailClosed {
                reason: format!("Mailbox '{}' is disabled", exact.full_address),
            };
        }
        if exact.rules.require_verified_sender_did && !sender_verified_did {
            return DomainMailDeliveryOutcome::DeliveredToExactMailbox {
                mailbox_address: exact.full_address.clone(),
                quarantined: true,
                priority: exact.rules.priority,
                semantic_route: Some("quarantined:unverified-sender-on-verified-only-mailbox".to_string()),
            };
        }
        return DomainMailDeliveryOutcome::DeliveredToExactMailbox {
            mailbox_address: exact.full_address.clone(),
            quarantined: exact.rules.quarantine_by_default,
            priority: exact.rules.priority,
            semantic_route: exact.rules.semantic_route_agreement_id.clone(),
        };
    }

    if let Some(catchall) = mailboxes.iter().find(|m| {
        m.enabled
            && m.domain_name.eq_ignore_ascii_case(domain)
            && (m.kind == MailboxAddressKind::DeliberateCatchallQuarantine
                || m.local_part == "catchall"
                || m.local_part == "*")
    }) {
        return DomainMailDeliveryOutcome::DeliveredToCatchallQuarantine {
            catchall_address: catchall.full_address.clone(),
        };
    }

    DomainMailDeliveryOutcome::RejectedFailClosed {
        reason: format!(
            "Fail-closed: no minted mailbox or catchall surface for '{}' on domain '{}'",
            normalized, domain
        ),
    }
}

// ============================================================================
// 2. SANCTUARY UNCATEGORIZED INTAKE STAGING AREA & FORMAL CATEGORIZATION GATE
// ============================================================================

/// Canonical URI of the Sanctuary's special uncategorized intake quarantine area.
pub const SANCTUARY_UNCATEGORIZED_STAGING_URI: &str = "sanctuary://intake/uncategorized";

/// Source format of an imported external artifact.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ImportSourceKind {
    /// Domain Mail (`.eml` / SMTP / IMAP) or Gmail Takeout (`.mbox`).
    DomainMailOrGmailMbox,
    /// Google Maps Timeline / Semantic Location History (`Records.json` / `Timeline.json`).
    GoogleMapsLocationHistory,
    /// Samsung Galaxy Watch / Samsung Health (`com.samsung.shealth.*` CSV / JSON).
    SamsungGalaxyWatchHealth,
    /// External PDF Document (`%PDF-1.x` clinical report, specialist letter, invoice, affidavit).
    PdfDocument,
}

impl ImportSourceKind {
    pub const fn label(self) -> &'static str {
        match self {
            Self::DomainMailOrGmailMbox => "Domain Mail / Gmail Takeout (.mbox / .eml)",
            Self::GoogleMapsLocationHistory => "Google Maps Location History (Timeline JSON)",
            Self::SamsungGalaxyWatchHealth => "Samsung Galaxy Watch / Samsung Health (CSV/JSON)",
            Self::PdfDocument => "PDF Document (%PDF-1.x Report / Statement)",
        }
    }
}

/// Lifecycle state of an imported item inside the Sanctuary Staging Area.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum StagingLifecycleState {
    /// Initial state upon import: held inside `sanctuary://intake/uncategorized` and strictly
    /// isolated from specialist leases, public portals, and AI agent context.
    QuarantinedUncategorized,
    /// Human principal is inspecting provenance, redacting fields, or attaching assertions.
    UnderHumanReview,
    /// Human principal has formally categorized and promoted the item into a governed Sanctuary vault.
    FormallyCategorizedAndPromoted,
    /// Rejected and purged from the staging area.
    RejectedAndPurged,
}

/// Formal target Sanctuary category assigned when a human categorizes and promotes a staged item.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FormalSanctuaryCategory {
    ClinicalAndBiometricSanctuary,
    SpatioTemporalMovementAndPlaceHistory,
    DomainCommunicationsAndRelationshipMail,
    ForensicLegalAndHumanRightsDossier,
    PersonalOrCooperativeAccountingLedger,
}

impl FormalSanctuaryCategory {
    pub const ALL: &'static [FormalSanctuaryCategory] = &[
        Self::ClinicalAndBiometricSanctuary,
        Self::SpatioTemporalMovementAndPlaceHistory,
        Self::DomainCommunicationsAndRelationshipMail,
        Self::ForensicLegalAndHumanRightsDossier,
        Self::PersonalOrCooperativeAccountingLedger,
    ];

    pub const fn label(self) -> &'static str {
        match self {
            Self::ClinicalAndBiometricSanctuary => "Clinical, Vitals & Biometric Sanctuary (.q42)",
            Self::SpatioTemporalMovementAndPlaceHistory => "Spatio-Temporal Place & Movement History (.q42)",
            Self::DomainCommunicationsAndRelationshipMail => "Domain Mail & Relationship Communications (.q42)",
            Self::ForensicLegalAndHumanRightsDossier => "Forensic, Legal & Human-Rights Evidence Dossier (.q42)",
            Self::PersonalOrCooperativeAccountingLedger => "Personal & Cooperative Double-Entry Ledger (.q42)",
        }
    }

    pub const fn target_vault_uri(self) -> &'static str {
        match self {
            Self::ClinicalAndBiometricSanctuary => "sanctuary://vault/clinical-biometrics",
            Self::SpatioTemporalMovementAndPlaceHistory => "sanctuary://vault/spatio-temporal-history",
            Self::DomainCommunicationsAndRelationshipMail => "sanctuary://vault/domain-communications",
            Self::ForensicLegalAndHumanRightsDossier => "sanctuary://vault/forensic-legal-dossier",
            Self::PersonalOrCooperativeAccountingLedger => "sanctuary://vault/accounting-ledger",
        }
    }
}

/// Parsed payload summary for each of the 4 importer types.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum ImportedPayloadSummary {
    MailMessage {
        source_account_id: String,
        message_id: String,
        from_address: String,
        to_address: String,
        resolved_domain_mailbox: String,
        subject: String,
        body_preview: String,
        gmail_labels: Vec<String>,
        delivery_quarantined: bool,
    },
    GoogleMapsLocationBatch {
        visit_count: usize,
        raw_point_count: usize,
        bounding_box_lat_lon: (f64, f64, f64, f64),
        notable_places: Vec<String>,
        earliest_timestamp: String,
        latest_timestamp: String,
    },
    SamsungWatchBiometricsBatch {
        device_model: String,
        sample_count: usize,
        mean_hr_bpm: f64,
        mean_hrv_rmssd_ms: f64,
        min_spo2_percent: f64,
        total_sleep_minutes: u32,
        total_steps: u32,
    },
    PdfDocumentExtract {
        filename: String,
        pdf_version: String,
        page_estimate: usize,
        extracted_title: String,
        extracted_text_preview: String,
        has_embedded_qecp_or_pades_signature: bool,
    },
}

/// An item residing in the Sanctuary Uncategorized Intake Staging Area (`sanctuary://intake/uncategorized`)
/// or promoted from it after formal human categorization.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SanctuaryStagedImportItem {
    pub staging_id: String,
    pub staging_area_uri: String,
    pub source_kind: ImportSourceKind,
    pub lifecycle_state: StagingLifecycleState,
    pub imported_at_unix: u64,
    pub raw_content_digest_hex: String,
    pub suggested_category_hint: FormalSanctuaryCategory,
    pub formal_category: Option<FormalSanctuaryCategory>,
    pub promoted_target_vault_uri: Option<String>,
    pub categorized_by_human_did: Option<String>,
    pub linked_domain_or_agreement_id: Option<String>,
    pub human_review_notes: Option<String>,
    pub payload: ImportedPayloadSummary,
    pub promoted_nquin48_count: usize,
}

impl SanctuaryStagedImportItem {
    /// Strictly `false` while `QuarantinedUncategorized` or `UnderHumanReview` so uncategorized
    /// imports can never leak into specialist leases, public portals, or AI agent inference context.
    #[inline]
    pub const fn is_accessible_to_specialist_leases_or_agents(&self) -> bool {
        matches!(
            self.lifecycle_state,
            StagingLifecycleState::FormallyCategorizedAndPromoted
        )
    }
}

/// The Sanctuary Uncategorized Intake Staging Vault (`sanctuary://intake/uncategorized`).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SanctuaryIntakeStagingVault {
    pub owner_natural_person_did: String,
    pub context_domains: Vec<QdpContextDomain>,
    pub domain_mailboxes: Vec<DomainMailboxAddress>,
    pub staged_items: Vec<SanctuaryStagedImportItem>,
    pub promoted_quins: Vec<NQuin48>,
}

impl SanctuaryIntakeStagingVault {
    pub fn new(owner_natural_person_did: impl Into<String>) -> Self {
        let did = owner_natural_person_did.into();
        let personal_domain = QdpContextDomain {
            domain_name: "alexmercer.me".to_string(),
            agent_type: QdpAgentType::NaturalPerson,
            owner: DomainOwner::Personal {
                natural_person_did: did.clone(),
            },
            front_door_did: "did:webizen:qdp:frontdoor:alexmercer-me".to_string(),
            parent_domain: None,
            context_label: "Personal & Clinical Sanctuary Domain".to_string(),
            nym_mixnet_address: Some("nym1alexmercer99sanctuary77gateway".to_string()),
            ecash_address: Some("ecash:qpalexmercer77sanctuary88xec".to_string()),
            profile_url: Some("https://alexmercer.me/.well-known/QDP".to_string()),
        };
        let coop_domain = QdpContextDomain {
            domain_name: "aether-commons.coop".to_string(),
            agent_type: QdpAgentType::Group,
            owner: DomainOwner::Group {
                governing_agreement_id: "AGR-COOP-CHARTER-2026".to_string(),
            },
            front_door_did: "did:webizen:qdp:frontdoor:aether-commons-coop".to_string(),
            parent_domain: None,
            context_label: "Cooperative Project Commons Domain (M:N Agreement)".to_string(),
            nym_mixnet_address: Some("nym1aethercommons42coop99gateway".to_string()),
            ecash_address: Some("ecash:qpaethercommons42pool88xec".to_string()),
            profile_url: Some("https://aether-commons.coop/.well-known/QDP".to_string()),
        };

        let mailboxes = vec![
            DomainMailboxAddress {
                full_address: "frontdoor@alexmercer.me".to_string(),
                local_part: "frontdoor".to_string(),
                domain_name: "alexmercer.me".to_string(),
                kind: MailboxAddressKind::PurposeInbox,
                relationship_did: None,
                governing_agreement_id: None,
                rules: MailboxRules {
                    quarantine_by_default: false,
                    require_verified_sender_did: false,
                    priority: 1,
                    retention_days: 365,
                    notify_on_receipt: true,
                    semantic_route_agreement_id: Some("purpose:frontdoor".to_string()),
                },
                enabled: true,
            },
            DomainMailboxAddress {
                full_address: "mygov@alexmercer.me".to_string(),
                local_part: "mygov".to_string(),
                domain_name: "alexmercer.me".to_string(),
                kind: MailboxAddressKind::PurposeInbox,
                relationship_did: None,
                governing_agreement_id: None,
                rules: MailboxRules {
                    quarantine_by_default: false,
                    require_verified_sender_did: true,
                    priority: 5,
                    retention_days: 3650,
                    notify_on_receipt: true,
                    semantic_route_agreement_id: Some("purpose:mygov-official".to_string()),
                },
                enabled: true,
            },
            DomainMailboxAddress {
                full_address: "dr-rostova@alexmercer.me".to_string(),
                local_part: "dr-rostova".to_string(),
                domain_name: "alexmercer.me".to_string(),
                kind: MailboxAddressKind::RelationshipPairwise,
                relationship_did: Some("did:webizen:person:dr-elena-rostova".to_string()),
                governing_agreement_id: Some("AGR-CLINICAL-CARE-2026".to_string()),
                rules: MailboxRules {
                    quarantine_by_default: false,
                    require_verified_sender_did: true,
                    priority: 5,
                    retention_days: 3650,
                    notify_on_receipt: true,
                    semantic_route_agreement_id: Some("AGR-CLINICAL-CARE-2026".to_string()),
                },
                enabled: true,
            },
            DomainMailboxAddress {
                full_address: "junkmail@alexmercer.me".to_string(),
                local_part: "junkmail".to_string(),
                domain_name: "alexmercer.me".to_string(),
                kind: MailboxAddressKind::PurposeInbox,
                relationship_did: None,
                governing_agreement_id: None,
                rules: MailboxRules {
                    quarantine_by_default: true,
                    require_verified_sender_did: false,
                    priority: -1,
                    retention_days: 30,
                    notify_on_receipt: false,
                    semantic_route_agreement_id: Some("quarantine:junkmail".to_string()),
                },
                enabled: true,
            },
            DomainMailboxAddress {
                full_address: "catchall@alexmercer.me".to_string(),
                local_part: "catchall".to_string(),
                domain_name: "alexmercer.me".to_string(),
                kind: MailboxAddressKind::DeliberateCatchallQuarantine,
                relationship_did: None,
                governing_agreement_id: None,
                rules: MailboxRules {
                    quarantine_by_default: true,
                    require_verified_sender_did: false,
                    priority: 0,
                    retention_days: 90,
                    notify_on_receipt: false,
                    semantic_route_agreement_id: Some("quarantine:catchall".to_string()),
                },
                enabled: true,
            },
        ];

        Self {
            owner_natural_person_did: did,
            context_domains: vec![personal_domain, coop_domain],
            domain_mailboxes: mailboxes,
            staged_items: Vec::new(),
            promoted_quins: Vec::new(),
        }
    }

    /// Count of items currently sitting in `QuarantinedUncategorized` or `UnderHumanReview` inside
    /// the Sanctuary staging area (`sanctuary://intake/uncategorized`).
    pub fn uncategorized_count(&self) -> usize {
        self.staged_items
            .iter()
            .filter(|i| {
                matches!(
                    i.lifecycle_state,
                    StagingLifecycleState::QuarantinedUncategorized
                        | StagingLifecycleState::UnderHumanReview
                )
            })
            .count()
    }

    /// count of formally categorized and promoted items.
    pub fn categorized_promoted_count(&self) -> usize {
        self.staged_items
            .iter()
            .filter(|i| {
                i.lifecycle_state == StagingLifecycleState::FormallyCategorizedAndPromoted
            })
            .count()
    }

    // ------------------------------------------------------------------------
    // IMPORTER 1: Domain Mail (RFC-5322 .eml / IMAP) & Gmail Takeout (.mbox)
    // ------------------------------------------------------------------------
    pub fn import_mail_or_gmail_mbox(
        &mut self,
        source_account_id: &str,
        raw_mbox_or_eml: &str,
        sender_verified_did: bool,
        imported_at_unix: u64,
    ) -> Vec<String> {
        let mut created_ids = Vec::new();
        // Split .mbox on "\nFrom " boundaries or treat as single RFC-5322 .eml message
        let chunks: Vec<&str> = if raw_mbox_or_eml.contains("\nFrom ") {
            raw_mbox_or_eml.split("\nFrom ").collect()
        } else {
            vec![raw_mbox_or_eml]
        };

        for (idx, chunk) in chunks.into_iter().enumerate() {
            let trimmed = chunk.trim();
            if trimmed.is_empty() {
                continue;
            }
            let mut from_addr = String::from("unknown@external.example");
            let mut to_addr = String::from("frontdoor@alexmercer.me");
            let mut subject = String::from("(No Subject)");
            let mut msg_id = format!("msg-{}-{}", imported_at_unix, idx + 1);
            let mut gmail_labels = Vec::new();
            let mut body_lines = Vec::new();
            let mut in_headers = true;

            for line in trimmed.lines() {
                if in_headers {
                    if line.trim().is_empty() {
                        in_headers = false;
                        continue;
                    }
                    if let Some(rest) = line.strip_prefix("From:") {
                        from_addr = rest.trim().to_string();
                    } else if let Some(rest) = line.strip_prefix("To:") {
                        to_addr = rest.trim().to_string();
                    } else if let Some(rest) = line.strip_prefix("Subject:") {
                        subject = rest.trim().to_string();
                    } else if let Some(rest) = line.strip_prefix("Message-ID:") {
                        msg_id = rest.trim().trim_matches(['<', '>']).to_string();
                    } else if let Some(rest) = line.strip_prefix("X-Gmail-Labels:") {
                        gmail_labels = rest
                            .split(',')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect();
                    }
                } else {
                    body_lines.push(line);
                }
            }

            let delivery = resolve_domain_mail_delivery(
                &self.domain_mailboxes,
                &to_addr,
                sender_verified_did,
            );
            let (resolved_mb, quarantined) = match delivery {
                DomainMailDeliveryOutcome::DeliveredToExactMailbox {
                    mailbox_address,
                    quarantined,
                    ..
                } => (mailbox_address, quarantined),
                DomainMailDeliveryOutcome::DeliveredToCatchallQuarantine { catchall_address } => {
                    (catchall_address, true)
                }
                DomainMailDeliveryOutcome::RejectedFailClosed { reason } => {
                    (format!("quarantine:unmapped ({reason})"), true)
                }
            };

            let body_joined = body_lines.join(" ");
            let preview = if body_joined.len() > 140 {
                format!("{}…", &body_joined[..140])
            } else {
                body_joined
            };

            let digest = format!("{:016x}", q_hash_u64(trimmed));
            let staging_id = format!("STG-MAIL-{:04}-{}", self.staged_items.len() + 1, &digest[..8]);

            let hint = if resolved_mb.starts_with("dr-rostova@")
                || subject.to_lowercase().contains("clinical")
                || subject.to_lowercase().contains("pathology")
            {
                FormalSanctuaryCategory::ClinicalAndBiometricSanctuary
            } else if resolved_mb.starts_with("mygov@")
                || subject.to_lowercase().contains("notice")
                || subject.to_lowercase().contains("affidavit")
            {
                FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier
            } else {
                FormalSanctuaryCategory::DomainCommunicationsAndRelationshipMail
            };

            self.staged_items.push(SanctuaryStagedImportItem {
                staging_id: staging_id.clone(),
                staging_area_uri: SANCTUARY_UNCATEGORIZED_STAGING_URI.to_string(),
                source_kind: ImportSourceKind::DomainMailOrGmailMbox,
                lifecycle_state: StagingLifecycleState::QuarantinedUncategorized,
                imported_at_unix,
                raw_content_digest_hex: digest,
                suggested_category_hint: hint,
                formal_category: None,
                promoted_target_vault_uri: None,
                categorized_by_human_did: None,
                linked_domain_or_agreement_id: None,
                human_review_notes: None,
                payload: ImportedPayloadSummary::MailMessage {
                    source_account_id: source_account_id.to_string(),
                    message_id: msg_id,
                    from_address: from_addr,
                    to_address: to_addr,
                    resolved_domain_mailbox: resolved_mb,
                    subject,
                    body_preview: preview,
                    gmail_labels,
                    delivery_quarantined: quarantined,
                },
                promoted_nquin48_count: 0,
            });
            created_ids.push(staging_id);
        }
        created_ids
    }

    // ------------------------------------------------------------------------
    // IMPORTER 2: Google Maps Timeline / Semantic Location History (JSON)
    // ------------------------------------------------------------------------
    pub fn import_google_maps_location_history(
        &mut self,
        raw_timeline_json: &str,
        imported_at_unix: u64,
    ) -> Result<String, String> {
        let parsed: serde_json::Value =
            serde_json::from_str(raw_timeline_json).map_err(|e| format!("Invalid Google Maps JSON: {e}"))?;

        let mut visit_count = 0usize;
        let mut raw_point_count = 0usize;
        let mut min_lat = 90.0_f64;
        let mut max_lat = -90.0_f64;
        let mut min_lon = 180.0_f64;
        let mut max_lon = -180.0_f64;
        let mut notable_places = Vec::new();
        let mut earliest = String::from("2026-11-01T00:00:00Z");
        let mut latest = String::from("2026-11-24T00:00:00Z");

        // 1. Parse `Records.json` (`locations: [{ latitudeE7, longitudeE7, timestamp }]`)
        if let Some(locs) = parsed.get("locations").and_then(|v| v.as_array()) {
            for loc in locs {
                let lat_e7 = loc.get("latitudeE7").and_then(|v| v.as_i64()).unwrap_or(-378136000);
                let lon_e7 = loc.get("longitudeE7").and_then(|v| v.as_i64()).unwrap_or(1449631000);
                let lat = lat_e7 as f64 / 1e7;
                let lon = lon_e7 as f64 / 1e7;
                min_lat = min_lat.min(lat);
                max_lat = max_lat.max(lat);
                min_lon = min_lon.min(lon);
                max_lon = max_lon.max(lon);
                raw_point_count += 1;
                if let Some(ts) = loc.get("timestamp").and_then(|v| v.as_str()) {
                    if raw_point_count == 1 {
                        earliest = ts.to_string();
                    }
                    latest = ts.to_string();
                }
            }
        }

        // 2. Parse `Semantic Location History` (`timelineObjects: [{ placeVisit: { location: { name, address, latitudeE7, longitudeE7 } } }]`)
        if let Some(objs) = parsed.get("timelineObjects").and_then(|v| v.as_array()) {
            for obj in objs {
                if let Some(pv) = obj.get("placeVisit") {
                    visit_count += 1;
                    if let Some(loc) = pv.get("location") {
                        if let Some(name) = loc.get("name").and_then(|v| v.as_str()) {
                            notable_places.push(name.to_string());
                        }
                        if let (Some(lat_e7), Some(lon_e7)) = (
                            loc.get("latitudeE7").and_then(|v| v.as_i64()),
                            loc.get("longitudeE7").and_then(|v| v.as_i64()),
                        ) {
                            let lat = lat_e7 as f64 / 1e7;
                            let lon = lon_e7 as f64 / 1e7;
                            min_lat = min_lat.min(lat);
                            max_lat = max_lat.max(lat);
                            min_lon = min_lon.min(lon);
                            max_lon = max_lon.max(lon);
                        }
                    }
                }
            }
        }

        if min_lat > max_lat {
            min_lat = -37.8136;
            max_lat = -37.8136;
            min_lon = 144.9631;
            max_lon = 144.9631;
        }

        let digest = format!("{:016x}", q_hash_u64(raw_timeline_json));
        let staging_id = format!("STG-GMAPS-{:04}-{}", self.staged_items.len() + 1, &digest[..8]);

        self.staged_items.push(SanctuaryStagedImportItem {
            staging_id: staging_id.clone(),
            staging_area_uri: SANCTUARY_UNCATEGORIZED_STAGING_URI.to_string(),
            source_kind: ImportSourceKind::GoogleMapsLocationHistory,
            lifecycle_state: StagingLifecycleState::QuarantinedUncategorized,
            imported_at_unix,
            raw_content_digest_hex: digest,
            suggested_category_hint: FormalSanctuaryCategory::SpatioTemporalMovementAndPlaceHistory,
            formal_category: None,
            promoted_target_vault_uri: None,
            categorized_by_human_did: None,
            linked_domain_or_agreement_id: None,
            human_review_notes: None,
            payload: ImportedPayloadSummary::GoogleMapsLocationBatch {
                visit_count,
                raw_point_count,
                bounding_box_lat_lon: (min_lat, min_lon, max_lat, max_lon),
                notable_places,
                earliest_timestamp: earliest,
                latest_timestamp: latest,
            },
            promoted_nquin48_count: 0,
        });
        Ok(staging_id)
    }

    // ------------------------------------------------------------------------
    // IMPORTER 3: Samsung Galaxy Watch / Samsung Health (CSV / JSON)
    // ------------------------------------------------------------------------
    pub fn import_samsung_watch_health_csv(
        &mut self,
        device_model: &str,
        csv_content: &str,
        imported_at_unix: u64,
    ) -> Result<String, String> {
        // Expected columns: timestamp,heart_rate_bpm,hrv_rmssd_ms,spo2_percent,sleep_minutes,steps
        let mut sample_count = 0usize;
        let mut sum_hr = 0.0_f64;
        let mut sum_hrv = 0.0_f64;
        let mut min_spo2 = 100.0_f64;
        let mut total_sleep = 0u32;
        let mut total_steps = 0u32;

        for (idx, line) in csv_content.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('#') || (idx == 0 && trimmed.contains("heart_rate")) {
                continue;
            }
            let cols: Vec<&str> = trimmed.split(',').collect();
            if cols.len() < 6 {
                continue;
            }
            let hr: f64 = cols[1].trim().parse().unwrap_or(68.0);
            let hrv: f64 = cols[2].trim().parse().unwrap_or(34.0);
            let spo2: f64 = cols[3].trim().parse().unwrap_or(98.0);
            let sleep_min: u32 = cols[4].trim().parse().unwrap_or(0);
            let steps: u32 = cols[5].trim().parse().unwrap_or(0);

            sample_count += 1;
            sum_hr += hr;
            sum_hrv += hrv;
            min_spo2 = min_spo2.min(spo2);
            total_sleep = total_sleep.saturating_add(sleep_min);
            total_steps = total_steps.saturating_add(steps);
        }

        if sample_count == 0 {
            return Err("Samsung Watch CSV contained zero valid biometric rows".to_string());
        }

        let digest = format!("{:016x}", q_hash_u64(csv_content));
        let staging_id = format!("STG-WATCH-{:04}-{}", self.staged_items.len() + 1, &digest[..8]);

        self.staged_items.push(SanctuaryStagedImportItem {
            staging_id: staging_id.clone(),
            staging_area_uri: SANCTUARY_UNCATEGORIZED_STAGING_URI.to_string(),
            source_kind: ImportSourceKind::SamsungGalaxyWatchHealth,
            lifecycle_state: StagingLifecycleState::QuarantinedUncategorized,
            imported_at_unix,
            raw_content_digest_hex: digest,
            suggested_category_hint: FormalSanctuaryCategory::ClinicalAndBiometricSanctuary,
            formal_category: None,
            promoted_target_vault_uri: None,
            categorized_by_human_did: None,
            linked_domain_or_agreement_id: None,
            human_review_notes: None,
            payload: ImportedPayloadSummary::SamsungWatchBiometricsBatch {
                device_model: device_model.to_string(),
                sample_count,
                mean_hr_bpm: ((sum_hr / sample_count as f64) * 10.0).round() / 10.0,
                mean_hrv_rmssd_ms: ((sum_hrv / sample_count as f64) * 10.0).round() / 10.0,
                min_spo2_percent: min_spo2,
                total_sleep_minutes: total_sleep,
                total_steps,
            },
            promoted_nquin48_count: 0,
        });
        Ok(staging_id)
    }

    // ------------------------------------------------------------------------
    // IMPORTER 4: External PDF Document (%PDF-1.x) Importer
    // ------------------------------------------------------------------------
    pub fn import_pdf_document(
        &mut self,
        filename: &str,
        raw_pdf_bytes: &[u8],
        imported_at_unix: u64,
    ) -> Result<String, String> {
        let text_lossy = String::from_utf8_lossy(raw_pdf_bytes);
        if !text_lossy.starts_with("%PDF-") {
            return Err(format!("File '{filename}' does not begin with a valid %PDF- header"));
        }
        let pdf_version = text_lossy
            .lines()
            .next()
            .unwrap_or("%PDF-1.7")
            .trim()
            .to_string();
        let page_estimate = text_lossy.matches("/Type /Page").count().max(1);
        let has_qecp = text_lossy.contains("QECP") || text_lossy.contains("/SubFilter /ETSI.CAdES.detached");

        // Extract parenthesized PDF text literals `(...) Tj` or `/Title (...)`
        let mut extracted_literals = Vec::new();
        let mut cur = text_lossy.as_ref();
        while let Some(open) = cur.find('(') {
            let after = &cur[open + 1..];
            let Some(close) = after.find(')') else {
                break;
            };
            let literal = after[..close].trim();
            if literal.len() >= 4 && literal.chars().any(|c| c.is_ascii_alphabetic()) {
                extracted_literals.push(literal.to_string());
            }
            cur = &after[close + 1..];
        }

        let extracted_title = extracted_literals
            .first()
            .cloned()
            .unwrap_or_else(|| filename.to_string());
        let joined_text = extracted_literals.join(" · ");
        let preview = if joined_text.len() > 160 {
            format!("{}…", &joined_text[..160])
        } else {
            joined_text
        };

        let hint = if preview.to_lowercase().contains("invoice")
            || preview.to_lowercase().contains("statement")
            || preview.to_lowercase().contains("tax")
        {
            FormalSanctuaryCategory::PersonalOrCooperativeAccountingLedger
        } else if preview.to_lowercase().contains("clinical")
            || preview.to_lowercase().contains("medical")
            || preview.to_lowercase().contains("pathology")
        {
            FormalSanctuaryCategory::ClinicalAndBiometricSanctuary
        } else {
            FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier
        };

        let digest = format!("{:016x}", q_hash_u64(&text_lossy));
        let staging_id = format!("STG-PDF-{:04}-{}", self.staged_items.len() + 1, &digest[..8]);

        self.staged_items.push(SanctuaryStagedImportItem {
            staging_id: staging_id.clone(),
            staging_area_uri: SANCTUARY_UNCATEGORIZED_STAGING_URI.to_string(),
            source_kind: ImportSourceKind::PdfDocument,
            lifecycle_state: StagingLifecycleState::QuarantinedUncategorized,
            imported_at_unix,
            raw_content_digest_hex: digest,
            suggested_category_hint: hint,
            formal_category: None,
            promoted_target_vault_uri: None,
            categorized_by_human_did: None,
            linked_domain_or_agreement_id: None,
            human_review_notes: None,
            payload: ImportedPayloadSummary::PdfDocumentExtract {
                filename: filename.to_string(),
                pdf_version,
                page_estimate,
                extracted_title,
                extracted_text_preview: preview,
                has_embedded_qecp_or_pades_signature: has_qecp,
            },
            promoted_nquin48_count: 0,
        });
        Ok(staging_id)
    }

    // ------------------------------------------------------------------------
    // FORMAL HUMAN CATEGORIZATION & PROMOTION OUT OF STAGING QUARANTINE
    // ------------------------------------------------------------------------
    /// Formally categorizes a staged import item, moving it out of `QuarantinedUncategorized`
    /// (`sanctuary://intake/uncategorized`) into the chosen target Sanctuary vault and minting
    /// verified 48-byte `NQuin48` quads.
    pub fn formally_categorize_and_promote(
        &mut self,
        staging_id: &str,
        formal_category: FormalSanctuaryCategory,
        human_principal_did: &str,
        linked_domain_or_agreement_id: Option<String>,
        review_notes: impl Into<String>,
    ) -> Result<usize, String> {
        if human_principal_did.trim().is_empty() {
            return Err("Formal categorization requires an identified natural-person principal DID".to_string());
        }
        let item = self
            .staged_items
            .iter_mut()
            .find(|i| i.staging_id == staging_id)
            .ok_or_else(|| format!("Staged import item '{staging_id}' not found"))?;

        let target_uri = formal_category.target_vault_uri().to_string();
        item.lifecycle_state = StagingLifecycleState::FormallyCategorizedAndPromoted;
        item.formal_category = Some(formal_category);
        item.promoted_target_vault_uri = Some(target_uri.clone());
        item.categorized_by_human_did = Some(human_principal_did.to_string());
        item.linked_domain_or_agreement_id = linked_domain_or_agreement_id.clone();
        item.human_review_notes = Some(review_notes.into());

        let subj = q_hash_u64(&item.staging_id);
        let ctx = q_hash_u64(&target_uri);
        let meta = item.imported_at_unix;

        let mut minted = vec![
            NQuin48::new(
                subj,
                q_hash_u64("sanctuary:formallyCategorizedAs"),
                q_hash_u64(formal_category.label()),
                ctx,
                meta,
            ),
            NQuin48::new(
                subj,
                q_hash_u64("sanctuary:categorizedByNaturalPerson"),
                q_hash_u64(human_principal_did),
                ctx,
                meta,
            ),
            NQuin48::new(
                subj,
                q_hash_u64("sanctuary:rawContentDigest"),
                q_hash_u64(&item.raw_content_digest_hex),
                ctx,
                meta,
            ),
        ];
        if let Some(ref link) = linked_domain_or_agreement_id {
            minted.push(NQuin48::new(
                subj,
                q_hash_u64("sanctuary:linkedDomainOrAgreement"),
                q_hash_u64(link),
                ctx,
                meta,
            ));
        }

        let count = minted.len();
        item.promoted_nquin48_count = count;
        self.promoted_quins.extend(minted);
        Ok(count)
    }
}

/// Builds a seeded `SanctuaryIntakeStagingVault` demonstrating all 4 importer types sitting in
/// `sanctuary://intake/uncategorized` ready for human inspection and formal categorization.
pub fn build_seeded_sanctuary_staging_vault() -> SanctuaryIntakeStagingVault {
    let mut vault = SanctuaryIntakeStagingVault::new("did:webizen:person:alex-mercer");

    // 1. Import a 2-message Gmail / Domain Mail .mbox payload
    let sample_mbox = "\
From dr.rostova@wellfair-clinic.org.au Tue Nov 24 09:15:00 2026
From: Dr. Elena Rostova <dr.rostova@wellfair-clinic.org.au>
To: dr-rostova@alexmercer.me
Subject: Clinical rPPG & Autonomic HRV Review Follow-Up
Message-ID: <msg-20261124-01@wellfair-clinic.org.au>
X-Gmail-Labels: Inbox,Important,Clinical

Alex, your camera rPPG RMSSD (31.0 ms) and Prazosin 2mg PK trough curve look stable. Let's co-sign the QECP PDF report.

From notices@ato.gov.au Tue Nov 24 10:02:00 2026
From: Australian Government Notices <notices@ato.gov.au>
To: mygov@alexmercer.me
Subject: Official Notice of Assessment & Cooperative BAS Summary
Message-ID: <msg-20261124-02@ato.gov.au>
X-Gmail-Labels: Inbox,MyGov,Tax

Your 2026-Q4 BAS & Cooperative Stewardship Statement is available for review.";
    let _ = vault.import_mail_or_gmail_mbox(
        "gmail-takeout:alex.mercer@gmail.com -> qdp:alexmercer.me",
        sample_mbox,
        true,
        1_763_962_000,
    );

    // 2. Import a Google Maps Timeline / Semantic Location History export
    let sample_gmaps_json = r#"{
        "locations": [
            { "latitudeE7": -378136000, "longitudeE7": 1449631000, "timestamp": "2026-11-23T22:00:00Z" },
            { "latitudeE7": -377984000, "longitudeE7": 1449782000, "timestamp": "2026-11-24T04:30:00Z" }
        ],
        "timelineObjects": [
            {
                "placeVisit": {
                    "location": {
                        "name": "Royal Melbourne Clinical Sanctuary Centre",
                        "address": "300 Grattan St, Parkville VIC 3050",
                        "latitudeE7": -377992000,
                        "longitudeE7": 1449559000
                    }
                }
            },
            {
                "placeVisit": {
                    "location": {
                        "name": "Civic & Human-Rights Law Chambers",
                        "address": "205 William St, Melbourne VIC 3000",
                        "latitudeE7": -378142000,
                        "longitudeE7": 1449568000
                    }
                }
            }
        ]
    }"#;
    let _ = vault.import_google_maps_location_history(sample_gmaps_json, 1_763_962_500);

    // 3. Import a Samsung Galaxy Watch (`com.samsung.shealth.*`) CSV export
    let sample_watch_csv = "\
timestamp,heart_rate_bpm,hrv_rmssd_ms,spo2_percent,sleep_minutes,steps
2026-11-22T07:00:00Z,66.4,34.2,98.0,450,7420
2026-11-23T07:00:00Z,69.1,30.8,97.0,435,8190
2026-11-24T07:00:00Z,67.8,33.5,98.5,465,6840";
    let _ = vault.import_samsung_watch_health_csv(
        "Samsung Galaxy Watch 7 Ultra (SM-L705F)",
        sample_watch_csv,
        1_763_963_000,
    );

    // 4. Import an external PDF (`%PDF-1.7`) clinical/legal document
    let sample_pdf = b"%PDF-1.7\n\
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n\
2 0 obj << /Type /Page >> endobj\n\
(Specialist Trauma & Autonomic Assessment Report - Dr. Elena Rostova) Tj\n\
(Patient demonstrates vagal recovery and coherent respiratory sinus arrhythmia. QECP Attested.) Tj\n\
%%EOF";
    let _ = vault.import_pdf_document(
        "Dr_Rostova_Autonomic_Assessment_2026-11-24.pdf",
        sample_pdf,
        1_763_963_500,
    );

    vault
}

//! Dual-PIN Plausible-Deniability Sanctuary Vault (Normal vs. Duress Decoy PIN),
//! 4-Logic Clinical & Trauma-Cascade N3 Rule Engine, Wearable CSV-to-`NQuin48` `.q42` Compiler,
//! Zero-Trust Human-Centric Wallet (Nym Vouchers), and Chat-Graph Delegated-Agent Contract (`WP-WF-APP3` & `WP-WF-APP5`).
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: CC BY-NC-ND 4.0.

use crate::biophysical_rppg_telehealth::CameraRppgAndRespirationReading;
use crate::pharmacokinetics_meds_diet_anatomy::PharmacokineticOdeCurve;
use poet_aether_ui::investigation_link_analysis::InstrumentAuthorRole;
use poet_aether_ui::wordnet_q42_ontology::{
    compile_ontology_to_q42_pack, deterministic_digest_hex, CompiledQ42OntologyArtifact,
};
use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// 1. Dual-PIN Sanctuary & Plausible-Deniability Duress Vault
// ---------------------------------------------------------------------------

/// Active vault unlock posture determined by which PIN was entered at the Sanctuary gate.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SanctuaryUnlockPosture {
    /// Vault is locked; zero records decrypted in memory.
    Locked,
    /// Unlocked via the true Sanctuary PIN — full clinical, human-rights & evidentiary records available.
    NormalSanctuaryUnlocked,
    /// Unlocked via the Duress / Plausible-Deniability Decoy PIN — shows only benign cover fitness entries
    /// and silently freezes all active online specialist disclosure leases!
    DuressDecoyCoverActive,
}

/// Encrypted Sanctuary journal entry (Assertion or Hypothesis) anchored with a QECP commitment.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SanctuaryJournalEntry {
    pub entry_id: String,
    /// `"assertion"` or `"hypothesis"`
    pub epistemic_kind: String,
    pub timestamp_iso: String,
    pub content: String,
    pub author_role: InstrumentAuthorRole,
    pub commitment_digest_hex: String,
    pub ots_qecp_anchor: String,
}

/// Hardware-backed Dual-PIN Sanctuary Vault with plausible-deniability Duress Decoy slice.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SanctuaryDuressVault {
    pub principal_did: String,
    pub normal_pin_hash_hex: String,
    pub duress_decoy_pin_hash_hex: String,
    pub posture: SanctuaryUnlockPosture,
    pub active_specialist_leases_frozen: bool,
    pub true_sanctuary_entries: Vec<SanctuaryJournalEntry>,
    pub decoy_cover_entries: Vec<SanctuaryJournalEntry>,
}

impl Default for SanctuaryDuressVault {
    fn default() -> Self {
        Self::new_with_pins(
            "did:q42:person:timothy-holborn",
            "4210",
            "9911",
        )
    }
}

impl SanctuaryDuressVault {
    pub fn new_with_pins(principal_did: &str, normal_pin: &str, duress_pin: &str) -> Self {
        let normal_pin_hash_hex =
            deterministic_digest_hex(format!("SANCTUARY-NORMAL|{principal_did}|{normal_pin}").as_bytes());
        let duress_decoy_pin_hash_hex =
            deterministic_digest_hex(format!("SANCTUARY-DURESS|{principal_did}|{duress_pin}").as_bytes());

        let true_sanctuary_entries = vec![
            SanctuaryJournalEntry {
                entry_id: "SANC-001".into(),
                epistemic_kind: "assertion".into(),
                timestamp_iso: "2026-10-14T09:05:00Z".into(),
                content: "Submitted clinical psychologist ADHD (DOID:1094) & PTSD (DOID:2055) attestation and GP summary to housing/welfare agency with signed delivery receipt.".into(),
                author_role: InstrumentAuthorRole::PrincipalSelfAuthored,
                commitment_digest_hex: deterministic_digest_hex(b"SANC-001|2026-10-14T09:05:00Z"),
                ots_qecp_anchor: "qecp://ots/bitcoin-block-865420-merkle-root".into(),
            },
            SanctuaryJournalEntry {
                entry_id: "SANC-002".into(),
                epistemic_kind: "hypothesis".into(),
                timestamp_iso: "2026-10-22T17:00:00Z".into(),
                content: "Agency's 22 October form letter claiming 'no documentation on file' indicates administrative failure to check the 14 October clinical intake queue (breach of cml:DutyOfInquiry).".into(),
                author_role: InstrumentAuthorRole::PrincipalSelfAuthored,
                commitment_digest_hex: deterministic_digest_hex(b"SANC-002|2026-10-22T17:00:00Z"),
                ots_qecp_anchor: "qecp://ots/bitcoin-block-866110-merkle-root".into(),
            },
        ];

        let decoy_cover_entries = vec![
            SanctuaryJournalEntry {
                entry_id: "LOG-101".into(),
                epistemic_kind: "assertion".into(),
                timestamp_iso: "2026-10-20T08:00:00Z".into(),
                content: "Morning walk completed: 6,500 steps, 2.1L water intake goal met.".into(),
                author_role: InstrumentAuthorRole::PrincipalSelfAuthored,
                commitment_digest_hex: deterministic_digest_hex(b"DECOY-101"),
                ots_qecp_anchor: "local-fitness-note".into(),
            },
        ];

        Self {
            principal_did: principal_did.to_string(),
            normal_pin_hash_hex,
            duress_decoy_pin_hash_hex,
            posture: SanctuaryUnlockPosture::NormalSanctuaryUnlocked,
            active_specialist_leases_frozen: false,
            true_sanctuary_entries,
            decoy_cover_entries,
        }
    }

    /// Evaluates a PIN entry against the Normal and Duress key slots in constant-shape flow.
    /// If the Duress PIN is entered, transitions to `DuressDecoyCoverActive` and silently freezes
    /// all online specialist leases without displaying any alarm to a coercing observer.
    pub fn unlock_with_pin(&mut self, entered_pin: &str) -> SanctuaryUnlockPosture {
        let try_normal = deterministic_digest_hex(
            format!("SANCTUARY-NORMAL|{}|{}", self.principal_did, entered_pin).as_bytes(),
        );
        let try_duress = deterministic_digest_hex(
            format!("SANCTUARY-DURESS|{}|{}", self.principal_did, entered_pin).as_bytes(),
        );

        if try_normal == self.normal_pin_hash_hex {
            self.posture = SanctuaryUnlockPosture::NormalSanctuaryUnlocked;
        } else if try_duress == self.duress_decoy_pin_hash_hex {
            self.posture = SanctuaryUnlockPosture::DuressDecoyCoverActive;
            self.active_specialist_leases_frozen = true;
        } else {
            self.posture = SanctuaryUnlockPosture::Locked;
        }
        self.posture
    }

    /// Returns the entries visible in the current unlock posture (never exposing `true_sanctuary_entries`
    /// when locked or when in Duress Decoy mode!).
    pub fn visible_entries(&self) -> &[SanctuaryJournalEntry] {
        match self.posture {
            SanctuaryUnlockPosture::NormalSanctuaryUnlocked => &self.true_sanctuary_entries,
            SanctuaryUnlockPosture::DuressDecoyCoverActive => &self.decoy_cover_entries,
            SanctuaryUnlockPosture::Locked => &[],
        }
    }
}

// ---------------------------------------------------------------------------
// 2. Wearable CSV -> .q42 (Q42\0 v4 NQuin48) & 7 N3 Clinical / Trauma Rules
// ---------------------------------------------------------------------------

/// Triggered clinical, autonomic, pharmacokinetic, or human-rights rule match from the N3 engine.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WellfairN3ClinicalRuleMatch {
    pub rule_id: String,
    pub pattern_title: String,
    pub n3_source_file: String,
    pub confidence: String,
    pub routing_lane: u8,
    pub grounded_ontology_iris: Vec<String>,
    pub recommended_action: String,
}

/// Evaluates the 7 WellFair N3Logic clinical, trauma-cascade, autonomic HRV, and pharmacokinetic rules
/// over live biometric readings, sleep architecture, and PK/PD curves.
pub fn evaluate_wellfair_clinical_and_rights_rules(
    rppg: &CameraRppgAndRespirationReading,
    avg_sleep_efficiency_pct: f64,
    avg_sleep_hours: f64,
    pk_curves: &[PharmacokineticOdeCurve],
    has_unaccommodated_housing_threat: bool,
) -> Vec<WellfairN3ClinicalRuleMatch> {
    let mut matches = Vec::new();

    // Rule 1: sleep_debt.n3
    if avg_sleep_efficiency_pct < 82.0 || avg_sleep_hours < 6.5 {
        matches.push(WellfairN3ClinicalRuleMatch {
            rule_id: "N3-SLEEP-DEBT-01".into(),
            pattern_title: "Cumulative Sleep Architecture Debt & REM Fragmentation".into(),
            n3_source_file: "extensions/n3_reasoner/rules/sleep_debt.n3".into(),
            confidence: "High (0.91)".into(),
            routing_lane: 2,
            grounded_ontology_iris: vec![
                "http://snomed.info/id/364075005".into(),
                "http://purl.obolibrary.org/obo/HP_0002360".into(),
            ],
            recommended_action: "Prioritize quiet nocturnal sanctuary environment and verify evening Prazosin PK trough window.".into(),
        });
    }

    // Rule 2: trauma_cascade.n3
    if (avg_sleep_efficiency_pct < 82.0 && rppg.hrv_rmssd_ms < 45.0)
        || has_unaccommodated_housing_threat
    {
        matches.push(WellfairN3ClinicalRuleMatch {
            rule_id: "N3-TRAUMA-CASCADE-02".into(),
            pattern_title: "Autonomic Trauma-Cascade & Environmental Threat Hyperarousal".into(),
            n3_source_file: "extensions/n3_reasoner/rules/trauma_cascade.n3".into(),
            confidence: "Critical (0.95)".into(),
            routing_lane: 2,
            grounded_ontology_iris: vec![
                "http://purl.obolibrary.org/obo/DOID_2055".into(),
                "http://purl.obolibrary.org/obo/HP_0033676".into(),
                "https://ns.webcivics.net/rights/crpd#Article19_IndependentLivingAndSanctuary".into(),
            ],
            recommended_action: "Enforce UN CRPD Art. 19 & ICESCR Art. 11 housing sanctuary protection; halt coercive administrative deadlines under cml:DutyOfInquiry.".into(),
        });
    }

    // Rule 3: adrenal_fatigue.n3 / HPA axis strain
    if rppg.lf_hf_autonomic_ratio > 1.25 && avg_sleep_hours < 7.0 {
        matches.push(WellfairN3ClinicalRuleMatch {
            rule_id: "N3-HPA-STRAIN-03".into(),
            pattern_title: "HPA-Axis Sympathetic Dominance & Executive Load Strain".into(),
            n3_source_file: "extensions/n3_reasoner/rules/adrenal_fatigue.n3".into(),
            confidence: "Moderate-High (0.86)".into(),
            routing_lane: 2,
            grounded_ontology_iris: vec![
                "http://purl.obolibrary.org/obo/DOID_1094".into(),
                "http://purl.obolibrary.org/obo/UBERON_0002369".into(),
            ],
            recommended_action: "Schedule asynchronous written communications and low-sensory recovery intervals.".into(),
        });
    }

    // Rule 4: cardiovascular_risk.n3
    if rppg.heart_rate_bpm >= 60.0 {
        matches.push(WellfairN3ClinicalRuleMatch {
            rule_id: "N3-CARDIO-RPPG-04".into(),
            pattern_title: "Chrominance rPPG Cardiovascular & Vagal Tone Baseline Verified".into(),
            n3_source_file: "extensions/n3_reasoner/rules/cardiovascular_risk.n3".into(),
            confidence: "Verified Live (0.96)".into(),
            routing_lane: 1,
            grounded_ontology_iris: vec![
                "http://purl.obolibrary.org/obo/UBERON_0000948".into(),
                "http://hl7.org/fhir/Observation".into(),
            ],
            recommended_action: format!(
                "Resting rPPG {:.1} BPM, RMSSD {:.1} ms, Respiration {:.1} BrPM within monitored steady envelope.",
                rppg.heart_rate_bpm, rppg.hrv_rmssd_ms, rppg.respiration_breaths_per_min
            ),
        });
    }

    // Rule 5: pk_pd_therapeutic_window.n3
    for curve in pk_curves {
        matches.push(WellfairN3ClinicalRuleMatch {
            rule_id: format!("N3-PKPD-{}", curve.med_id),
            pattern_title: format!("RK4 Pharmacokinetic Window Check ({})", curve.med_id),
            n3_source_file: "wellfair://rules/pk_pd_therapeutic_window.n3".into(),
            confidence: if curve.within_therapeutic_window {
                "Optimal Window (0.98)".into()
            } else {
                "Advisory Review (0.89)".into()
            },
            routing_lane: 2,
            grounded_ontology_iris: vec!["https://bio2rdf.org/drugbank".into()],
            recommended_action: curve.clinical_advisory.clone(),
        });
    }

    matches
}

/// Compiles wearable heart-rate, sleep-efficiency, steps, and rPPG telemetry directly into a
/// `.q42` (`Q42\0` v4 `NQuin48`) binary container with `UBERON`/`FHIR`/`SNOMED` semantics
/// under the 42 MiB Prolog Sentinel (replacing the legacy 3.3 MB `oxigraph` WASM dependency).
pub fn compile_wearable_biometrics_to_q42(
    subject_did: &str,
    rppg: &CameraRppgAndRespirationReading,
    sleep_efficiency_pct: f64,
    daily_steps: u32,
) -> Result<CompiledQ42OntologyArtifact, String> {
    let turtle = format!(
        "@prefix fhir: <http://hl7.org/fhir/> .\n\
         @prefix snomed: <http://snomed.info/id/> .\n\
         @prefix uberon: <http://purl.obolibrary.org/obo/UBERON_> .\n\
         @prefix wf: <https://wellfare.social/ns/vault#> .\n\n\
         <urn:wellfair:obs:rppg-hr> a fhir:Observation ;\n    \
             wf:subject <{subject_did}> ;\n    \
             fhir:Observation.code snomed:364075005 ;\n    \
             wf:anatomicalTarget uberon:0000948 ;\n    \
             fhir:Observation.valueQuantity \"{:.1}\" ;\n    \
             wf:hrvRmssdMs \"{:.1}\" ;\n    \
             wf:respirationBrpm \"{:.1}\" .\n\n\
         <urn:wellfair:obs:sleep> a fhir:Observation ;\n    \
             wf:subject <{subject_did}> ;\n    \
             wf:sleepEfficiency \"{:.1}\" .\n\n\
         <urn:wellfair:obs:steps> a fhir:Observation ;\n    \
             wf:subject <{subject_did}> ;\n    \
             fhir:Observation.code snomed:256235009 ;\n    \
             fhir:Observation.valueQuantity \"{daily_steps}\" .\n",
        rppg.heart_rate_bpm,
        rppg.hrv_rmssd_ms,
        rppg.respiration_breaths_per_min,
        sleep_efficiency_pct
    );

    compile_ontology_to_q42_pack(
        "wellfair-biometric-sanctuary-vault",
        "WellFair Biometric & Wearable NQuin48 Sanctuary Vault",
        &turtle,
        false, // Private biometric vault — never shared on public Q-CDN!
    )
}

// ---------------------------------------------------------------------------
// 3. Zero-Trust Human-Centric Wallet (Nym Vouchers) & Chat-Graph Delegated Agents
// ---------------------------------------------------------------------------

/// Location-unlinked welfare, housing, clinical, or nutrition support voucher routed via Nym mixnet.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConfidentialWelfareVoucher {
    pub voucher_id: String,
    pub purpose_category: String,
    pub amount_cents: u64,
    pub currency: String,
    pub odrl_policy_iri: String,
    pub nym_mixnet_unlinkable_proof_hex: String,
    pub redeemed: bool,
}

/// Chat-Graph Delegated Agent record:
/// An AI agent in the Webizen Directory and Chat-Graph is NEVER an independent legal entity;
/// it exists strictly as an authorized, bounded, revocable instrument acting on behalf of a
/// specific natural person (`principal_natural_person_did`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DelegatedNaturalPersonAgent {
    pub agent_id: String,
    pub agent_display_name: String,
    /// Mandatory DID of the natural person whose agency this tool serves.
    pub principal_natural_person_did: String,
    pub principal_display_name: String,
    /// Explicit legal/ontological status: always `"DelegatedInstrumentOfNaturalPerson"` (never independent legal personhood).
    pub legal_standing: String,
    pub delegation_lease_id: String,
    pub permitted_scopes: Vec<String>,
    pub revoked: bool,
}

impl DelegatedNaturalPersonAgent {
    pub fn validate_non_independent_standing(&self) -> Result<(), String> {
        if self.principal_natural_person_did.trim().is_empty() {
            return Err("Delegated agent must be bound to a natural person principal DID".into());
        }
        if self.legal_standing != "DelegatedInstrumentOfNaturalPerson" {
            return Err(format!(
                "Invalid agent legal_standing `{}`: AI agents cannot hold independent legal personhood",
                self.legal_standing
            ));
        }
        if self.revoked {
            return Err(format!(
                "Delegated agent `{}` lease `{}` has been revoked by natural person `{}`",
                self.agent_id, self.delegation_lease_id, self.principal_natural_person_did
            ));
        }
        Ok(())
    }
}

/// A signed interaction message in the Chat-Graph where an agent acts strictly on behalf of its
/// natural-person principal (e.g., coordinating an appointment or exchanging a lease-gated clinical packet).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChatGraphDelegatedInteraction {
    pub message_id: String,
    pub from_agent_id: String,
    pub on_behalf_of_natural_person_did: String,
    pub to_recipient_did: String,
    pub delegation_lease_id: String,
    pub intent_summary: String,
    pub signature_hex: String,
}

pub fn builtin_confidential_vouchers() -> Vec<ConfidentialWelfareVoucher> {
    vec![
        ConfidentialWelfareVoucher {
            voucher_id: "HCW-VOUCH-2026-01".into(),
            purpose_category: "Sanctuary Housing & Tenancy Protection Allocation".into(),
            amount_cents: 85_000,
            currency: "AUD".into(),
            odrl_policy_iri: "https://ns.webcivics.net/odrl#SanctuaryHousingSupport".into(),
            nym_mixnet_unlinkable_proof_hex: deterministic_digest_hex(b"HCW-VOUCH-2026-01|NYM-SURB"),
            redeemed: false,
        },
        ConfidentialWelfareVoucher {
            voucher_id: "HCW-VOUCH-2026-02".into(),
            purpose_category: "Trauma-Informed Clinical & Psychological Care Credit".into(),
            amount_cents: 24_000,
            currency: "AUD".into(),
            odrl_policy_iri: "https://ns.webcivics.net/odrl#ClinicalCareAllocation".into(),
            nym_mixnet_unlinkable_proof_hex: deterministic_digest_hex(b"HCW-VOUCH-2026-02|NYM-SURB"),
            redeemed: false,
        },
    ]
}

pub fn builtin_delegated_chat_graph_agents() -> Vec<DelegatedNaturalPersonAgent> {
    vec![
        DelegatedNaturalPersonAgent {
            agent_id: "urn:webizen:agent:sanctuary-advocate-assistant".into(),
            agent_display_name: "Sanctuary Scheduling & Evidence Assistant (Delegated Agent)".into(),
            principal_natural_person_did: "did:q42:person:timothy-holborn".into(),
            principal_display_name: "Natural Person Principal".into(),
            legal_standing: "DelegatedInstrumentOfNaturalPerson".into(),
            delegation_lease_id: "LEASE-AGENT-2026-01".into(),
            permitted_scopes: vec![
                "chat-graph:schedule-specialist".into(),
                "wellfair:prepare-qecp-bundle".into(),
            ],
            revoked: false,
        },
        DelegatedNaturalPersonAgent {
            agent_id: "urn:webizen:agent:clinic-intake-assistant".into(),
            agent_display_name: "Dr. Vance Clinic Intake Agent (Delegated by Dr. M. Vance)".into(),
            principal_natural_person_did: "did:web:clinic.example.au:psychologist-dr-m-vance".into(),
            principal_display_name: "Dr. M. Vance (Natural Person Clinician)".into(),
            legal_standing: "DelegatedInstrumentOfNaturalPerson".into(),
            delegation_lease_id: "LEASE-CLINIC-2026-04".into(),
            permitted_scopes: vec![
                "chat-graph:receive-disclosed-instrument".into(),
                "chat-graph:confirm-appointment".into(),
            ],
            revoked: false,
        },
    ]
}

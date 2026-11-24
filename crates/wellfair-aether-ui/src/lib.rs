//! WellFair Aether RSX 8-Stage Desktop, Mobile & Specialist Portal Workbench (`WP-WF-APP6`).
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: CC BY-NC-ND 4.0.

use aether::prelude::*;
use poet_aether_ui::bodies::ontology::{
    ForensicInvestigationStudioBay, OntologyBody, VerifiablePdfPrinterStudioBay,
};
use poet_aether_ui::store::Workbench;
use wellfair_core_q42::biophysical_rppg_telehealth::{
    estimate_chrom_rppg_and_hrv, synthesize_camera_roi_pulsatile_buffer, TelehealthCallProfile,
    TelehealthSessionState,
};
use wellfair_core_q42::civics_au_human_rights_observatory::{
    build_seeded_civics_au_human_rights_observatory,
    mint_zero_identity_verifiable_truthfulness_proof, AustralianCivicsJurisdiction,
    HumanRightsCivicsIssueDomain,
};
use wellfair_core_q42::domain_mail_and_sanctuary_importers::{
    build_seeded_sanctuary_staging_vault, ImportedPayloadSummary, StagingLifecycleState,
    SANCTUARY_UNCATEGORIZED_STAGING_URI,
};
use wellfair_core_q42::evidence_interchange_directory_fiduciary::{
    build_seeded_interchangeable_library_artifact, builtin_australian_jurisdiction_frame,
    builtin_fiduciary_persona_profiles, builtin_negotiated_directory_connections,
    builtin_webcivics_values_credentials,
    evaluate_cross_qap_fiduciary_and_jurisdictional_access, ConnectionInitiationCategory,
    QapAppConsumer,
};
use wellfair_core_q42::household_family_village_vps::{
    build_seeded_family_village_personal_vps,
    build_seeded_machine_onboarding_account_assignments,
};
use wellfair_core_q42::pharmacokinetics_meds_diet_anatomy::{
    builtin_hra_10d_living_organs, builtin_medications, decode_and_lookup_food_barcode,
    simulate_medication_pk_pd_curve,
};
use wellfair_core_q42::sanctuary_duress_n3_shacl_wallet::{
    builtin_confidential_vouchers, builtin_delegated_chat_graph_agents,
    compile_wearable_biometrics_to_q42, evaluate_wellfair_clinical_and_rights_rules,
    SanctuaryDuressVault, SanctuaryUnlockPosture,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WellfairStageTab {
    SanctuaryAndDuressGate,
    TelehealthAndRppgStudio,
    Hra10dAnatomyAndN3Rules,
    PharmacokineticsAndNutrition,
    SemanticInstrumentsAndPdfDossier,
    ChatGraphAndDelegatedAgents,
    CooperativeProjectsAndCommons,
    ConfidentialNymWallet,
    SanctuaryStagingImportersAndQdpMail,
    FiduciaryDirectoryAndCrossQapInterchange,
}

impl WellfairStageTab {
    pub const ALL: [Self; 10] = [
        Self::SanctuaryAndDuressGate,
        Self::TelehealthAndRppgStudio,
        Self::Hra10dAnatomyAndN3Rules,
        Self::PharmacokineticsAndNutrition,
        Self::SemanticInstrumentsAndPdfDossier,
        Self::ChatGraphAndDelegatedAgents,
        Self::CooperativeProjectsAndCommons,
        Self::ConfidentialNymWallet,
        Self::SanctuaryStagingImportersAndQdpMail,
        Self::FiduciaryDirectoryAndCrossQapInterchange,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::SanctuaryAndDuressGate => "1. 🛡️ Sanctuary & Duress Gate",
            Self::TelehealthAndRppgStudio => "2. 📞 Telehealth & Camera rPPG",
            Self::Hra10dAnatomyAndN3Rules => "3. 🫀 10D HRA Anatomy & N3 Rules",
            Self::PharmacokineticsAndNutrition => "4. 💊 RK4 PK/PD Meds & 🥗 Diet",
            Self::SemanticInstrumentsAndPdfDossier => "5. 🩺 Instruments & PDF Dossier",
            Self::ChatGraphAndDelegatedAgents => "6. 💬 Chat-Graph (Delegated Agents)",
            Self::CooperativeProjectsAndCommons => "7. 🤝 Cooperative Grounds",
            Self::ConfidentialNymWallet => "8. 💳 Confidential Nym Wallet",
            Self::SanctuaryStagingImportersAndQdpMail => "9. 📥 Sanctuary Staging Importers & QDP Mail",
            Self::FiduciaryDirectoryAndCrossQapInterchange => "10. 🏛️ Fiduciary Profiles, Values & Cross-Qap",
        }
    }
}

const CARD_STYLE: &str = "background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:12px;display:grid;gap:8px;";
const BADGE_CYAN: &str = "background:#1e293b;color:#38bdf8;border:1px solid #334155;border-radius:4px;padding:2px 7px;font-size:11px;font-family:monospace;";
const BTN_BLUE: &str = "background:#0284c7;color:#ffffff;border:none;border-radius:5px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;";
const BTN_GREEN: &str = "background:#059669;color:#ffffff;border:none;border-radius:5px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;";

#[component]
/// Root Aether RSX component for the Native Desktop, Mobile & WASM WellFair Application.
pub fn WellfairAppWorkbench() -> Element {
    let mut active_tab = use_signal(|| WellfairStageTab::TelehealthAndRppgStudio);
    let mut vault = use_signal(SanctuaryDuressVault::default);
    let mut pin_input = use_signal(|| String::from("4210"));
    let mut call_session = use_signal(TelehealthSessionState::default);
    let mut simulated_bpm = use_signal(|| 68.0_f64);
    let mut barcode_input = use_signal(|| String::from("9300601123452"));
    let mut staging_vault = use_signal(build_seeded_sanctuary_staging_vault);
    let mut civics_obs_state = use_signal(build_seeded_civics_au_human_rights_observatory);
    let mut civics_testimony_draft = use_signal(|| {
        String::from(
            "De-identified constituent statement: 150-day unacknowledged NDIS functional review despite corroborated specialist assessment.",
        )
    });
    let mut civics_status_banner = use_signal(String::new);
    let wb = use_signal(Workbench::new);

    let current_vault = vault();
    let current_call = call_session();
    let current_staging = staging_vault();
    let meds = builtin_medications();
    let pk_curves: Vec<_> = meds
        .iter()
        .map(|m| simulate_medication_pk_pd_curve(m, 24))
        .collect();
    let n3_matches = evaluate_wellfair_clinical_and_rights_rules(
        &current_call.latest_rppg,
        76.0,
        5.8,
        &pk_curves,
        true,
    );

    rsx! {
        div {
            style: "background:#070b14;color:#e2e8f0;min-height:100vh;font-family:'Inter',system-ui,sans-serif;display:flex;flex-direction:column;",
            // Top Header & Security Posture Banner
            header {
                style: "background:#0b1120;border-bottom:1px solid #1e293b;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;",
                div { style: "display:flex;align-items:center;gap:10px;",
                    span { style: "font-size:20px;", "🛡️" }
                    div {
                        strong { style: "color:#38bdf8;font-size:15px;", "Webizen WellFair — Personal Sanctuary, Telehealth rPPG & Human-Rights Protection" }
                        div { style: "color:#94a3b8;font-size:11px;",
                            "Principal: {current_vault.principal_did} · Powered by QualiaDB (.q42 NQuin48), Etalon 10D v2 (HOLO 0x0306) & Aether Native"
                        }
                    }
                }
                div { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;",
                    span {
                        style: match current_vault.posture {
                            SanctuaryUnlockPosture::NormalSanctuaryUnlocked => "background:#064e3b;color:#34d399;border:1px solid #059669;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;",
                            SanctuaryUnlockPosture::DuressDecoyCoverActive => "background:#1e293b;color:#94a3b8;border:1px solid #475569;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;",
                            SanctuaryUnlockPosture::Locked => "background:#450a0a;color:#f87171;border:1px solid #dc2626;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;",
                        },
                        match current_vault.posture {
                            SanctuaryUnlockPosture::NormalSanctuaryUnlocked => "🔓 Sanctuary Vault Active (ML-KEM-1024 + ChaCha20-Poly1305)",
                            SanctuaryUnlockPosture::DuressDecoyCoverActive => "🔒 Cover Mode Active (Online Leases Silently Frozen)",
                            SanctuaryUnlockPosture::Locked => "🔒 Vault Locked",
                        }
                    }
                    span { style: BADGE_CYAN, "♥ rPPG {current_call.latest_rppg.heart_rate_bpm:.1} BPM · HRV {current_call.latest_rppg.hrv_rmssd_ms:.1}ms · Resp {current_call.latest_rppg.respiration_breaths_per_min:.1} BrPM" }
                }
            }

            // 8-Stage Navigation Bar (Desktop & Touch Mobile Responsive)
            nav {
                style: "background:#090d16;border-bottom:1px solid #1e293b;padding:6px 12px;display:flex;gap:6px;flex-wrap:wrap;",
                for tab in WellfairStageTab::ALL {
                    button {
                        r#type: "button",
                        style: if active_tab() == tab {
                            "background:#38bdf8;color:#090d16;border:none;border-radius:5px;padding:6px 10px;font-size:11px;font-weight:700;cursor:pointer;"
                        } else {
                            "background:#111827;color:#cbd5e1;border:1px solid #1e293b;border-radius:5px;padding:6px 10px;font-size:11px;cursor:pointer;"
                        },
                        onclick: move |_| active_tab.set(tab),
                        "{tab.label()}"
                    }
                }
            }

            // Main Stage Content
            main {
                style: "padding:14px;display:grid;gap:14px;flex:1;overflow:auto;",
                match active_tab() {
                    WellfairStageTab::SanctuaryAndDuressGate => rsx! {
                        div { style: CARD_STYLE,
                            strong { style: "color:#38bdf8;font-size:14px;", "🛡️ Dual-PIN Plausible-Deniability Sanctuary Vault (Normal PIN `4210` vs. Duress Decoy PIN `9911`)" }
                            div { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;",
                                input {
                                    r#type: "password",
                                    style: "background:#131c2e;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:6px 10px;font-size:12px;",
                                    value: "{pin_input}",
                                    oninput: move |e| pin_input.set(e.value()),
                                }
                                button {
                                    r#type: "button",
                                    style: BTN_BLUE,
                                    onclick: move |_| {
                                        let mut v = vault();
                                        v.unlock_with_pin(&pin_input());
                                        vault.set(v);
                                    },
                                    "Unlock Vault with PIN"
                                }
                                button {
                                    r#type: "button",
                                    style: "background:#475569;color:#ffffff;border:none;border-radius:5px;padding:6px 10px;font-size:11px;cursor:pointer;",
                                    onclick: move |_| {
                                        pin_input.set("9911".into());
                                        let mut v = vault();
                                        v.unlock_with_pin("9911");
                                        vault.set(v);
                                    },
                                    "Test Duress Decoy PIN (9911)"
                                }
                                button {
                                    r#type: "button",
                                    style: BTN_GREEN,
                                    onclick: move |_| {
                                        pin_input.set("4210".into());
                                        let mut v = vault();
                                        v.unlock_with_pin("4210");
                                        vault.set(v);
                                    },
                                    "Restore Normal Sanctuary PIN (4210)"
                                }
                            }
                            div { style: "display:grid;gap:8px;",
                                for entry in current_vault.visible_entries().iter() {
                                    div {
                                        key: "{entry.entry_id}",
                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                        div { style: "display:flex;justify-content:space-between;align-items:center;",
                                            strong { style: "color:#34d399;font-size:12px;", "[{entry.entry_id}] {entry.epistemic_kind.to_ascii_uppercase()} · {entry.timestamp_iso}" }
                                            span { style: BADGE_CYAN, "{entry.ots_qecp_anchor}" }
                                        }
                                        p { style: "margin:0;color:#e2e8f0;font-size:12px;", "{entry.content}" }
                                        div { style: "color:#64748b;font-size:10px;font-family:monospace;", "QECP Commitment: {entry.commitment_digest_hex}" }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::TelehealthAndRppgStudio => rsx! {
                        div { style: CARD_STYLE,
                            div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                div {
                                    strong { style: "color:#38bdf8;font-size:14px;", "📞 WebRTC + Noise_XX + ML-KEM-1024 Telehealth & Camera rPPG Biophysical Studio" }
                                    div { style: "color:#94a3b8;font-size:11px;",
                                        "Active Call: {current_call.profile.title()} · Specialist: {current_call.remote_specialist_name} ({current_call.remote_specialist_did})"
                                    }
                                }
                                span { style: "background:#064e3b;color:#34d399;border:1px solid #059669;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;",
                                    "✓ {current_call.latest_rppg.quality.label()}"
                                }
                            }

                            // Call Profile Switcher
                            div { style: "display:flex;gap:6px;flex-wrap:wrap;",
                                for prof in TelehealthCallProfile::ALL {
                                    button {
                                        r#type: "button",
                                        style: if current_call.profile == prof { BTN_BLUE } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.profile = prof;
                                            call_session.set(c);
                                        },
                                        "{prof.title()}"
                                    }
                                }
                            }

                            // Live Camera rPPG, HRV, Thoracic Respiration & Vocal Prosody Cards
                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;",
                                div { style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;",
                                    div { style: "color:#94a3b8;font-size:10px;text-transform:uppercase;", "Chrominance/POS Camera rPPG Pulse" }
                                    strong { style: "color:#38bdf8;font-size:20px;font-family:monospace;", "♥ {current_call.latest_rppg.heart_rate_bpm:.1} BPM" }
                                    div { style: "color:#34d399;font-size:11px;", "SNR: {current_call.latest_rppg.spectral_snr:.2} · PAD Liveness: {current_call.latest_rppg.liveness_pad_score * 100.0:.0}%" }
                                }
                                div { style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;",
                                    div { style: "color:#94a3b8;font-size:10px;text-transform:uppercase;", "Vagal HRV & Autonomic Balance" }
                                    strong { style: "color:#a78bfa;font-size:20px;font-family:monospace;", "RMSSD {current_call.latest_rppg.hrv_rmssd_ms:.1} ms" }
                                    div { style: "color:#cbd5e1;font-size:11px;", "SDNN: {current_call.latest_rppg.hrv_sdnn_ms:.1} ms · LF/HF: {current_call.latest_rppg.lf_hf_autonomic_ratio:.2}" }
                                }
                                div { style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;",
                                    div { style: "color:#94a3b8;font-size:10px;text-transform:uppercase;", "Thoracic Phase-Flow Respiration" }
                                    strong { style: "color:#34d399;font-size:20px;font-family:monospace;", "🫁 {current_call.latest_rppg.respiration_breaths_per_min:.1} BrPM" }
                                    div { style: "color:#cbd5e1;font-size:11px;", "0.15–0.50 Hz Optical Thoracic Envelope" }
                                }
                                div { style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;",
                                    div { style: "color:#94a3b8;font-size:10px;text-transform:uppercase;", "Vocal Formant & Prosody (qualia-audio)" }
                                    strong { style: "color:#fbbf24;font-size:20px;font-family:monospace;", "🎵 {current_call.latest_prosody.f0_pitch_hz:.0} Hz" }
                                    div { style: "color:#cbd5e1;font-size:11px;", "Jitter {current_call.latest_prosody.jitter_pct:.2}% · {current_call.latest_prosody.vocal_stress_indicator}" }
                                }
                            }

                            // Per-Modality Opt-In Consent Gate & DataChannel Packet Emitter
                            div { style: "background:#111827;border:1px solid #334155;border-radius:6px;padding:10px;display:grid;gap:8px;",
                                strong { style: "color:#38bdf8;font-size:12px;",
                                    "🔒 Granular Per-Modality Telemetry Sharing Consent (Raw video/audio NEVER leave device; default = ALL OFF)"
                                }
                                div { style: "display:flex;gap:8px;flex-wrap:wrap;",
                                    button {
                                        r#type: "button",
                                        style: if current_call.consent.share_rppg_pulse_bpm { BTN_GREEN } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.consent.share_rppg_pulse_bpm = !c.consent.share_rppg_pulse_bpm;
                                            call_session.set(c);
                                        },
                                        if current_call.consent.share_rppg_pulse_bpm { "✓ Share ♥ Pulse BPM: ON" } else { "Share ♥ Pulse BPM: OFF" }
                                    }
                                    button {
                                        r#type: "button",
                                        style: if current_call.consent.share_hrv_and_respiration { BTN_GREEN } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.consent.share_hrv_and_respiration = !c.consent.share_hrv_and_respiration;
                                            call_session.set(c);
                                        },
                                        if current_call.consent.share_hrv_and_respiration { "✓ Share HRV & Respiration: ON" } else { "Share HRV & Respiration: OFF" }
                                    }
                                    button {
                                        r#type: "button",
                                        style: if current_call.consent.share_liveness_pad_attestation { BTN_GREEN } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.consent.share_liveness_pad_attestation = !c.consent.share_liveness_pad_attestation;
                                            call_session.set(c);
                                        },
                                        if current_call.consent.share_liveness_pad_attestation { "✓ Share PAD Liveness Proof: ON" } else { "Share PAD Liveness Proof: OFF" }
                                    }
                                    button {
                                        r#type: "button",
                                        style: if current_call.consent.share_voice_prosody { BTN_GREEN } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.consent.share_voice_prosody = !c.consent.share_voice_prosody;
                                            call_session.set(c);
                                        },
                                        if current_call.consent.share_voice_prosody { "✓ Share 🎵 Voice Prosody: ON" } else { "Share 🎵 Voice Prosody: OFF" }
                                    }
                                    button {
                                        r#type: "button",
                                        style: if current_call.consent.record_cml_rdfa_transcript { BTN_GREEN } else { BADGE_CYAN },
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            c.consent.record_cml_rdfa_transcript = !c.consent.record_cml_rdfa_transcript;
                                            call_session.set(c);
                                        },
                                        if current_call.consent.record_cml_rdfa_transcript { "✓ Log CML/RDFa Transcript: ON" } else { "Log CML/RDFa Transcript: OFF" }
                                    }
                                    button {
                                        r#type: "button",
                                        style: BTN_BLUE,
                                        onclick: move |_| {
                                            let mut c = call_session();
                                            let next_bpm = if simulated_bpm() >= 84.0 { 66.0 } else { simulated_bpm() + 4.0 };
                                            simulated_bpm.set(next_bpm);
                                            let samples = synthesize_camera_roi_pulsatile_buffer(next_bpm, 15.0, 30.0, 256);
                                            c.latest_rppg = estimate_chrom_rppg_and_hrv(&samples, 30.0, 0.02);
                                            c.emit_consented_telemetry_frame("2026-11-24T16:15:00Z");
                                            call_session.set(c);
                                        },
                                        "📡 Sample Camera rPPG & Transmit Consented Noise_XX Frame"
                                    }
                                }

                                div { style: "background:#090d16;border:1px solid #1e293b;border-radius:4px;padding:8px;max-height:150px;overflow:auto;font-family:monospace;font-size:11px;color:#34d399;",
                                    for line in current_call.cml_rdfa_transcript_entries.iter() {
                                        div { "{line}" }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::Hra10dAnatomyAndN3Rules => rsx! {
                        div { style: CARD_STYLE,
                            strong { style: "color:#38bdf8;font-size:14px;", "🫀 7-Layer (L0–L6) Holographic 10D v2 (HOLO 0x0306) HRA Living Anatomy & 7 N3 Clinical Rules" }
                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;",
                                for org in builtin_hra_10d_living_organs().iter() {
                                    div {
                                        key: "{org.organ_id}",
                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                        strong { style: "color:#38bdf8;font-size:12px;", "{org.title}" }
                                        div { style: "color:#34d399;font-size:10px;font-family:monospace;", "{org.uberon_iri} · Cavity SDF φ = {org.cavity_sdf_phi}" }
                                        div { style: "color:#cbd5e1;font-size:11px;", "Cells: {org.cell_types_cl.join(\", \")}" }
                                        div { style: "color:#a78bfa;font-size:11px;", "Biomarkers: {org.biomarkers_hgnc.join(\", \")}" }
                                        div { style: "color:#fbbf24;font-size:10px;", "{org.l6_quantum_chemistry_note}" }
                                    }
                                }
                            }
                            strong { style: "color:#a78bfa;font-size:13px;margin-top:6px;", "⚖️ Triggered N3Logic Clinical, Autonomic & Trauma-Cascade Rules ({n3_matches.len()} active):" }
                            div { style: "display:grid;gap:6px;",
                                for m in n3_matches.iter() {
                                    div {
                                        key: "{m.rule_id}",
                                        style: "background:#111827;border-left:3px solid #38bdf8;padding:8px 10px;border-radius:4px;display:grid;gap:2px;",
                                        div { style: "display:flex;justify-content:space-between;align-items:center;",
                                            strong { style: "color:#e2e8f0;font-size:12px;", "[{m.rule_id}] {m.pattern_title}" }
                                            span { style: BADGE_CYAN, "{m.confidence} · {m.n3_source_file}" }
                                        }
                                        div { style: "color:#34d399;font-size:11px;", "Action: {m.recommended_action}" }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::PharmacokineticsAndNutrition => rsx! {
                        div { style: CARD_STYLE,
                            strong { style: "color:#38bdf8;font-size:14px;", "💊 RK4 Pharmacokinetic (PK/PD) ODE Plasma Concentration Curves & 🥗 Nym Barcode Nutrition" }
                            div { style: "display:grid;gap:8px;",
                                for (med, curve) in meds.iter().zip(pk_curves.iter()) {
                                    div {
                                        key: "{med.med_id}",
                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                        div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;",
                                            strong { style: "color:#38bdf8;font-size:13px;", "{med.name} ({med.rxcui} · ATC {med.atc_code})" }
                                            span { style: "color:#34d399;font-family:monospace;font-size:11px;",
                                                "Peak Cmax: {curve.peak_cmax_mg_per_l:.3} mg/L @ {curve.peak_tmax_hours:.1}h · Trough: {curve.trough_cmin_mg_per_l:.3} mg/L"
                                            }
                                        }
                                        div { style: "color:#cbd5e1;font-size:11px;", "{curve.clinical_advisory}" }
                                    }
                                }
                            }
                            div { style: "border-top:1px solid #1e293b;padding-top:10px;display:grid;gap:8px;",
                                strong { style: "color:#34d399;font-size:13px;", "🥗 Nym-Routed Camera Barcode Nutrition & PK Interaction Scanner" }
                                div { style: "display:flex;gap:8px;align-items:center;",
                                    input {
                                        r#type: "text",
                                        style: "background:#131c2e;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:5px 8px;font-size:12px;",
                                        value: "{barcode_input}",
                                        oninput: move |e| barcode_input.set(e.value()),
                                    }
                                }
                                {
                                    let food = decode_and_lookup_food_barcode(&barcode_input(), "breakfast", true);
                                    rsx! {
                                        div { style: "background:#111827;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                            strong { style: "color:#38bdf8;font-size:12px;", "{food.product_name} ({food.brand}) — Barcode {food.barcode_ean13}" }
                                            div { style: "color:#34d399;font-size:11px;font-family:monospace;",
                                                "{food.kcal} kcal · Protein {food.protein_g}g · Carbs {food.carbs_g}g · Fat {food.fat_g}g · Fiber {food.fiber_g}g · FoodOn: {food.foodon_category_iri}"
                                            }
                                            div { style: "color:#a78bfa;font-size:11px;", "PK/PD Interaction Check: {food.pk_interaction_note} · Nym Mixnet Routed: {food.routed_via_nym_mixnet}" }
                                        }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::SemanticInstrumentsAndPdfDossier => rsx! {
                        div { style: "display:grid;gap:12px;",
                            ForensicInvestigationStudioBay { wb }
                            VerifiablePdfPrinterStudioBay {}
                        }
                    },

                    WellfairStageTab::ChatGraphAndDelegatedAgents => rsx! {
                        div { style: CARD_STYLE,
                            strong { style: "color:#38bdf8;font-size:14px;", "💬 Chat-Graph & Verified Directory — Delegated Agents of Natural Persons" }
                            p { style: "margin:0;color:#94a3b8;font-size:12px;",
                                "In Webizen & QualiaDB, AI agents are NEVER independent legal entities; every agent in the Chat-Graph acts strictly as a bounded, revocable instrument delegated by an identified natural person."
                            }
                            div { style: "display:grid;gap:8px;",
                                for ag in builtin_delegated_chat_graph_agents().iter() {
                                    div {
                                        key: "{ag.agent_id}",
                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                        div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;",
                                            strong { style: "color:#38bdf8;font-size:12px;", "🤖 {ag.agent_display_name}" }
                                            span { style: "background:#064e3b;color:#34d399;border:1px solid #059669;border-radius:4px;padding:2px 6px;font-size:10px;font-family:monospace;",
                                                "Standing: {ag.legal_standing}"
                                            }
                                        }
                                        div { style: "color:#e2e8f0;font-size:11px;",
                                            "Principal Natural Person: {ag.principal_display_name} ({ag.principal_natural_person_did}) · Lease: {ag.delegation_lease_id}"
                                        }
                                        div { style: "color:#a78bfa;font-size:11px;font-family:monospace;",
                                            "Permitted Scopes: {ag.permitted_scopes.join(\", \")}"
                                        }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::CooperativeProjectsAndCommons => rsx! {
                        OntologyBody {}
                    },

                    WellfairStageTab::ConfidentialNymWallet => rsx! {
                        div { style: CARD_STYLE,
                            strong { style: "color:#38bdf8;font-size:14px;", "💳 Zero-Trust Human-Centric Wallet & Location-Unlinked Nym Welfare Vouchers" }
                            div { style: "display:grid;gap:8px;",
                                for v in builtin_confidential_vouchers().iter() {
                                    div {
                                        key: "{v.voucher_id}",
                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                        div {
                                            strong { style: "color:#34d399;font-size:13px;", "[{v.voucher_id}] {v.purpose_category}" }
                                            div { style: "color:#94a3b8;font-size:11px;font-family:monospace;",
                                                "ODRL Policy: {v.odrl_policy_iri} · Nym SURB Proof: {&v.nym_mixnet_unlinkable_proof_hex[..20]}…"
                                            }
                                        }
                                        strong { style: "color:#38bdf8;font-size:15px;font-family:monospace;",
                                            "{v.amount_cents as f64 / 100.0:.2} {v.currency}"
                                        }
                                    }
                                }
                            }
                            {
                                let q42_status = compile_wearable_biometrics_to_q42(
                                    &current_vault.principal_did,
                                    &current_call.latest_rppg,
                                    78.0,
                                    6500,
                                );
                                match q42_status {
                                    Ok(art) => rsx! {
                                        div { style: "background:#090d16;border:1px solid #1e293b;border-radius:4px;padding:8px;color:#34d399;font-family:monospace;font-size:11px;",
                                            "✓ Sealed Biometric Sanctuary .q42 Vault ({art.magic_header} v{art.format_version} · {art.nquin48_triple_count} NQuin48 quads · Digest {&art.content_digest_hex[..20]}…)"
                                        }
                                    },
                                    Err(e) => rsx! { div { "{e}" } },
                                }
                            }
                        }
                    },

                    WellfairStageTab::SanctuaryStagingImportersAndQdpMail => rsx! {
                        div { style: "display:grid;gap:12px;",
                            // 1. Domain-Based QDP Mail System (draft-webcivics-QDP: Domain as Agent)
                            div { style: CARD_STYLE,
                                strong { style: "color:#38bdf8;font-size:14px;", "🌐 Domain-Based QDP Communications & Rule-Bearing Mail System (draft-webcivics-QDP)" }
                                p { style: "margin:0;color:#94a3b8;font-size:12px;",
                                    "Domains and subdomains act as QDP Agents (_qdp.<domain> DNS TXT + /.well-known/QDP RDF profile), hosting purpose inboxes (frontdoor@, mygov@, junkmail@) and per-relationship pairwise addresses (dr-rostova@alexmercer.me)."
                                }
                                div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px;",
                                    for dom in current_staging.context_domains.iter() {
                                        div {
                                            key: "{dom.domain_name}",
                                            style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                            div { style: "display:flex;justify-content:space-between;align-items:center;",
                                                strong { style: "color:#38bdf8;font-size:13px;", "{dom.domain_name} ({dom.context_label})" }
                                                span { style: BADGE_CYAN, "{dom.agent_type.rdf_class()}" }
                                            }
                                            div { style: "color:#34d399;font-size:10px;font-family:monospace;",
                                                "DNS TXT {dom.qdp_dns_record_name()} → {dom.to_qdp_dns_txt()}"
                                            }
                                        }
                                    }
                                }
                                div { style: "display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;",
                                    for mb in current_staging.domain_mailboxes.iter() {
                                        span {
                                            key: "{mb.full_address}",
                                            style: "background:#111827;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:3px 8px;font-size:11px;font-family:monospace;",
                                            "✉️ {mb.full_address} [{mb.kind:?} · VerifiedOnly:{mb.rules.require_verified_sender_did}]"
                                        }
                                    }
                                }
                            }

                            // 2. Sanctuary Uncategorized Intake Staging Area (sanctuary://intake/uncategorized)
                            div { style: CARD_STYLE,
                                div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                    div {
                                        strong { style: "color:#fbbf24;font-size:14px;", "📥 Sanctuary Uncategorized Intake Staging Quarantine ({SANCTUARY_UNCATEGORIZED_STAGING_URI})" }
                                        div { style: "color:#94a3b8;font-size:11px;",
                                            "All imports from Mail/Gmail (.mbox/.eml), Google Maps Location History, Samsung Galaxy Watch, and PDFs land here in quarantine — isolated from external leases and AI agents until formally categorized."
                                        }
                                    }
                                    span { style: BADGE_CYAN,
                                        "Uncategorized Quarantine: {current_staging.uncategorized_count()} · Formally Categorized & Promoted: {current_staging.categorized_promoted_count()} ({current_staging.promoted_quins.len()} NQuin48s)"
                                    }
                                }

                                div { style: "display:grid;gap:8px;",
                                    for item in current_staging.staged_items.iter() {
                                        {
                                            let stg_id = item.staging_id.clone();
                                            let hint_cat = item.suggested_category_hint;
                                            let principal_did = current_staging.owner_natural_person_did.clone();
                                            let is_quarantined = item.lifecycle_state == StagingLifecycleState::QuarantinedUncategorized;
                                            rsx! {
                                                div {
                                                    key: "{item.staging_id}",
                                                    style: if is_quarantined {
                                                        "background:#131c2e;border-left:4px solid #fbbf24;border-radius:6px;padding:10px;display:grid;gap:6px;"
                                                    } else {
                                                        "background:#09191f;border-left:4px solid #34d399;border-radius:6px;padding:10px;display:grid;gap:6px;"
                                                    },
                                                    div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                                        strong { style: "color:#38bdf8;font-size:12px;", "[{item.staging_id}] {item.source_kind.label()}" }
                                                        span {
                                                            style: if is_quarantined {
                                                                "background:#451a03;color:#fbbf24;border:1px solid #d97706;border-radius:4px;padding:2px 7px;font-size:10px;font-family:monospace;"
                                                            } else {
                                                                "background:#064e3b;color:#34d399;border:1px solid #059669;border-radius:4px;padding:2px 7px;font-size:10px;font-family:monospace;"
                                                            },
                                                            if is_quarantined {
                                                                "🔒 QuarantinedUncategorized (Isolated in {item.staging_area_uri})"
                                                            } else {
                                                                "✓ FormallyCategorizedAndPromoted → {item.promoted_target_vault_uri.as_deref().unwrap_or(\"\")} ({item.promoted_nquin48_count} NQuin48)"
                                                            }
                                                        }
                                                    }

                                                    match &item.payload {
                                                        ImportedPayloadSummary::MailMessage {
                                                            source_account_id,
                                                            from_address,
                                                            resolved_domain_mailbox,
                                                            subject,
                                                            body_preview,
                                                            gmail_labels,
                                                            ..
                                                        } => rsx! {
                                                            div { style: "color:#e2e8f0;font-size:11px;",
                                                                "✉️ Subject: {subject} · From: {from_address} → Domain Mailbox: {resolved_domain_mailbox} ({source_account_id})"
                                                            }
                                                            div { style: "color:#94a3b8;font-size:11px;", "Labels: [{gmail_labels.join(\", \")}] · Preview: {body_preview}" }
                                                        },
                                                        ImportedPayloadSummary::GoogleMapsLocationBatch {
                                                            visit_count,
                                                            raw_point_count,
                                                            notable_places,
                                                            earliest_timestamp,
                                                            latest_timestamp,
                                                            ..
                                                        } => rsx! {
                                                            div { style: "color:#e2e8f0;font-size:11px;",
                                                                "🗺️ Google Maps Timeline: {visit_count} Place Visits · {raw_point_count} GPS E7 Points ({earliest_timestamp} → {latest_timestamp})"
                                                            }
                                                            div { style: "color:#34d399;font-size:11px;", "Visited Places: {notable_places.join(\" · \")}" }
                                                        },
                                                        ImportedPayloadSummary::SamsungWatchBiometricsBatch {
                                                            device_model,
                                                            sample_count,
                                                            mean_hr_bpm,
                                                            mean_hrv_rmssd_ms,
                                                            min_spo2_percent,
                                                            total_sleep_minutes,
                                                            total_steps,
                                                        } => rsx! {
                                                            div { style: "color:#e2e8f0;font-size:11px;",
                                                                "⌚ {device_model} ({sample_count} days): Mean HR {mean_hr_bpm:.1} BPM · HRV RMSSD {mean_hrv_rmssd_ms:.1} ms · Min SpO2 {min_spo2_percent:.1}% · Sleep {total_sleep_minutes}m · Steps {total_steps}"
                                                            }
                                                        },
                                                        ImportedPayloadSummary::PdfDocumentExtract {
                                                            filename,
                                                            pdf_version,
                                                            page_estimate,
                                                            extracted_title,
                                                            extracted_text_preview,
                                                            has_embedded_qecp_or_pades_signature,
                                                        } => rsx! {
                                                            div { style: "color:#e2e8f0;font-size:11px;",
                                                                "📄 {filename} ({pdf_version} · {page_estimate}p · QECP/PAdES Verified: {has_embedded_qecp_or_pades_signature}): {extracted_title}"
                                                            }
                                                            div { style: "color:#94a3b8;font-size:11px;", "{extracted_text_preview}" }
                                                        },
                                                    }

                                                    if is_quarantined {
                                                        div { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;",
                                                            button {
                                                                r#type: "button",
                                                                style: BTN_GREEN,
                                                                onclick: move |_| {
                                                                    let mut next = staging_vault();
                                                                    let _ = next.formally_categorize_and_promote(
                                                                        &stg_id,
                                                                        hint_cat,
                                                                        &principal_did,
                                                                        Some("AGR-SANCTUARY-INTAKE-2026".to_string()),
                                                                        "Formally categorized and promoted from Sanctuary Staging Area.",
                                                                    );
                                                                    staging_vault.set(next);
                                                                },
                                                                "✓ Formally Categorize & Promote → {hint_cat.label()}"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },

                    WellfairStageTab::FiduciaryDirectoryAndCrossQapInterchange => {
                        let artifact = build_seeded_interchangeable_library_artifact();
                        let vcs = builtin_webcivics_values_credentials();
                        let conns = builtin_negotiated_directory_connections();
                        let profiles = builtin_fiduciary_persona_profiles();
                        let jur = builtin_australian_jurisdiction_frame();
                        rsx! {
                            div { style: "display:grid;gap:12px;",
                                // 1. Enhanced Digital Evidence Informatics & Universal Cross-Qap File Interchange
                                div { style: CARD_STYLE,
                                    div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                        div {
                                            strong { style: "color:#38bdf8;font-size:14px;", "🗂️ Universal Cross-Qap File Interchange & Evidence Act Informatics ({artifact.canonical_library_uri})" }
                                            div { style: "color:#94a3b8;font-size:11px;",
                                                "{artifact.title} · Persistence: {artifact.spc_persistence_class.iri()} · Sticky No-Publish Travels With Artifact: {artifact.travels_with_artifact_no_publish_prohibition}"
                                            }
                                        }
                                        span { style: BADGE_CYAN,
                                            "Digest: {&artifact.evidence_informatics.content_digest_hex[..18]}… · Created @ {artifact.evidence_informatics.timestamps.original_created_at_unix}"
                                        }
                                    }
                                    div { style: "display:flex;gap:6px;flex-wrap:wrap;",
                                        for sec in artifact.evidence_informatics.applicable_statutory_sections.iter() {
                                            span {
                                                style: "background:#064e3b;color:#34d399;border:1px solid #059669;border-radius:4px;padding:2px 7px;font-size:10px;font-family:monospace;",
                                                "⚖️ {sec.citation()}"
                                            }
                                        }
                                    }
                                    div { style: "display:flex;gap:6px;flex-wrap:wrap;",
                                        for app in QapAppConsumer::ALL {
                                            span {
                                                style: "background:#111827;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:3px 8px;font-size:11px;",
                                                "✓ Interchangeable in: {app.label()}"
                                            }
                                        }
                                    }
                                }

                                // 2. Two-Category Active-Directory Social Connection Ceremonies & ns.webcivics.net Values Credentials
                                div { style: CARD_STYLE,
                                    strong { style: "color:#38bdf8;font-size:14px;", "🤝 Two-Category Active-Directory Connection Ceremonies & ns.webcivics.net Values Credentials" }
                                    p { style: "margin:0;color:#94a3b8;font-size:12px;",
                                        "Category A (StrangerZeroPriorHistory) discovers via QDP front-door; Category B (ClaimedPriorConnection) corroborates against imported Sanctuary mail/location data. Both negotiate Values Credentials (values:HumanOnly) before connection establishment."
                                    }
                                    div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px;",
                                        for c in conns.iter() {
                                            div {
                                                key: "{c.connection_id}",
                                                style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                div { style: "display:flex;justify-content:space-between;align-items:center;",
                                                    strong { style: "color:#34d399;font-size:12px;", "[{c.connection_id}] {c.responder_did}" }
                                                    span { style: BADGE_CYAN, "{c.state:?} · {c.governing_jurisdiction_iso}" }
                                                }
                                                div { style: "color:#e2e8f0;font-size:11px;",
                                                    match &c.initiation_category {
                                                        ConnectionInitiationCategory::StrangerZeroPriorHistory { discovery_mechanism } => format!("Category A (Stranger / Zero Prior History): {}", discovery_mechanism),
                                                        ConnectionInitiationCategory::ClaimedPriorConnection { claimed_context_summary, verified_against_sanctuary_data, .. } => format!("Category B (Claimed Prior Connection · Verified={}): {}", verified_against_sanctuary_data, claimed_context_summary),
                                                    }
                                                }
                                                div { style: "color:#a78bfa;font-size:10px;font-family:monospace;",
                                                    "Bound Projects: [{c.bound_project_ids.join(\", \")}] · Groups: [{c.bound_group_categories.join(\", \")}]"
                                                }
                                            }
                                        }
                                    }
                                    div { style: "display:grid;gap:6px;margin-top:4px;",
                                        for vc in vcs.iter() {
                                            div {
                                                key: "{vc.credential_iri}",
                                                style: "background:#111827;border-left:3px solid #38bdf8;padding:8px 10px;border-radius:4px;",
                                                strong { style: "color:#38bdf8;font-size:12px;", "📜 {vc.title} (PersonReading: {vc.person_reading:?})" }
                                                div { style: "color:#94a3b8;font-size:10px;font-family:monospace;", "{vc.credential_iri} · {vc.undertakings.len()} Deontic Undertakings" }
                                            }
                                        }
                                    }
                                }

                                // 3. Fiduciary & Professional Persona Profiles, Qualifications & Jurisdiction-Aware Permissions
                                div { style: CARD_STYLE,
                                    strong { style: "color:#38bdf8;font-size:14px;", "🏛️ Fiduciary & Professional Persona Profiles, Qualifications & Jurisdictional Permission Matrix ({jur.jurisdiction_iso})" }
                                    div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px;",
                                        for prof in profiles.iter() {
                                            {
                                                let decision = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
                                                    &artifact,
                                                    QapAppConsumer::PoetHyperCanvas,
                                                    prof,
                                                    &conns[0],
                                                    &jur,
                                                    true,
                                                    1_763_965_000,
                                                );
                                                let qual = &prof.qualifications[0];
                                                rsx! {
                                                    div {
                                                        key: "{prof.natural_person_did}",
                                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;",
                                                            strong { style: "color:#38bdf8;font-size:12px;", "{prof.display_name}" }
                                                            span { style: BADGE_CYAN, "{prof.active_persona_context:?}" }
                                                        }
                                                        div { style: "color:#e2e8f0;font-size:11px;",
                                                            "Sector: {qual.sector.label()} · Reg: {qual.registration_or_certificate_number} ({qual.issuing_authority_or_register})"
                                                        }
                                                        div { style: "color:#94a3b8;font-size:10px;font-family:monospace;",
                                                            "Personal QDP: {prof.personal_qdp_domain} | Professional QDP: {prof.professional_qdp_domain.as_deref().unwrap_or(\"N/A\")} | Jurisdictions: [{qual.recognized_jurisdictions_iso.join(\", \")}]"
                                                        }
                                                        div { style: "color:#34d399;font-size:11px;",
                                                            "✓ Access Decision: {decision.reason} (Multi-Sig Instigation Required: {decision.requires_multi_sig_party_instigation})"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // 4. Multi-Person Family, Household & Village Small-Business Personal VPS (webizen-host)
                                {
                                    let vps = build_seeded_family_village_personal_vps();
                                    rsx! {
                                        div { style: CARD_STYLE,
                                            div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                                div {
                                                    strong { style: "color:#38bdf8;font-size:14px;", "🏡 Family, Household & Village Small-Business Personal VPS ({vps.homestead_root_domain})" }
                                                    div { style: "color:#94a3b8;font-size:11px;",
                                                        "Topology: {vps.topology.label()} · Local Homestead: {vps.local_sanctuary_bind} · Online Relay: {vps.online_relay_bind.as_deref().unwrap_or(\"N/A\")}"
                                                    }
                                                }
                                                span { style: BADGE_CYAN, "{vps.seats.len()} Family Seats · {vps.family_works.len()} Village Craft/Clinical Works · {vps.school_bridges.len()} Child-School Bridges" }
                                            }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;",
                                                for work in vps.family_works.iter() {
                                                    div {
                                                        key: "{work.work_id}",
                                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#34d399;font-size:12px;", "⚒️ {work.title} ({work.shopfront_subdomain})" }
                                                        div { style: "color:#e2e8f0;font-size:11px;", "{work.craft_archetype} · Owner: {work.owner_principal_did}" }
                                                        div { style: "color:#a78bfa;font-size:10px;font-family:monospace;", "Hosted Qaps: [{work.hosted_qap_ids.join(\", \")}] · Compartment Isolated: {work.isolated_from_other_family_works}" }
                                                    }
                                                }
                                            }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;",
                                                for bridge in vps.school_bridges.iter() {
                                                    div {
                                                        key: "{bridge.bridge_id}",
                                                        style: "background:#111827;border-left:3px solid #38bdf8;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#38bdf8;font-size:12px;", "🎓 {bridge.child_display_name} — {bridge.child_school_subdomain} ↔ {bridge.school_institution_domain}" }
                                                        div { style: "color:#34d399;font-size:11px;",
                                                            "School: {bridge.school_institution_name} · Guardian Quorum: {bridge.approving_guardian_dids.len()}/{bridge.required_guardian_quorum} · Learning Claims Retained on Family VPS: {bridge.retain_learning_claims_in_family_vps}"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // 5. 7-Screen New-User Onboarding Wizard & Multi-Account Shared-Machine Seat Assignments
                                {
                                    let machine_seats = build_seeded_machine_onboarding_account_assignments();
                                    let onboarding_screens = [
                                        ("Screen 1 · Apparatus & WSL2/Primary OS Probe", "Anvil .np64 GPU/TPM quote + Windows/WSL2 eBPF/nftables/ext4 Bridge vs. Debian 13 Trixie Primary OS"),
                                        ("Screen 2 · Four-Plane Natural-Person Anchor", "Plane 1 NaturalAgent (living-SHACL, disjoint from owl:Thing · OS Account != Identity)"),
                                        ("Screen 3 · 4-Slot VaultContainerV2 & Dual-PIN", "Memory-hard Argon2id (64 MiB) Real Sanctuary Keep vs. Plausible-Deniability Duress Decoy lane"),
                                        ("Screen 4 · Mobile AVF Pocket Co-Signer Pairing", "Android 16 AVF pKVM EL2 arm64 Pocket Co-Signer over WireGuard + vhost-vsock CID 2"),
                                        ("Screen 5 · Multi-Account Machine Seat Assignment", "Assigns isolated ports (:8080..:8083), 42 MiB SlgArena, and vaults for Personal, Fiduciary, Child & Agent seats"),
                                        ("Screen 6 · Always-On Persistence Mesh & ABN/VPS", "Mac Mini :8080 / Cloud VPS :4242 store-and-forward + ATO Mod-89 ABN + 2-of-4 Shamir .q42j Guardians"),
                                        ("Screen 7 · Progressive Noisy-OR Confidence (< 1.0)", "Combines 5 attested identifiers -> Noisy-OR C_agg = 0.997 (< 1.0) -> Tier 3 High-Assurance Activation"),
                                    ];
                                    rsx! {
                                        div { style: CARD_STYLE,
                                            strong { style: "color:#38bdf8;font-size:14px;", "🧭 7-Screen New-User Onboarding Wizard & Multi-Account Shared-Machine Seat Assignments" }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:6px;",
                                                for (title, desc) in onboarding_screens.iter() {
                                                    div {
                                                        key: "{title}",
                                                        style: "background:#111827;border:1px solid #334155;border-radius:6px;padding:8px;display:grid;gap:3px;",
                                                        strong { style: "color:#34d399;font-size:11px;", "{title}" }
                                                        div { style: "color:#94a3b8;font-size:10px;", "{desc}" }
                                                    }
                                                }
                                            }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;margin-top:6px;",
                                                for seat in machine_seats.iter() {
                                                    div {
                                                        key: "{seat.seat_id}",
                                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#38bdf8;font-size:12px;", "🪑 {seat.display_name}" }
                                                        div { style: "color:#e2e8f0;font-size:11px;font-family:monospace;",
                                                            "OS Login: '{seat.os_account_username}' · Profile: '{seat.webizen_profile_slug}' · Port :{seat.dedicated_loopback_port} · {seat.isolated_slg_arena_mib} MiB SlgArena"
                                                        }
                                                        div { style: "color:#34d399;font-size:11px;font-family:monospace;",
                                                            "Identifiers: {seat.developed_identifiers.len()} · Noisy-OR Confidence: 0.{seat.aggregate_confidence_permille:03} (< 1.0) · {seat.confidence_tier:?}"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // 6. civics.au — Australian Human-Rights & Civics Statistical Observatory,
                                //    Zero-Identifier Verifiable Testimony & Parliamentary (Civic) Engagement
                                {
                                    let obs = civics_obs_state();
                                    let draft_summary = civics_testimony_draft();
                                    let banner = civics_status_banner();
                                    rsx! {
                                        div { style: CARD_STYLE,
                                            div { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;",
                                                div {
                                                    strong { style: "color:#38bdf8;font-size:14px;", "🇦🇺 civics.au — Australian Human-Rights & Civics Statistical Observatory & Parliamentary Constituent Engagement" }
                                                    div { style: "color:#94a3b8;font-size:11px;",
                                                        "Endpoints: [{obs.observatory_endpoints.join(\", \")}] · k-Anonymity >= 5 · Laplace Differential Privacy · Zero-Who-Leak Verifiable Truthfulness Proofs"
                                                    }
                                                }
                                                span { style: BADGE_CYAN, "{obs.statistical_series.len()} Hosted Statistical Series · {obs.testimonies.len()} Zero-ID Verifiable Testimonies · {obs.parliamentary_engagements.len()} Parliamentary Engagements" }
                                            }
                                            div { style: "background:#111827;border:1px solid #334155;border-radius:6px;padding:10px;display:grid;gap:8px;",
                                                strong { style: "color:#34d399;font-size:12px;", "✍️ Submit Zero-Identifier (Zero-Who-Leak) Verifiable Testimony or Record Parliamentary Engagement" }
                                                div { style: "display:flex;gap:8px;flex-wrap:wrap;align-items:center;",
                                                    input {
                                                        r#type: "text",
                                                        style: "flex:1;min-width:260px;background:#131c2e;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:6px 10px;font-size:12px;",
                                                        value: "{draft_summary}",
                                                        oninput: move |e| civics_testimony_draft.set(e.value()),
                                                    }
                                                    button {
                                                        r#type: "button",
                                                        style: BTN_GREEN,
                                                        onclick: move |_| {
                                                            let mut next_obs = civics_obs_state();
                                                            let seed = format!("sanctuary_seed_live_{}", next_obs.testimonies.len() + 1);
                                                            match mint_zero_identity_verifiable_truthfulness_proof(
                                                                &seed,
                                                                HumanRightsCivicsIssueDomain::SocialSecurityNdisAndAutomatedWelfareFairness.code(),
                                                                "2026-11",
                                                                AustralianCivicsJurisdiction::Victoria,
                                                                "Melbourne",
                                                                997,
                                                                &[
                                                                    "qar://evidence-act-s69/agency-determination.qar",
                                                                    "qar://evidence-act-s146/specialist-report.qar",
                                                                ],
                                                                &civics_testimony_draft(),
                                                            ) {
                                                                Ok(proof) => {
                                                                    let tid = format!("TESTIMONY-AU-VIC-LIVE-00{}", next_obs.testimonies.len() + 1);
                                                                    match next_obs.submit_anonymised_verifiable_testimony(
                                                                        &tid,
                                                                        AustralianCivicsJurisdiction::Victoria,
                                                                        "Melbourne",
                                                                        "Melbourne Metro",
                                                                        HumanRightsCivicsIssueDomain::SocialSecurityNdisAndAutomatedWelfareFairness,
                                                                        90,
                                                                        150,
                                                                        civics_testimony_draft(),
                                                                        "Enforce statutory human-rights Duty-of-Inquiry review.",
                                                                        proof.clone(),
                                                                        1_764_000_000,
                                                                    ) {
                                                                        Ok(_) => {
                                                                            civics_status_banner.set(format!(
                                                                                "✓ Submitted Zero-ID Verifiable Testimony {} · Nullifier {} · Evidence Act Anchor {}",
                                                                                tid,
                                                                                proof.epoch_issue_nullifier_hex,
                                                                                proof.corroborating_evidence_act_anchor_commitment_hex
                                                                            ));
                                                                            civics_obs_state.set(next_obs);
                                                                        }
                                                                        Err(e) => civics_status_banner.set(format!("✗ Rejected: {e}")),
                                                                    }
                                                                }
                                                                Err(e) => civics_status_banner.set(format!("✗ Rejected by Zero-Identifier / Anti-False-Statement Gate: {e}")),
                                                            }
                                                        },
                                                        "🛡️ Mint Zero-ID Proof & Submit to civics.au"
                                                    }
                                                }
                                                if !banner.is_empty() {
                                                    div { style: "color:#38bdf8;font-size:11px;font-family:monospace;", "{banner}" }
                                                }
                                            }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px;",
                                                for s in obs.statistical_series.iter() {
                                                    div {
                                                        key: "{s.series_id}",
                                                        style: "background:#131c2e;border:1px solid #1e293b;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#34d399;font-size:12px;", "📊 [{s.series_id}] {s.issue_domain.title()}" }
                                                        div { style: "color:#e2e8f0;font-size:11px;",
                                                            "Jurisdiction: {s.jurisdiction.iso_code()} ({s.electorate_or_region_scope}) · Unique Verified Constituents: {s.verified_unique_constituent_count} (k-Anonymity >= 5: {s.k_anonymity_threshold_satisfied})"
                                                        }
                                                        div { style: "color:#38bdf8;font-size:11px;font-family:monospace;",
                                                            "Mean Impact Severity: {s.published_mean_severity_score:?}/100 · Median Unresolved Delay: {s.published_median_unresolved_days:?} days · Evidence Act Backed: {s.corroborated_evidence_act_backing_pct:?}%"
                                                        }
                                                        div { style: "color:#cbd5e1;font-size:11px;",
                                                            "Top Constituent Remedy Consensus: {s.top_constituent_remedy_consensus}"
                                                        }
                                                    }
                                                }
                                            }
                                            strong { style: "color:#38bdf8;font-size:13px;margin-top:6px;", "🛡️ Identifier-Free (Zero-Who-Leak) Yet Non-False Verifiable Constituent Testimonies" }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px;",
                                                for t in obs.testimonies.iter() {
                                                    div {
                                                        key: "{t.testimony_id}",
                                                        style: "background:#111827;border-left:3px solid #34d399;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#34d399;font-size:12px;", "[{t.testimony_id}] {t.jurisdiction.iso_code()} · Division of {t.federal_electorate_division} (Severity {t.impact_severity_score}/100 · Delay {t.systemic_delay_or_unresolved_days}d)" }
                                                        div { style: "color:#e2e8f0;font-size:11px;", "{t.deidentified_lived_experience_summary}" }
                                                        div { style: "color:#a78bfa;font-size:10px;font-family:monospace;",
                                                            "Nullifier: {t.truthfulness_proof.epoch_issue_nullifier_hex} · Apparatus Confidence: 0.{t.truthfulness_proof.apparatus_confidence_tier_verified_permille:03} · Evidence Act Artifacts: {t.truthfulness_proof.corroborated_primary_artifact_count} (Anchor {t.truthfulness_proof.corroborating_evidence_act_anchor_commitment_hex})"
                                                        }
                                                    }
                                                }
                                            }
                                            strong { style: "color:#38bdf8;font-size:13px;margin-top:6px;", "🏛️ Parliamentary (Civic) Constituent Engagements & Blind Nullifier Return Receipts" }
                                            div { style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px;",
                                                for p in obs.parliamentary_engagements.iter() {
                                                    div {
                                                        key: "{p.engagement_id}",
                                                        style: "background:#131c2e;border-left:3px solid #fbbf24;border-radius:6px;padding:10px;display:grid;gap:4px;",
                                                        strong { style: "color:#fbbf24;font-size:12px;", "🏛️ {p.parliamentarian_name_and_title} ({p.parliamentary_register_credential_id})" }
                                                        div { style: "color:#e2e8f0;font-size:11px;", "{p.parliamentary_response_and_action_commitment}" }
                                                        div { style: "color:#38bdf8;font-size:10px;font-family:monospace;",
                                                            "{p.hansard_or_committee_reference} · Blind Constituent Receipts: [{p.constituent_nullifier_blind_reply_tokens.join(\", \")}]"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        }
    }
}

//! Webizen WellFair Native Desktop Launcher & Biophysical/Clinical CLI (`WP-WF-APP6`).
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: CC BY-NC-ND 4.0.

use std::env;
use std::fs;
use std::process;
use wellfair_core_q42::biophysical_rppg_telehealth::{
    estimate_chrom_rppg_and_hrv, synthesize_camera_roi_pulsatile_buffer, TelehealthSessionState,
};
use wellfair_core_q42::civics_au_human_rights_observatory::build_seeded_civics_au_human_rights_observatory;
use wellfair_core_q42::domain_mail_and_sanctuary_importers::{
    build_seeded_sanctuary_staging_vault, FormalSanctuaryCategory,
};
use wellfair_core_q42::evidence_interchange_directory_fiduciary::{
    build_seeded_interchangeable_library_artifact, builtin_australian_jurisdiction_frame,
    builtin_fiduciary_persona_profiles, builtin_negotiated_directory_connections,
    evaluate_cross_qap_fiduciary_and_jurisdictional_access, QapAppConsumer,
};
use wellfair_core_q42::evidentiary_cold_archiver_qar::{
    build_seeded_evidentiary_cold_archiver, QarContainerReader,
};
use wellfair_core_q42::household_family_village_vps::{
    build_seeded_australian_abn_vps_nomination, build_seeded_family_village_personal_vps,
    build_seeded_machine_onboarding_account_assignments, build_seeded_multi_device_persistence_mesh,
    build_wsl2_linux_kernel_bridge_profile, instigate_nominated_vps_installation,
    seal_windows_to_webizen_primary_os_migration_capsule, DispatchedPayloadKind,
};
use wellfair_core_q42::pharmacokinetics_meds_diet_anatomy::{
    builtin_medications, simulate_medication_pk_pd_curve,
};
use wellfair_core_q42::qap_container_and_vibe_runtime::{
    build_canonical_wellfair_qap_package, QapContainerReader,
};
use wellfair_core_q42::sanctuary_duress_n3_shacl_wallet::{
    compile_wearable_biometrics_to_q42, evaluate_wellfair_clinical_and_rights_rules,
    SanctuaryDuressVault,
};

fn print_usage() {
    println!("Webizen WellFair Native Application & Biophysical CLI (v0.0.41)");
    println!("Usage:");
    #[cfg(feature = "native-graphical")]
    println!("  wellfair workbench              Launch the native Aether WellFair 8-Stage Application");
    println!("  wellfair rppg-sim <bpm>         Run CHROM/POS radix-2 FFT rPPG, HRV & respiration estimator");
    println!("  wellfair pk-sim                 Run 24h RK4 Pharmacokinetic (PK/PD) ODE solver on medications");
    println!("  wellfair verify-duress <pin>    Verify Dual-PIN Sanctuary vs. Duress Decoy unlock posture");
    println!("  wellfair compile-biometrics <f> Compile wearable & rPPG biometrics into a private .q42 vault");
    println!("  wellfair staging-importers      Verify QDP Domain Mail & 4 Importers into Sanctuary Staging Area");
    println!("  wellfair build-qap <out.qap>    Seal signed wellfair.qap (QAP\\0 v1 + yaml-ld-q42 + live .vibe)");
    println!("  wellfair archive-verify <f.qar> Seal cold .qar (QAR\\0 v1) evidentiary archive & prune hot runtime");
    println!("  wellfair fiduciary-interchange  Verify Evidence Act Informatics, Cross-Qap Interchange, Values Credentials & Jurisdictional Fiduciary Access");
    println!("  wellfair family-vps             Verify Multi-Person Family, Child/School & Village Small-Business Personal VPS (webizen-host)");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        process::exit(1);
    }

    match args[1].as_str() {
        #[cfg(feature = "native-graphical")]
        "workbench" => {
            let attributes = aether_native::WindowAttributes::default()
                .with_title("Webizen WellFair · Sanctuary, Telehealth rPPG, 10D Anatomy & Human-Rights Protection")
                .with_surface_size(aether_native::LogicalSize::new(1520, 920));
            aether_native::launch_cfg(
                wellfair_aether_ui::WellfairAppWorkbench,
                Vec::new(),
                vec![Box::new(attributes)],
            );
        }
        "rppg-sim" => {
            let target_bpm = args
                .get(2)
                .and_then(|s| s.parse::<f64>().ok())
                .unwrap_or(68.0);
            let samples = synthesize_camera_roi_pulsatile_buffer(target_bpm, 14.0, 30.0, 256);
            let r = estimate_chrom_rppg_and_hrv(&samples, 30.0, 0.02);
            println!(
                "rPPG Result: ♥ {:.1} BPM | HRV RMSSD {:.1} ms | SDNN {:.1} ms | Resp {:.1} BrPM | SNR {:.2} | PAD Liveness {:.0}% ({})",
                r.heart_rate_bpm,
                r.hrv_rmssd_ms,
                r.hrv_sdnn_ms,
                r.respiration_breaths_per_min,
                r.spectral_snr,
                r.liveness_pad_score * 100.0,
                r.quality.label()
            );
        }
        "pk-sim" => {
            for med in builtin_medications() {
                let curve = simulate_medication_pk_pd_curve(&med, 24);
                println!("{} -> {}", med.name, curve.clinical_advisory);
            }
        }
        "verify-duress" => {
            let pin = args.get(2).map(|s| s.as_str()).unwrap_or("4210");
            let mut vault = SanctuaryDuressVault::default();
            let posture = vault.unlock_with_pin(pin);
            println!(
                "PIN `{pin}` -> Posture: {posture:?} | Online Leases Frozen: {} | Visible Entries: {}",
                vault.active_specialist_leases_frozen,
                vault.visible_entries().len()
            );
        }
        "compile-biometrics" => {
            let out_path = args.get(2).map(|s| s.as_str()).unwrap_or("biometrics.q42");
            let session = TelehealthSessionState::default();
            let art = compile_wearable_biometrics_to_q42(
                "did:q42:person:timothy-holborn",
                &session.latest_rppg,
                78.0,
                6500,
            )
            .expect("compiles biometrics to .q42");
            fs::write(out_path, &art.binary_payload_bytes).expect("writes .q42 file");
            let curves: Vec<_> = builtin_medications()
                .iter()
                .map(|m| simulate_medication_pk_pd_curve(m, 24))
                .collect();
            let rules = evaluate_wellfair_clinical_and_rights_rules(
                &session.latest_rppg,
                76.0,
                5.8,
                &curves,
                true,
            );
            println!(
                "Sealed {} ({} NQuin48 quads, {} bytes, {} N3 rules evaluated, digest {}) -> {}",
                art.ontology_id,
                art.nquin48_triple_count,
                art.prolog_arena_bytes_used,
                rules.len(),
                art.content_digest_hex,
                out_path
            );
        }
        "staging-importers" => {
            let mut stg = build_seeded_sanctuary_staging_vault();
            println!(
                "QDP Domains: {} ({} -> {}) | Mailboxes: {} | Staged Uncategorized in '{}': {}",
                stg.context_domains.len(),
                stg.context_domains[0].qdp_dns_record_name(),
                stg.context_domains[0].to_qdp_dns_txt(),
                stg.domain_mailboxes.len(),
                wellfair_core_q42::domain_mail_and_sanctuary_importers::SANCTUARY_UNCATEGORIZED_STAGING_URI,
                stg.uncategorized_count()
            );
            let first_id = stg.staged_items[0].staging_id.clone();
            let minted = stg
                .formally_categorize_and_promote(
                    &first_id,
                    FormalSanctuaryCategory::ClinicalAndBiometricSanctuary,
                    "did:webizen:person:alex-mercer",
                    Some("AGR-CLINICAL-CARE-2026".to_string()),
                    "Categorized via CLI verification",
                )
                .expect("categorize and promote");
            println!(
                "Formally categorized '{}' -> Minted {} NQuin48 quads | Remaining Uncategorized: {} | Promoted: {}",
                first_id,
                minted,
                stg.uncategorized_count(),
                stg.categorized_promoted_count()
            );
        }
        "build-qap" => {
            let out_path = args.get(2).map(|s| s.as_str()).unwrap_or("wellfair.qap");
            let mut pkg = build_canonical_wellfair_qap_package();
            fs::write(out_path, &pkg.qap_bytes).expect("writes .qap container");
            let (entry_count, version) = {
                let reader = QapContainerReader::parse(&pkg.qap_bytes).expect("verifies .qap");
                (reader.entries.len(), reader.version)
            };
            let quin = pkg
                .activate_by_natural_person("did:webizen:person:alex-mercer")
                .expect("activates .qap");
            println!(
                "Sealed {} ({} bytes, {} page-aligned entries, magic QAP\\0 v{}, Sentinel NQuin48 parity {}, live .vibe eval OK) -> {}",
                pkg.descriptor.qap_id,
                pkg.qap_bytes.len(),
                entry_count,
                version,
                quin.verify_parity(),
                out_path
            );
        }
        "archive-verify" => {
            let out_path = args.get(2).map(|s| s.as_str()).unwrap_or("wellfair-cold-evidence.qar");
            let (archiver, qar_bytes) = build_seeded_evidentiary_cold_archiver();
            fs::write(out_path, &qar_bytes).expect("writes .qar cold archive");
            let reader = QarContainerReader::parse(&qar_bytes).expect("verifies .qar custody chain");
            let cert = reader
                .recall_historical_version(&reader.entries[0].archive_entry_id)
                .expect("recalls v1.0.0 from cold .qar");
            println!(
                "Sealed Cold Evidentiary Archive ({} bytes, {} historical versions, magic QAR\\0 v{}, Runtime Payload Bytes Freed: {} B, Retained Tombstones: {} NQuin48s, Recalled '{}' Created @ {} Verified: {}) -> {}",
                qar_bytes.len(),
                reader.entries.len(),
                reader.version,
                archiver.runtime_payload_bytes_freed,
                archiver.runtime_tombstone_quins.len(),
                cert.archive_entry.filename,
                cert.archive_entry.timestamps.original_created_at_unix,
                cert.payload_digest_verified && cert.cumulative_chain_verified && cert.timestamps_chronology_verified,
                out_path
            );
        }
        "fiduciary-interchange" => {
            let artifact = build_seeded_interchangeable_library_artifact();
            let conns = builtin_negotiated_directory_connections();
            let profiles = builtin_fiduciary_persona_profiles();
            let jur = builtin_australian_jurisdiction_frame();
            println!(
                "Interchangeable Artifact: {} | Evidence Sections: {} | Permitted Qaps: {} | Connections (Stranger + Prior): {}",
                artifact.canonical_library_uri,
                artifact.evidence_informatics.applicable_statutory_sections.len(),
                artifact.permitted_qap_consumers.len(),
                conns.len()
            );
            for prof in &profiles {
                let decision = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
                    &artifact,
                    QapAppConsumer::PoetHyperCanvas,
                    prof,
                    &conns[0],
                    &jur,
                    true,
                    1_763_965_000,
                );
                println!(
                    "  Fiduciary Persona: {} ({:?}) -> Permitted: {} | Qualification: {:?} | Jurisdiction: {}",
                    prof.display_name,
                    prof.qualifications[0].sector,
                    decision.permitted,
                    decision.matched_qualification_id,
                    decision.evaluated_jurisdiction_iso
                );
            }
        }
        "family-vps" => {
            let vps = build_seeded_family_village_personal_vps();
            println!(
                "Family & Village Personal VPS '{}' ({}) | Topology: {} | Local: {} | Online: {:?}",
                vps.homestead_root_domain,
                vps.vps_node_id,
                vps.topology.label(),
                vps.local_sanctuary_bind,
                vps.online_relay_bind
            );
            for seat in &vps.seats {
                println!(
                    "  Seat [{}] {} -> {} (42 MiB SlgArena, Lane {})",
                    seat.seat_id,
                    seat.display_name,
                    seat.personal_subdomain,
                    seat.sanctuary_lane_fingerprint_hex
                );
            }
            for work in &vps.family_works {
                println!(
                    "  Village Work [{}] {} -> {} | Owner: {} | Co-Stewards: {:?} | Qaps: {:?}",
                    work.work_id,
                    work.title,
                    work.shopfront_subdomain,
                    work.owner_principal_did,
                    work.co_steward_dids,
                    work.hosted_qap_ids
                );
            }
            for bridge in &vps.school_bridges {
                let res = vps.evaluate_child_school_interaction(
                    &bridge.child_did,
                    &bridge.school_institution_domain,
                    false,
                    1_763_999_000,
                );
                println!(
                    "  Child/School Bridge [{}] {} <-> {} ({}) -> {:?}",
                    bridge.bridge_id,
                    bridge.child_school_subdomain,
                    bridge.school_institution_domain,
                    bridge.school_institution_name,
                    res
                );
            }
            let mut mesh = build_seeded_multi_device_persistence_mesh();
            let env = mesh.dispatch_respecting_availability(
                "ENV-SETTLE-01",
                "did:webizen:person:marcus-vance",
                DispatchedPayloadKind::CooperativeProjectClaimOrSettlement,
                "Stage-8 Settlement Co-Sign while laptop is asleep",
                "sha256_settle_01",
                true,
                1_763_999_000,
            );
            let elevated = mesh
                .elevate_permission_on_phone("ENV-SETTLE-01", "ed25519_ml_dsa_87_phone_cosign")
                .expect("phone elevation");
            let hydrated = mesh.wake_workstation_and_drain_spool();
            println!(
                "  Multi-Device Mesh ({} devices: Phone Elevator + Sleeping Laptop + Mac Mini :8080 + Cloud VPS :4242): Spooled at {:?} -> Phone Elevated: {:?} -> Laptop Woke & Hydrated: {} envelope(s)",
                mesh.devices.len(),
                env.target_persistence_node_id,
                elevated,
                hydrated
            );
            let nom = build_seeded_australian_abn_vps_nomination();
            let plan = instigate_nominated_vps_installation(&nom, 1_763_999_000).expect("valid VPS nomination & ABN");
            println!(
                "  Nominated VPS Installation '{}' ({} -> {}) | Trade: {:?} | Auto 10% GST Escrow: {} | Annual Cost-Recovery Target: {} AUD cents | QDP TXT: {}",
                plan.installation_id,
                plan.provider_name,
                plan.target_host_endpoint,
                plan.trade_characterisation,
                plan.auto_gst_escrow_enabled,
                plan.qcdn_cost_recovery_pool_target_cents,
                plan.generated_qdp_dns_txt_record
            );
            let wsl = build_wsl2_linux_kernel_bridge_profile(true);
            let cap = seal_windows_to_webizen_primary_os_migration_capsule(
                "did:webizen:person:alex-mercer",
                wsl.substrate_mode,
                4,
                3,
                2,
                "ed25519_ml_dsa_87_phone_cosign_primary_os_cutover_alex",
                1_763_999_000,
            )
            .expect("primary os migration capsule");
            println!(
                "  WSL2 Bridge ({:?} · eBPF: {} · nftables: {} · ext4 mmap: {}) -> Primary OS Migration Capsule '{}': {} .q42 + {} .qap + {} .qar (Evidence Timestamps Preserved: {})",
                wsl.substrate_mode,
                wsl.ebpf_socket_quota_enforcement_active,
                wsl.nftables_deontic_split_horizon_active,
                wsl.ext4_posix_mmap_vault_active,
                cap.capsule_id,
                cap.preserved_q42_volumes_count,
                cap.preserved_qap_packages_count,
                cap.preserved_qar_evidentiary_archives_count,
                cap.evidentiary_timestamps_preserved_across_os_wipe
            );
            for seat in build_seeded_machine_onboarding_account_assignments() {
                println!(
                    "  Machine Account Seat [{}] OS-User '{}' / Profile '{}' (Port :{}) -> {} | Identifiers: {} | Noisy-OR Confidence: 0.{:03} (< 1.0) | Tier: {:?}",
                    seat.seat_id,
                    seat.os_account_username,
                    seat.webizen_profile_slug,
                    seat.dedicated_loopback_port,
                    seat.display_name,
                    seat.developed_identifiers.len(),
                    seat.aggregate_confidence_permille,
                    seat.confidence_tier
                );
            }
            let obs = build_seeded_civics_au_human_rights_observatory();
            println!(
                "  civics.au Observatory ({:?}) | Series: {} | Zero-ID Verifiable Testimonies: {} | Parliamentary Engagements: {}",
                obs.observatory_endpoints,
                obs.statistical_series.len(),
                obs.testimonies.len(),
                obs.parliamentary_engagements.len()
            );
            for s in &obs.statistical_series {
                println!(
                    "    Stats [{}] {} ({}) -> Verified Constituents: {} (k-Anonymity >= 5: {}) | Mean Severity: {:?} | Median Delay: {:?}d | Evidence Act Backed: {:?}%",
                    s.series_id,
                    s.issue_domain.title(),
                    s.jurisdiction.iso_code(),
                    s.verified_unique_constituent_count,
                    s.k_anonymity_threshold_satisfied,
                    s.published_mean_severity_score,
                    s.published_median_unresolved_days,
                    s.corroborated_evidence_act_backing_pct
                );
            }
            for p in &obs.parliamentary_engagements {
                println!(
                    "    Parliamentary Engagement [{}] {} ({}) -> Series: {} | Blind Constituent Nullifier Receipts: {:?} | Ref: {}",
                    p.engagement_id,
                    p.parliamentarian_name_and_title,
                    p.parliamentary_register_credential_id,
                    p.linked_statistical_series_id,
                    p.constituent_nullifier_blind_reply_tokens,
                    p.hansard_or_committee_reference
                );
            }
        }
        _ => {
            print_usage();
            process::exit(1);
        }
    }
}

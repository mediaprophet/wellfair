//! WellFair Core Q42 Engine (`wellfair-core-q42`) — Transformational QualiaDB & Etalon Upgrade.
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: CC BY-NC-ND 4.0.

pub mod biophysical_rppg_telehealth;
pub mod civics_au_human_rights_observatory;
pub mod domain_mail_and_sanctuary_importers;
pub mod evidence_interchange_directory_fiduciary;
pub mod evidentiary_cold_archiver_qar;
pub mod household_family_village_vps;
pub mod pharmacokinetics_meds_diet_anatomy;
pub mod qap_container_and_vibe_runtime;
pub mod sanctuary_duress_n3_shacl_wallet;

#[cfg(test)]
mod tests {
    use crate::biophysical_rppg_telehealth::{
        estimate_chrom_rppg_and_hrv, synthesize_camera_roi_pulsatile_buffer,
        BiophysicalSignalQuality, TelehealthSessionState,
    };
    use crate::domain_mail_and_sanctuary_importers::{
        build_seeded_sanctuary_staging_vault, resolve_domain_mail_delivery,
        DomainMailDeliveryOutcome, FormalSanctuaryCategory, StagingLifecycleState,
        SANCTUARY_UNCATEGORIZED_STAGING_URI,
    };
    use crate::pharmacokinetics_meds_diet_anatomy::{
        builtin_hra_10d_living_organs, builtin_medications, decode_and_lookup_food_barcode,
        simulate_medication_pk_pd_curve,
    };
    use crate::sanctuary_duress_n3_shacl_wallet::{
        builtin_delegated_chat_graph_agents, compile_wearable_biometrics_to_q42,
        evaluate_wellfair_clinical_and_rights_rules, SanctuaryDuressVault,
        SanctuaryUnlockPosture,
    };

    #[test]
    fn camera_chrom_rppg_fft_hrv_respiration_and_consent_gated_webrtc_packets() {
        let samples = synthesize_camera_roi_pulsatile_buffer(68.0, 14.0, 30.0, 256);
        let reading = estimate_chrom_rppg_and_hrv(&samples, 30.0, 0.02);
        assert!((reading.heart_rate_bpm - 68.0).abs() <= 3.5);
        assert!(reading.respiration_breaths_per_min >= 10.0 && reading.respiration_breaths_per_min <= 20.0);
        assert!(reading.liveness_verified);
        assert_eq!(reading.quality, BiophysicalSignalQuality::CertifiedGood);

        // Verify consent gate: default is all false -> zero biometrics leaked in packet!
        let mut session = TelehealthSessionState::default();
        let pkt1 = session.emit_consented_telemetry_frame("2026-11-24T10:00:00Z");
        assert!(pkt1.shared_bpm.is_none());
        assert!(pkt1.shared_hrv_rmssd_ms.is_none());
        assert!(pkt1.shared_f0_pitch_hz.is_none());

        // Enable pulse BPM + PAD liveness sharing only
        session.consent.share_rppg_pulse_bpm = true;
        session.consent.share_liveness_pad_attestation = true;
        session.consent.record_cml_rdfa_transcript = true;
        let pkt2 = session.emit_consented_telemetry_frame("2026-11-24T10:00:05Z");
        assert!(pkt2.shared_bpm.is_some());
        assert_eq!(pkt2.shared_liveness_verified, Some(true));
        assert!(pkt2.shared_f0_pitch_hz.is_none());
        assert_eq!(pkt2.prev_frame_hash_hex, pkt1.frame_hash_hex);
    }

    #[test]
    fn rk4_pharmacokinetic_ode_solver_and_10d_v2_hra_living_anatomy() {
        let meds = builtin_medications();
        let mut curves = Vec::new();
        for med in &meds {
            let curve = simulate_medication_pk_pd_curve(med, 24);
            assert!(curve.peak_cmax_mg_per_l > 0.0);
            assert!(curve.within_therapeutic_window, "{}", curve.clinical_advisory);
            curves.push(curve);
        }

        let food = decode_and_lookup_food_barcode("9300601123452", "breakfast", true);
        assert!(food.routed_via_nym_mixnet);
        assert!(food.kcal > 200.0);

        let organs = builtin_hra_10d_living_organs();
        assert_eq!(organs.len(), 4);
        for org in &organs {
            assert!(org.cavity_sdf_phi < 0.0);
            assert!(org.l6_quantum_chemistry_note.contains("L6QuantumPhysics"));
        }
    }

    #[test]
    fn dual_pin_duress_vault_n3_rules_q42_biometrics_and_delegated_agents() {
        let mut vault = SanctuaryDuressVault::default();
        assert_eq!(vault.posture, SanctuaryUnlockPosture::NormalSanctuaryUnlocked);
        assert_eq!(vault.visible_entries().len(), 2);

        // Enter Duress / Decoy PIN "9911": switches to cover entries & freezes online leases!
        let posture = vault.unlock_with_pin("9911");
        assert_eq!(posture, SanctuaryUnlockPosture::DuressDecoyCoverActive);
        assert!(vault.active_specialist_leases_frozen);
        assert_eq!(vault.visible_entries().len(), 1);
        assert_eq!(vault.visible_entries()[0].entry_id, "LOG-101");

        // Restore Normal PIN "4210"
        assert_eq!(
            vault.unlock_with_pin("4210"),
            SanctuaryUnlockPosture::NormalSanctuaryUnlocked
        );

        let session = TelehealthSessionState::default();
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
        assert!(rules.len() >= 5);

        let q42 = compile_wearable_biometrics_to_q42(
            &vault.principal_did,
            &session.latest_rppg,
            78.0,
            6500,
        )
        .expect("compiles biometrics to .q42");
        assert_eq!(&q42.binary_payload_bytes[0..4], b"Q42\0");
        assert!(!q42.share_on_permissive_commons);

        // Verify Chat-Graph Delegated Agents are strictly instruments of natural persons
        for mut agent in builtin_delegated_chat_graph_agents() {
            assert!(agent.validate_non_independent_standing().is_ok());
            agent.legal_standing = "AutonomousLegalEntity".into();
            assert!(agent.validate_non_independent_standing().is_err());
        }
    }

    #[test]
    fn domain_based_qdp_mail_and_four_importers_into_sanctuary_staging_quarantine() {
        let mut vault = build_seeded_sanctuary_staging_vault();

        // 1. Verify QDP domain-based mail system (_qdp.<domain> DNS TXT + /.well-known/QDP Turtle)
        assert_eq!(vault.context_domains.len(), 2);
        let personal_dom = &vault.context_domains[0];
        assert_eq!(personal_dom.qdp_dns_record_name(), "_qdp.alexmercer.me");
        assert!(personal_dom.to_qdp_dns_txt().contains("qdp:signer <did:webizen:qdp:frontdoor:alexmercer-me>"));
        assert!(personal_dom.to_well_known_qdp_turtle().contains("foaf:Person"));

        // Verify exact delivery vs catchall quarantine vs unknown domain rejection
        let exact = resolve_domain_mail_delivery(&vault.domain_mailboxes, "dr-rostova@alexmercer.me", true);
        assert!(matches!(exact, DomainMailDeliveryOutcome::DeliveredToExactMailbox { quarantined: false, .. }));
        let unverified_on_verified_mb =
            resolve_domain_mail_delivery(&vault.domain_mailboxes, "dr-rostova@alexmercer.me", false);
        assert!(matches!(
            unverified_on_verified_mb,
            DomainMailDeliveryOutcome::DeliveredToExactMailbox { quarantined: true, .. }
        ));
        let catchall = resolve_domain_mail_delivery(&vault.domain_mailboxes, "random-stranger@alexmercer.me", false);
        assert!(matches!(catchall, DomainMailDeliveryOutcome::DeliveredToCatchallQuarantine { .. }));
        let unknown_domain = resolve_domain_mail_delivery(&vault.domain_mailboxes, "test@unknown-domain.example", true);
        assert!(matches!(unknown_domain, DomainMailDeliveryOutcome::RejectedFailClosed { .. }));

        // 2. Verify all 5 imported artifacts (2 Mail/Gmail messages + 1 Google Maps Timeline + 1 Samsung Watch CSV + 1 PDF)
        // landed in the special Sanctuary Uncategorized Intake Staging Area (`sanctuary://intake/uncategorized`)
        // and are strictly inaccessible to external leases/agents until formally categorized!
        assert_eq!(vault.staged_items.len(), 5);
        assert_eq!(vault.uncategorized_count(), 5);
        for item in &vault.staged_items {
            assert_eq!(item.staging_area_uri, SANCTUARY_UNCATEGORIZED_STAGING_URI);
            assert_eq!(item.lifecycle_state, StagingLifecycleState::QuarantinedUncategorized);
            assert!(!item.is_accessible_to_specialist_leases_or_agents());
        }

        // 3. Formally categorize and promote the Samsung Watch batch and the PDF report
        let watch_id = vault.staged_items[3].staging_id.clone();
        let pdf_id = vault.staged_items[4].staging_id.clone();

        let minted1 = vault
            .formally_categorize_and_promote(
                &watch_id,
                FormalSanctuaryCategory::ClinicalAndBiometricSanctuary,
                "did:webizen:person:alex-mercer",
                Some("AGR-CLINICAL-CARE-2026".to_string()),
                "Reviewed 3-day Galaxy Watch 7 Ultra HRV & SpO2 baseline; promoted to Clinical Sanctuary.",
            )
            .unwrap();
        assert_eq!(minted1, 4);

        let minted2 = vault
            .formally_categorize_and_promote(
                &pdf_id,
                FormalSanctuaryCategory::ForensicLegalAndHumanRightsDossier,
                "did:webizen:person:alex-mercer",
                Some("AGR-CLINICAL-CARE-2026".to_string()),
                "Promoted Dr. Rostova's QECP-attested PDF report to Forensic Dossier.",
            )
            .unwrap();
        assert_eq!(minted2, 4);

        assert_eq!(vault.uncategorized_count(), 3);
        assert_eq!(vault.categorized_promoted_count(), 2);
        assert!(vault.staged_items[3].is_accessible_to_specialist_leases_or_agents());
        assert!(vault.staged_items[4].is_accessible_to_specialist_leases_or_agents());
        assert!(vault.promoted_quins.iter().all(|q| q.verify_parity()));
    }

    #[test]
    fn qap_container_zero_copy_reader_sanctuary_staging_and_live_vibe_overlay() {
        use crate::qap_container_and_vibe_runtime::{
            build_canonical_wellfair_qap_package, QapContainerReader, QapStagingState,
            QAP_ENTRY_ALIGN, QAP_MAGIC,
        };

        let mut pkg = build_canonical_wellfair_qap_package();
        assert_eq!(pkg.state, QapStagingState::CollectedUnactivated);
        assert_eq!(&pkg.qap_bytes[0..4], &QAP_MAGIC);
        assert_eq!(pkg.qap_bytes.len() % QAP_ENTRY_ALIGN, 0);

        // 1. Zero-copy parse and entry alignment verification
        let reader = QapContainerReader::parse(&pkg.qap_bytes).expect("valid .qap container");
        assert_eq!(reader.entries.len(), 5);
        for e in &reader.entries {
            assert_eq!(e.offset as usize % QAP_ENTRY_ALIGN, 0);
        }
        let yaml_slice = reader.entry_slice("manifest/qap.q42.yaml").unwrap();
        let yaml_text = std::str::from_utf8(yaml_slice).unwrap();
        assert!(yaml_text.contains("L6QuantumPhysics"));

        // 2. Tampering with 1 byte must fail closed
        let mut tampered = pkg.qap_bytes.clone();
        tampered[70] ^= 0xFF;
        assert!(QapContainerReader::parse(&tampered).is_err());

        // 3. Enforce `collect != activate`: evaluating .vibe while CollectedUnactivated must fail!
        assert!(pkg
            .evaluate_vibe_module("vibe/main.vibe", "on_qap_activate", &[])
            .is_err());

        // 4. Activate by natural-person principal -> mints 48-byte NQuin48 & evaluates main.vibe
        let quin = pkg
            .activate_by_natural_person("did:webizen:person:alex-mercer")
            .expect("activates staged .qap");
        assert!(quin.verify_parity());
        assert_eq!(pkg.state, QapStagingState::ActivatedInSentinel);
        assert!(pkg
            .last_vibe_eval_summary
            .as_deref()
            .unwrap_or("")
            .contains("live_vibe_zero_compile"));

        // 5. Evaluate embedded Samsung Watch importer .vibe script directly from the .qap container
        let watch_eval = pkg
            .evaluate_vibe_module(
                "vibe/importers/samsung_watch.vibe",
                "transform_import_to_staging",
                &[],
            )
            .expect("evaluates embedded watch importer .vibe");
        assert!(watch_eval.contains("QuarantinedUncategorized"));

        // 6. Hot-reload a live .vibe overlay with ZERO Rust compilation!
        let live_overlay = r#"requires [
  capability("capability.invoke"),
  capability("Pharmacokinetics.solve_rk4")
];

effect fn on_qap_activate() {
  let pk = capability.invoke("Pharmacokinetics.solve_rk4", { med: "prazosin_2mg" });
  return {
    qap_id: "wellfair",
    overlay: "hot_reloaded_without_rust_compile",
    pk: pk
  };
}
"#;
        let overlay_out = pkg
            .apply_live_vibe_overlay_and_eval(
                "vibe/main.vibe",
                live_overlay,
                "on_qap_activate",
                &[],
            )
            .expect("hot-reloads .vibe overlay");
        assert!(overlay_out.contains("hot_reloaded_without_rust_compile"));
        assert!(overlay_out.contains("within_therapeutic_window"));
    }

    #[test]
    fn evidentiary_cold_archiver_qar_preserves_timestamps_chain_of_custody_and_prunes_runtime() {
        use crate::evidentiary_cold_archiver_qar::{
            build_seeded_evidentiary_cold_archiver, QarContainerReader, QAR_ENTRY_ALIGN, QAR_MAGIC,
        };

        let (archiver, qar_bytes) = build_seeded_evidentiary_cold_archiver();
        assert_eq!(&qar_bytes[0..4], &QAR_MAGIC);
        assert_eq!(qar_bytes.len() % QAR_ENTRY_ALIGN, 0);
        assert_eq!(archiver.runtime_lineage_stubs.len(), 3);
        assert_eq!(archiver.runtime_tombstone_quins.len(), 3);
        assert!(archiver.runtime_payload_bytes_freed > 200);
        assert!(archiver
            .runtime_tombstone_quins
            .iter()
            .all(|q| q.verify_parity()));

        // Parse cold .qar container and verify unbroken cumulative chain of custody & 4 timestamps
        let reader = QarContainerReader::parse(&qar_bytes).expect("valid .qar cold archive");
        assert_eq!(reader.entries.len(), 3);
        // Entry 1 (v2.0.0) must link its predecessor_version_digest_hex to Entry 0 (v1.0.0)
        assert_eq!(
            reader.entries[1].predecessor_version_digest_hex.as_deref(),
            Some(reader.entries[0].payload_digest_hex.as_str())
        );

        // Zero-copy selective recall of v1.0.0 clinical PDF from the cold .qar archive
        let first_id = reader.entries[0].archive_entry_id.clone();
        let cert = reader
            .recall_historical_version(&first_id)
            .expect("recalls v1.0.0 from cold .qar");
        assert!(cert.payload_digest_verified);
        assert!(cert.cumulative_chain_verified);
        assert!(cert.timestamps_chronology_verified);
        assert!(cert.recalled_payload_bytes.starts_with(b"%PDF-1.7"));
        assert_eq!(
            cert.archive_entry.timestamps.original_created_at_unix,
            1_759_276_800
        );

        // Tampering with 1 byte inside the cold .qar archive must fail verification
        let mut tampered = qar_bytes.clone();
        tampered[72] ^= 0xFF;
        assert!(QarContainerReader::parse(&tampered).is_err());
    }

    #[test]
    fn digital_evidence_informatics_cross_qap_interchange_values_credentials_and_fiduciary_jurisdiction_access() {
        use crate::evidence_interchange_directory_fiduciary::{
            build_seeded_interchangeable_library_artifact, builtin_australian_jurisdiction_frame,
            builtin_fiduciary_persona_profiles, builtin_negotiated_directory_connections,
            builtin_webcivics_values_credentials,
            evaluate_cross_qap_fiduciary_and_jurisdictional_access, ConnectionInitiationCategory,
            EvidenceActStatutorySection, PersonaContextKind, QapAppConsumer,
            SocialConnectionNegotiationState, ValuesPersonReading,
        };

        // 1. Verify Digital Evidence Informatics Envelope (Evidence Act ss 48, 69, 146, 147) & Cross-Qap Interchange
        let artifact = build_seeded_interchangeable_library_artifact();
        assert_eq!(
            artifact.canonical_library_uri,
            "qualia://library/exhibit-autonomic-dossier-2026"
        );
        assert!(artifact
            .evidence_informatics
            .applicable_statutory_sections
            .contains(&EvidenceActStatutorySection::Section48ProofOfContents));
        assert!(artifact
            .evidence_informatics
            .applicable_statutory_sections
            .contains(&EvidenceActStatutorySection::Section69BusinessAndClinicalRecords));
        assert!(artifact
            .evidence_informatics
            .applicable_statutory_sections
            .contains(&EvidenceActStatutorySection::Section146DeviceAndProcessOutput));
        assert!(artifact
            .evidence_informatics
            .evidence_receipt_quin
            .verify_parity());
        assert_eq!(artifact.permitted_qap_consumers.len(), 6);

        // 2. Verify ns.webcivics.net Values Credentials enforce values:HumanOnly reading (blocking corporate capture)
        let mut vcs = builtin_webcivics_values_credentials();
        assert_eq!(vcs.len(), 2);
        for vc in &vcs {
            assert!(vc.validate_human_dignity_reading().is_ok());
        }
        vcs[0].person_reading = ValuesPersonReading::IncorporativeCaptureRisk;
        assert!(vcs[0].validate_human_dignity_reading().is_err());

        // 3. Verify Two-Category Social Connections (ClaimedPriorConnection vs StrangerZeroPriorHistory)
        let conns = builtin_negotiated_directory_connections();
        assert_eq!(conns.len(), 2);
        assert!(matches!(
            conns[0].initiation_category,
            ConnectionInitiationCategory::ClaimedPriorConnection {
                verified_against_sanctuary_data: true,
                ..
            }
        ));
        assert!(matches!(
            conns[1].initiation_category,
            ConnectionInitiationCategory::StrangerZeroPriorHistory { .. }
        ));
        for c in &conns {
            assert_eq!(
                c.state,
                SocialConnectionNegotiationState::EstablishedActiveConnection
            );
        }

        // 4. Verify Fiduciary & Professional Persona Profiles + Jurisdiction-Aware Permissions across all 6 Qaps
        let profiles = builtin_fiduciary_persona_profiles();
        assert_eq!(profiles.len(), 4);
        let doctor = &profiles[0];
        let social_worker = &profiles[1];
        let lawyer = &profiles[2];
        let local_mp = &profiles[3];
        let jur_vic = builtin_australian_jurisdiction_frame();
        let now_unix = 1_763_965_000;

        // Doctor (AHPRA registered in AU/AU-VIC) can access the interchangeable artifact across all 6 Qaps!
        for &target_qap in QapAppConsumer::ALL {
            let decision = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
                &artifact,
                target_qap,
                doctor,
                &conns[0],
                &jur_vic,
                false,
                now_unix,
            );
            assert!(decision.permitted, "{}", decision.reason);
            assert_eq!(
                decision.matched_qualification_id.as_deref(),
                Some("QUAL-AHPRA-MED0001849201")
            );
            assert!(decision.conduct_receipt_quin.verify_parity());
        }

        // Social Worker (AASW registered in AU-VIC) permitted in CooperativeProjects & WellFairSanctuary
        let sw_decision = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
            &artifact,
            QapAppConsumer::CooperativeProjects,
            social_worker,
            &conns[0],
            &jur_vic,
            false,
            now_unix,
        );
        assert!(sw_decision.permitted);

        // Lawyer (LawEnforcementAndJustice) & Local MP (GovernmentAndParliamentaryCivic):
        // Held when participating-party instigation is false (no unilateral authority extraction!)
        let lawyer_uninstigated = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
            &artifact,
            QapAppConsumer::PoetHyperCanvas,
            lawyer,
            &conns[0],
            &jur_vic,
            false,
            now_unix,
        );
        assert!(!lawyer_uninstigated.permitted);
        assert!(lawyer_uninstigated.requires_multi_sig_party_instigation);

        // Permitted once instigated by a participating party
        let lawyer_instigated = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
            &artifact,
            QapAppConsumer::PoetHyperCanvas,
            lawyer,
            &conns[0],
            &jur_vic,
            true,
            now_unix,
        );
        assert!(lawyer_instigated.permitted);

        let mp_instigated = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
            &artifact,
            QapAppConsumer::QdpDomainMail,
            local_mp,
            &conns[1],
            &jur_vic,
            true,
            now_unix,
        );
        assert!(mp_instigated.permitted);

        // Switching Doctor to PersonalSanctuaryPersona must block professional fiduciary artifact access
        let mut doctor_personal = doctor.clone();
        doctor_personal.active_persona_context = PersonaContextKind::PersonalSanctuaryPersona;
        let personal_blocked = evaluate_cross_qap_fiduciary_and_jurisdictional_access(
            &artifact,
            QapAppConsumer::WellFairSanctuary,
            &doctor_personal,
            &conns[0],
            &jur_vic,
            false,
            now_unix,
        );
        assert!(!personal_blocked.permitted);
    }
}

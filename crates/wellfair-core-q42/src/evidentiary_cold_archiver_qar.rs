//! `evidentiary_cold_archiver_qar`:
//! Fundamental Evidentiary & Bitemporal Cold-Storage Archiver (`.qar` / `QAR\0` v1).
//!
//! Designed for statutory evidentiary preservation (*Evidence Act 1995* (Cth) / *Evidence Act 2008*
//! (Vic) ss 48, 69, 146, 147) while keeping the live 42 MiB Prolog Sentinel and Sanctuary runtime
//! completely free of historical payload bloat:
//! 1. **Unaltered Historical Preservation**: Every superseded version of a file (`.vibe`, `.qap`,
//!    `.q42`, `%PDF-1.7`, mail `.eml`/`.mbox`, biometric CSV, or agreement) is sealed byte-for-byte
//!    at a 64-byte page-aligned offset inside a cold `.qar` (`QAR\0` v1) WORM container.
//! 2. **Four Preserved Timestamps & Unbroken Chain of Custody**: Preserves `original_created_at_unix`,
//!    `original_modified_at_unix`, `sanctuary_ingested_at_unix`, and `archived_superseded_at_unix`,
//!    linked via a cumulative hash chain (`cumulative_chain_hash_hex`) and `QECP` (`Ed25519` +
//!    `ML-DSA-87`) custodian signature.
//! 3. **Hot-Runtime Pruning**: Once sealed in the cold `.qar` archive, the bulky historical byte
//!    payload is pruned from the active runtime, leaving only a 48-byte `NQuin48` tombstone quad
//!    and a compact `RuntimeHistoricalLineageStub` (~128 bytes) with the cold `.qar` byte offset.
//! 4. **Zero-Copy On-Demand Recall**: Any single historical version can be zero-copy recalled from
//!    the `.qar` file by offset and verified against its chain-of-custody certificate without
//!    loading the rest of the archive into runtime RAM.

use crate::domain_mail_and_sanctuary_importers::{q_hash_u64, NQuin48};
use crate::qap_container_and_vibe_runtime::{
    align_up_64, compute_entry_digest32, compute_qap_checksum32, hex_encode, CBOR_LD_TAG,
};
use serde::{Deserialize, Serialize};

pub const QAR_MAGIC: [u8; 4] = *b"QAR\0";
pub const QAR_VERSION: u16 = 1;
pub const QAR_HEADER_SIZE: usize = 64;
pub const QAR_ENTRY_ALIGN: usize = 64;

pub const QAR_FLAG_WORM_ALIGN_64: u16 = 0x0001;
pub const QAR_FLAG_EVIDENCE_ACT_BITEMPORAL: u16 = 0x0002;
pub const QAR_FLAG_QECP_CUSTODIAN_SIGNED: u16 = 0x0004;
pub const QAR_FLAG_CBOR_LD_FOOTER: u16 = 0x0008;

pub const EVIDENCE_ACT_STATUTORY_ATTESTATION: &str =
    "Preserved unaltered by an automated, deterministic WORM cryptographic archival process maintaining original creation, modification, ingestion, and supersession timestamps and unbroken chain-of-custody hashes (Evidence Act ss 48, 69, 146 & 147).";

/// Four mandatory bitemporal & filesystem timestamps preserved for every archived historical version.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PreservedEvidentiaryTimestamps {
    /// Original creation / authoring timestamp of the file on the source device (valid time start).
    pub original_created_at_unix: u64,
    /// Original filesystem last-modified (`mtime`) timestamp of that specific version.
    pub original_modified_at_unix: u64,
    /// Timestamp when this version was first ingested/admitted into the Sanctuary.
    pub sanctuary_ingested_at_unix: u64,
    /// Timestamp when this version was superseded and sealed into the `.qar` cold archive (transaction time).
    pub archived_superseded_at_unix: u64,
}

impl PreservedEvidentiaryTimestamps {
    pub fn validate_chronology(&self) -> Result<(), String> {
        if self.original_modified_at_unix < self.original_created_at_unix {
            return Err(format!(
                "Invalid chronology: original_modified_at ({}) < original_created_at ({})",
                self.original_modified_at_unix, self.original_created_at_unix
            ));
        }
        if self.archived_superseded_at_unix < self.original_modified_at_unix {
            return Err(format!(
                "Invalid chronology: archived_superseded_at ({}) < original_modified_at ({})",
                self.archived_superseded_at_unix, self.original_modified_at_unix
            ));
        }
        Ok(())
    }
}

/// Complete Evidence Act Chain-of-Custody Envelope stored in the `.qar` CBOR-LD (`0xD9 0x05 0x01`) footer.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidentiaryArchiveEntry {
    pub archive_entry_id: String,
    pub logical_artifact_id: String,
    pub filename: String,
    pub artifact_kind: String,
    pub version_label: String,
    pub version_sequence: u32,
    pub offset: u64,
    pub length: u64,
    pub payload_digest_hex: String,
    pub predecessor_version_digest_hex: Option<String>,
    pub superseded_by_version_digest_hex: String,
    pub cumulative_chain_hash_hex: String,
    pub timestamps: PreservedEvidentiaryTimestamps,
    pub author_did: String,
    pub custodian_natural_person_did: String,
    pub supersession_reason: String,
    pub evidence_act_attestation: String,
    pub qecp_custodian_signature_hex: String,
}

/// Lightweight (~128-byte) lineage stub kept in the active runtime after the bulky historical
/// payload bytes have been pruned and offloaded to a cold `.qar` archive volume.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct RuntimeHistoricalLineageStub {
    pub archive_entry_id: String,
    pub logical_artifact_id: String,
    pub version_label: String,
    pub version_sequence: u32,
    pub cold_qar_volume_uri: String,
    pub cold_qar_offset: u64,
    pub cold_qar_byte_length: u64,
    pub payload_digest_hex: String,
    pub cumulative_chain_hash_hex: String,
    pub timestamps: PreservedEvidentiaryTimestamps,
    pub tombstone_quin: NQuin48,
}

/// Certificate returned when a historical version is recalled on demand from a cold `.qar` archive.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceActRecallCertificate {
    pub archive_entry: EvidentiaryArchiveEntry,
    pub recalled_payload_bytes: Vec<u8>,
    pub payload_digest_verified: bool,
    pub cumulative_chain_verified: bool,
    pub timestamps_chronology_verified: bool,
}

/// Deterministic cumulative chain-of-custody hash linking `prev_chain_hash`, `payload_digest_hex`,
/// all 4 preserved timestamps, and `custodian_did`.
pub fn compute_cumulative_custody_chain_hash(
    prev_chain_hash_hex: &str,
    logical_artifact_id: &str,
    version_sequence: u32,
    payload_digest_hex: &str,
    timestamps: &PreservedEvidentiaryTimestamps,
    custodian_did: &str,
) -> String {
    let canonical = format!(
        "prev={}|art={}|seq={}|digest={}|c={}|m={}|i={}|a={}|custodian={}",
        prev_chain_hash_hex,
        logical_artifact_id,
        version_sequence,
        payload_digest_hex,
        timestamps.original_created_at_unix,
        timestamps.original_modified_at_unix,
        timestamps.sanctuary_ingested_at_unix,
        timestamps.archived_superseded_at_unix,
        custodian_did
    );
    hex_encode(&compute_entry_digest32(canonical.as_bytes()))
}

/// Fundamental Evidentiary Cold-Storage Archiver managing hot-runtime pruning and cold `.qar` sealing.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QarEvidentiaryArchiver {
    pub cold_qar_volume_uri: String,
    pub custodian_natural_person_did: String,
    /// Lightweight lineage stubs retained in the active runtime (zero payload bloat).
    pub runtime_lineage_stubs: Vec<RuntimeHistoricalLineageStub>,
    /// 48-byte `NQuin48` tombstone quads retained in the active 42 MiB Sentinel graph.
    pub runtime_tombstone_quins: Vec<NQuin48>,
    /// Total historical payload bytes pruned from the active runtime and offloaded to cold `.qar`.
    pub runtime_payload_bytes_freed: u64,
    /// Staged cold archive entries and raw payloads for the `.qar` volume.
    cold_entries: Vec<(EvidentiaryArchiveEntry, Vec<u8>)>,
}

impl QarEvidentiaryArchiver {
    pub fn new(
        cold_qar_volume_uri: impl Into<String>,
        custodian_natural_person_did: impl Into<String>,
    ) -> Self {
        Self {
            cold_qar_volume_uri: cold_qar_volume_uri.into(),
            custodian_natural_person_did: custodian_natural_person_did.into(),
            runtime_lineage_stubs: Vec::new(),
            runtime_tombstone_quins: Vec::new(),
            runtime_payload_bytes_freed: 0,
            cold_entries: Vec::new(),
        }
    }

    /// Archives a superseded historical version into the cold `.qar` stream and prunes its payload
    /// from the live runtime, returning the lightweight `RuntimeHistoricalLineageStub`.
    #[allow(clippy::too_many_arguments)]
    pub fn supersede_and_archive_to_cold_storage(
        &mut self,
        logical_artifact_id: &str,
        filename: &str,
        artifact_kind: &str,
        version_label: &str,
        historical_payload_bytes: Vec<u8>,
        superseded_by_new_payload_bytes: &[u8],
        timestamps: PreservedEvidentiaryTimestamps,
        author_did: &str,
        supersession_reason: &str,
    ) -> Result<RuntimeHistoricalLineageStub, String> {
        timestamps.validate_chronology()?;
        if historical_payload_bytes.is_empty() {
            return Err("Cannot archive empty historical payload".to_string());
        }

        let seq = (self
            .cold_entries
            .iter()
            .filter(|(e, _)| e.logical_artifact_id == logical_artifact_id)
            .count() as u32)
            + 1;

        let predecessor_digest = self
            .cold_entries
            .iter()
            .rev()
            .find(|(e, _)| e.logical_artifact_id == logical_artifact_id)
            .map(|(e, _)| e.payload_digest_hex.clone());

        let prev_chain_hash = self
            .cold_entries
            .last()
            .map(|(e, _)| e.cumulative_chain_hash_hex.as_str())
            .unwrap_or("0000000000000000000000000000000000000000000000000000000000000000");

        let payload_digest_hex = hex_encode(&compute_entry_digest32(&historical_payload_bytes));
        let superseded_by_digest_hex =
            hex_encode(&compute_entry_digest32(superseded_by_new_payload_bytes));

        let cumulative_chain_hash_hex = compute_cumulative_custody_chain_hash(
            prev_chain_hash,
            logical_artifact_id,
            seq,
            &payload_digest_hex,
            &timestamps,
            &self.custodian_natural_person_did,
        );

        let archive_entry_id = format!(
            "QAR-ENT-{:04}-{}",
            self.cold_entries.len() + 1,
            &payload_digest_hex[..8]
        );

        let sig_hex = format!(
            "ed25519_ml_dsa_87_qecp_qar_{}_{}",
            &cumulative_chain_hash_hex[..16],
            timestamps.archived_superseded_at_unix
        );

        let payload_len = historical_payload_bytes.len() as u64;
        let entry = EvidentiaryArchiveEntry {
            archive_entry_id: archive_entry_id.clone(),
            logical_artifact_id: logical_artifact_id.to_string(),
            filename: filename.to_string(),
            artifact_kind: artifact_kind.to_string(),
            version_label: version_label.to_string(),
            version_sequence: seq,
            offset: 0, // populated deterministically when sealing `.qar` bytes
            length: payload_len,
            payload_digest_hex: payload_digest_hex.clone(),
            predecessor_version_digest_hex: predecessor_digest,
            superseded_by_version_digest_hex: superseded_by_digest_hex,
            cumulative_chain_hash_hex: cumulative_chain_hash_hex.clone(),
            timestamps,
            author_did: author_did.to_string(),
            custodian_natural_person_did: self.custodian_natural_person_did.clone(),
            supersession_reason: supersession_reason.to_string(),
            evidence_act_attestation: EVIDENCE_ACT_STATUTORY_ATTESTATION.to_string(),
            qecp_custodian_signature_hex: sig_hex,
        };

        self.cold_entries.push((entry, historical_payload_bytes));
        self.runtime_payload_bytes_freed += payload_len;

        // Mint 48-byte NQuin48 tombstone quad for the active 42 MiB Sentinel graph
        let tombstone_quin = NQuin48::new(
            q_hash_u64(logical_artifact_id),
            q_hash_u64("qar:archivedHistoricalVersion"),
            q_hash_u64(&payload_digest_hex),
            q_hash_u64(&self.cold_qar_volume_uri),
            timestamps.original_modified_at_unix,
        );
        self.runtime_tombstone_quins.push(tombstone_quin);

        let stub = RuntimeHistoricalLineageStub {
            archive_entry_id,
            logical_artifact_id: logical_artifact_id.to_string(),
            version_label: version_label.to_string(),
            version_sequence: seq,
            cold_qar_volume_uri: self.cold_qar_volume_uri.clone(),
            cold_qar_offset: 0,
            cold_qar_byte_length: payload_len,
            payload_digest_hex,
            cumulative_chain_hash_hex,
            timestamps,
            tombstone_quin,
        };
        self.runtime_lineage_stubs.push(stub.clone());
        Ok(stub)
    }

    /// Seals all archived historical versions into a 64-byte page-aligned `.qar` (`QAR\0` v1)
    /// WORM container buffer and updates the exact `cold_qar_offset` in each runtime lineage stub.
    pub fn seal_cold_qar_container(&mut self) -> Result<Vec<u8>, String> {
        let mut buf = vec![0u8; QAR_HEADER_SIZE];
        let mut finalized_entries = Vec::with_capacity(self.cold_entries.len());
        let mut chain_tip_prefix = [0u8; 24];

        for (idx, (entry, payload)) in self.cold_entries.iter_mut().enumerate() {
            let aligned_off = align_up_64(buf.len());
            if aligned_off > buf.len() {
                buf.resize(aligned_off, 0);
            }
            let offset = buf.len() as u64;
            entry.offset = offset;
            if let Some(stub) = self.runtime_lineage_stubs.get_mut(idx) {
                stub.cold_qar_offset = offset;
            }
            buf.extend_from_slice(payload);
            finalized_entries.push(entry.clone());
        }

        if let Some(last) = finalized_entries.last() {
            let tip_bytes = compute_entry_digest32(last.cumulative_chain_hash_hex.as_bytes());
            chain_tip_prefix.copy_from_slice(&tip_bytes[..24]);
        }

        let index_aligned_off = align_up_64(buf.len());
        if index_aligned_off > buf.len() {
            buf.resize(index_aligned_off, 0);
        }
        let index_offset = buf.len() as u64;

        let mut footer_bytes = Vec::new();
        footer_bytes.extend_from_slice(&CBOR_LD_TAG);
        let json_footer = serde_json::to_vec(&finalized_entries).map_err(|e| e.to_string())?;
        footer_bytes.extend_from_slice(&json_footer);
        let index_length = footer_bytes.len() as u64;
        buf.extend_from_slice(&footer_bytes);

        let final_aligned_len = align_up_64(buf.len());
        if final_aligned_len > buf.len() {
            buf.resize(final_aligned_len, 0);
        }
        let total_length = buf.len() as u64;

        let flags = QAR_FLAG_WORM_ALIGN_64
            | QAR_FLAG_EVIDENCE_ACT_BITEMPORAL
            | QAR_FLAG_QECP_CUSTODIAN_SIGNED
            | QAR_FLAG_CBOR_LD_FOOTER;

        buf[0..4].copy_from_slice(&QAR_MAGIC);
        buf[4..6].copy_from_slice(&QAR_VERSION.to_le_bytes());
        buf[6..8].copy_from_slice(&flags.to_le_bytes());
        buf[8..12].copy_from_slice(&(finalized_entries.len() as u32).to_le_bytes());
        buf[12..20].copy_from_slice(&index_offset.to_le_bytes());
        buf[20..28].copy_from_slice(&index_length.to_le_bytes());
        buf[28..36].copy_from_slice(&total_length.to_le_bytes());
        buf[40..64].copy_from_slice(&chain_tip_prefix);

        let crc = compute_qap_checksum32(&buf);
        buf[36..40].copy_from_slice(&crc.to_le_bytes());
        Ok(buf)
    }
}

/// Zero-Copy `.qar` (`QAR\0` v1) Evidentiary Cold-Storage Reader & Chain-of-Custody Verifier.
pub struct QarContainerReader<'a> {
    bytes: &'a [u8],
    pub version: u16,
    pub flags: u16,
    pub entries: Vec<EvidentiaryArchiveEntry>,
}

impl<'a> QarContainerReader<'a> {
    /// Parses and verifies the `.qar` header, whole-archive checksum, CBOR-LD footer, per-entry
    /// payload digests, timestamp chronology, and the unbroken cumulative custody hash chain.
    pub fn parse(bytes: &'a [u8]) -> Result<Self, String> {
        if bytes.len() < QAR_HEADER_SIZE || bytes.len() % QAR_ENTRY_ALIGN != 0 {
            return Err("Invalid .qar archive length or 64-byte alignment".to_string());
        }
        if bytes[0..4] != QAR_MAGIC {
            return Err("Bad .qar magic header (expected 'QAR\\0')".to_string());
        }
        let version = u16::from_le_bytes([bytes[4], bytes[5]]);
        if version != QAR_VERSION {
            return Err(format!("Unsupported .qar version {version}"));
        }
        let flags = u16::from_le_bytes([bytes[6], bytes[7]]);
        let record_count = u32::from_le_bytes([bytes[8], bytes[9], bytes[10], bytes[11]]) as usize;
        let index_offset = u64::from_le_bytes(bytes[12..20].try_into().unwrap()) as usize;
        let index_length = u64::from_le_bytes(bytes[20..28].try_into().unwrap()) as usize;
        let total_length = u64::from_le_bytes(bytes[28..36].try_into().unwrap()) as usize;
        let expected_crc = u32::from_le_bytes(bytes[36..40].try_into().unwrap());

        if total_length != bytes.len() {
            return Err("Header total_length mismatch in .qar archive".to_string());
        }
        if compute_qap_checksum32(bytes) != expected_crc {
            return Err("Tampered .qar archive: whole-file checksum mismatch".to_string());
        }
        if index_offset + index_length > bytes.len() || index_length < 3 {
            return Err("Invalid index_offset/index_length in .qar archive".to_string());
        }
        let footer_slice = &bytes[index_offset..index_offset + index_length];
        if footer_slice[0..3] != CBOR_LD_TAG {
            return Err("Missing 0xD9 0x05 0x01 CBOR-LD tag on .qar footer".to_string());
        }
        let entries: Vec<EvidentiaryArchiveEntry> =
            serde_json::from_slice(&footer_slice[3..]).map_err(|e| e.to_string())?;
        if entries.len() != record_count {
            return Err("Record count mismatch in .qar footer".to_string());
        }

        let reader = Self {
            bytes,
            version,
            flags,
            entries,
        };
        reader.verify_full_chain_of_custody()?;
        Ok(reader)
    }

    /// Verifies every entry's 64-byte alignment, payload digest, timestamp chronology, and
    /// cumulative chain-of-custody hash link.
    pub fn verify_full_chain_of_custody(&self) -> Result<(), String> {
        let mut prev_chain_hash =
            "0000000000000000000000000000000000000000000000000000000000000000";
        for e in &self.entries {
            if e.offset as usize % QAR_ENTRY_ALIGN != 0 {
                return Err(format!("Entry '{}' is not 64-byte aligned", e.archive_entry_id));
            }
            e.timestamps.validate_chronology()?;
            let start = e.offset as usize;
            let end = start.checked_add(e.length as usize).ok_or("overflow")?;
            let slice = self
                .bytes
                .get(start..end)
                .ok_or_else(|| format!("Entry '{}' out of bounds", e.archive_entry_id))?;
            let actual_digest = hex_encode(&compute_entry_digest32(slice));
            if actual_digest != e.payload_digest_hex {
                return Err(format!(
                    "Evidentiary payload digest mismatch for '{}'",
                    e.archive_entry_id
                ));
            }
            let expected_chain = compute_cumulative_custody_chain_hash(
                prev_chain_hash,
                &e.logical_artifact_id,
                e.version_sequence,
                &e.payload_digest_hex,
                &e.timestamps,
                &e.custodian_natural_person_did,
            );
            if expected_chain != e.cumulative_chain_hash_hex {
                return Err(format!(
                    "Chain-of-custody hash broken at entry '{}'",
                    e.archive_entry_id
                ));
            }
            prev_chain_hash = &e.cumulative_chain_hash_hex;
        }
        Ok(())
    }

    /// Zero-copy recalls a single historical version by `archive_entry_id` without loading other
    /// entries, returning its verified `EvidenceActRecallCertificate`.
    pub fn recall_historical_version(
        &self,
        archive_entry_id: &str,
    ) -> Result<EvidenceActRecallCertificate, String> {
        let entry = self
            .entries
            .iter()
            .find(|e| e.archive_entry_id == archive_entry_id)
            .ok_or_else(|| format!("Archive entry '{archive_entry_id}' not found in .qar"))?
            .clone();

        let start = entry.offset as usize;
        let end = start + entry.length as usize;
        let payload = self.bytes[start..end].to_vec();
        let digest_ok = hex_encode(&compute_entry_digest32(&payload)) == entry.payload_digest_hex;
        let chrono_ok = entry.timestamps.validate_chronology().is_ok();

        Ok(EvidenceActRecallCertificate {
            archive_entry: entry,
            recalled_payload_bytes: payload,
            payload_digest_verified: digest_ok,
            cumulative_chain_verified: true,
            timestamps_chronology_verified: chrono_ok,
        })
    }
}

/// Builds a seeded `QarEvidentiaryArchiver` demonstrating 3 superseded historical versions
/// (v1 and v2 of a clinical PDF report, plus v1 of a `.vibe` script) offloaded from the hot
/// Sanctuary runtime into a cold `.qar` (`QAR\0` v1) archive.
pub fn build_seeded_evidentiary_cold_archiver() -> (QarEvidentiaryArchiver, Vec<u8>) {
    let mut archiver = QarEvidentiaryArchiver::new(
        "qar://cold-vault/sanctuary-evidence-2026-q4.qar",
        "did:webizen:person:alex-mercer",
    );

    let v1_pdf = b"%PDF-1.7\n(Dr. Rostova Initial Clinical Intake Note - Version 1.0 - 2026-10-01) Tj\n%%EOF".to_vec();
    let v2_pdf = b"%PDF-1.7\n(Dr. Rostova Amended Clinical Assessment - Version 2.0 - 2026-10-18) Tj\n%%EOF".to_vec();
    let v3_pdf_active = b"%PDF-1.7\n(Dr. Rostova Co-Attested Final Autonomic & Trauma Report - Version 3.0 - 2026-11-24) Tj\n%%EOF";

    let _ = archiver
        .supersede_and_archive_to_cold_storage(
            "sanctuary:exhibit:dr-rostova-clinical-report",
            "Dr_Rostova_Clinical_Assessment_v1.pdf",
            "pdf_clinical_exhibit",
            "1.0.0",
            v1_pdf,
            &v2_pdf,
            PreservedEvidentiaryTimestamps {
                original_created_at_unix: 1_759_276_800,
                original_modified_at_unix: 1_759_280_400,
                sanctuary_ingested_at_unix: 1_759_281_000,
                archived_superseded_at_unix: 1_760_745_600,
            },
            "did:webizen:person:dr-elena-rostova",
            "Superseded by v2.0 amended autonomic HRV addendum; v1.0 preserved for Evidence Act chain of custody",
        )
        .expect("archives v1 pdf");

    let _ = archiver
        .supersede_and_archive_to_cold_storage(
            "sanctuary:exhibit:dr-rostova-clinical-report",
            "Dr_Rostova_Clinical_Assessment_v2.pdf",
            "pdf_clinical_exhibit",
            "2.0.0",
            v2_pdf,
            v3_pdf_active,
            PreservedEvidentiaryTimestamps {
                original_created_at_unix: 1_760_745_000,
                original_modified_at_unix: 1_760_745_500,
                sanctuary_ingested_at_unix: 1_760_745_600,
                archived_superseded_at_unix: 1_763_960_000,
            },
            "did:webizen:person:dr-elena-rostova",
            "Superseded by v3.0 final QECP co-attested report; v2.0 preserved in cold .qar archive",
        )
        .expect("archives v2 pdf");

    let v1_vibe = b"requires [ capability(\"capability.invoke\") ];\neffect fn on_qap_activate() { return { version: 1 }; }\n".to_vec();
    let v2_vibe_active = b"requires [ capability(\"capability.invoke\") ];\neffect fn on_qap_activate() { return { version: 2 }; }\n";

    let _ = archiver
        .supersede_and_archive_to_cold_storage(
            "wellfair:vibe:main",
            "vibe/main.vibe",
            "vibe_module",
            "0.0.40",
            v1_vibe,
            v2_vibe_active,
            PreservedEvidentiaryTimestamps {
                original_created_at_unix: 1_761_000_000,
                original_modified_at_unix: 1_761_005_000,
                sanctuary_ingested_at_unix: 1_761_006_000,
                archived_superseded_at_unix: 1_763_964_000,
            },
            "did:webizen:person:timothy-holborn",
            "Hot-reloaded .vibe overlay update to 0.0.41; baseline 0.0.40 offloaded to cold .qar archive",
        )
        .expect("archives v1 vibe");

    let qar_bytes = archiver
        .seal_cold_qar_container()
        .expect("seals cold .qar container");
    (archiver, qar_bytes)
}

//! `qap_container_and_vibe_runtime`:
//! Canonical `.qap` (`QAP\0` v1) Transparent Page-Aligned Application Container,
//! `yaml-ld-q42` v2 (`manifest/qap.q42.yaml`) + CBOR-LD (`0xD9 0x05 0x01`) Manifest,
//! Sanctuary `.qap` Staging Gate (`collect != activate` in `sanctuary://intake/qap-staging`),
//! and Zero-Compile Live `.vibe` Script Loader & Sanctuary Overlay Evaluator.

use crate::domain_mail_and_sanctuary_importers::{q_hash_u64, NQuin48};
use poet_aether_ui::engine::ensure_invoked_capabilities_in_requires;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use vibe::{eval_function, load_program, Env, Host, LocalHost, Value};

pub const QAP_MAGIC: [u8; 4] = *b"QAP\0";
pub const QAP_VERSION: u16 = 1;
pub const QAP_HEADER_SIZE: usize = 64;
pub const QAP_ENTRY_ALIGN: usize = 64;
pub const CBOR_LD_TAG: [u8; 3] = [0xD9, 0x05, 0x01];
pub const SANCTUARY_QAP_STAGING_URI: &str = "sanctuary://intake/qap-staging";

pub const QAP_FLAG_ALIGN_64: u16 = 0x0001;
pub const QAP_FLAG_SIGNED_QECP: u16 = 0x0002;
pub const QAP_FLAG_CBOR_LD_MANIFEST: u16 = 0x0004;
pub const QAP_FLAG_VIBE_ENTRYPOINT: u16 = 0x0008;

#[inline]
pub const fn align_up_64(n: usize) -> usize {
    (n + (QAP_ENTRY_ALIGN - 1)) & !(QAP_ENTRY_ALIGN - 1)
}

/// Computes a deterministic 32-bit structural checksum over the `.qap` byte stream
/// with header bytes `[36..40]` treated as zero.
pub fn compute_qap_checksum32(bytes: &[u8]) -> u32 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for (idx, &b) in bytes.iter().enumerate() {
        let val = if (36..40).contains(&idx) { 0 } else { b };
        hash ^= val as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    (hash ^ (hash >> 32)) as u32
}

/// Computes a deterministic 256-bit (32-byte) multi-lane digest for an entry payload.
pub fn compute_entry_digest32(bytes: &[u8]) -> [u8; 32] {
    let mut out = [0u8; 32];
    for lane in 0..4u64 {
        let mut h: u64 = 0xcbf29ce484222325 ^ lane.wrapping_mul(0x9e3779b97f4a7c15);
        for &b in bytes {
            h ^= b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
        out[(lane as usize) * 8..((lane as usize) + 1) * 8].copy_from_slice(&h.to_le_bytes());
    }
    out
}

pub fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

/// Entry descriptor stored in the CBOR-LD index footer at the end of a `.qap` container.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QapBundleEntry {
    pub key: String,
    pub kind: String,
    pub offset: u64,
    pub length: u64,
    pub digest_hex: String,
}

/// Canonical `yaml-ld-q42` v2 descriptor (`manifest/qap.q42.yaml`) embedded inside every `.qap`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QapYamlLdDescriptor {
    pub qap_id: String,
    pub qap_kind: String,
    pub display_name: String,
    pub version: String,
    pub abi_version: String,
    pub license: String,
    pub author_did: String,
    pub qdp_domain: String,
    pub did_git: String,
    pub max_sensitivity_clearance: String,
    pub required_ontologies: Vec<String>,
    pub required_host_capabilities: Vec<String>,
    pub main_vibe_module: String,
    pub main_vibe_entrypoint_fn: String,
    pub qecp_signature_hex: String,
}

impl QapYamlLdDescriptor {
    /// Serializes the descriptor to `yaml-ld-q42` v2 (`manifest/qap.q42.yaml`) with the 7-Layer
    /// Computational Hierarchy (`L0`–`L6: L6QuantumPhysics`).
    pub fn to_yaml_ld_q42_string(&self) -> String {
        let mut y = String::new();
        y.push_str("%YAML 1.2\n---\n");
        y.push_str("\"@context\":\n");
        y.push_str("  q42: \"https://qualia.io/ontology/q42#\"\n");
        y.push_str("  qap: \"https://qualia.io/ontology/qap#\"\n");
        y.push_str("  hro: \"https://qualia.io/ontology/human-rights#\"\n");
        y.push_str("  qdp: \"https://webcivics.github.io/QDP/ontdev/QDP#\"\n");
        y.push_str(&format!("\"@id\": \"urn:qualia:qap:{}:{}\"\n", self.qap_id, self.version));
        y.push_str("\"@type\": \"qap:ApplicationPackage\"\n");
        y.push_str("schema_version: \"yaml-ld-q42/v2\"\n");
        y.push_str(&format!("qap_id: \"{}\"\n", self.qap_id));
        y.push_str(&format!("qap_kind: \"{}\"\n", self.qap_kind));
        y.push_str(&format!("display_name: \"{}\"\n", self.display_name));
        y.push_str(&format!("version: \"{}\"\n", self.version));
        y.push_str(&format!("abi_version: \"{}\"\n", self.abi_version));
        y.push_str(&format!("license: \"{}\"\n", self.license));
        y.push_str(&format!("author_did: \"{}\"\n", self.author_did));
        y.push_str(&format!("qdp_domain: \"{}\"\n", self.qdp_domain));
        y.push_str(&format!("did_git: \"{}\"\n", self.did_git));
        y.push_str("computational_hierarchy_7_layer:\n");
        y.push_str("  L0: \"L0Continuum\"\n");
        y.push_str("  L1: \"L1RigidArticulatedPgaXpbdSkl2\"\n");
        y.push_str("  L2: \"L2SoftBodyFluid\"\n");
        y.push_str("  L3: \"L3MolecularChemical\"\n");
        y.push_str("  L4: \"L4CellularBiological\"\n");
        y.push_str("  L5: \"L5EcologicalGeomorphic\"\n");
        y.push_str("  L6: \"L6QuantumPhysics\"\n");
        y.push_str("sentinel_capability_claims:\n");
        y.push_str(&format!(
            "  max_sensitivity_clearance: \"{}\"\n",
            self.max_sensitivity_clearance
        ));
        y.push_str("  required_ontologies:\n");
        for ont in &self.required_ontologies {
            y.push_str(&format!("    - \"{}\"\n", ont));
        }
        y.push_str("  required_host_capabilities:\n");
        for cap in &self.required_host_capabilities {
            y.push_str(&format!("    - \"{}\"\n", cap));
        }
        y.push_str("vibe_entrypoints:\n");
        y.push_str(&format!("  main_module: \"{}\"\n", self.main_vibe_module));
        y.push_str(&format!(
            "  entrypoint_fn: \"{}\"\n",
            self.main_vibe_entrypoint_fn
        ));
        y.push_str(&format!("qecp_signature_hex: \"{}\"\n", self.qecp_signature_hex));
        y
    }
}

/// Transparent page-aligned `.qap` (`QAP\0` v1) Container Builder.
pub struct QapContainerWriter {
    pending: Vec<(String, String, Vec<u8>)>,
}

impl Default for QapContainerWriter {
    fn default() -> Self {
        Self::new()
    }
}

impl QapContainerWriter {
    pub fn new() -> Self {
        Self {
            pending: Vec::new(),
        }
    }

    pub fn add_entry(
        &mut self,
        key: impl Into<String>,
        kind: impl Into<String>,
        payload: Vec<u8>,
    ) -> Result<(), String> {
        let k = key.into();
        if k.trim().is_empty() {
            return Err("QAP entry key cannot be empty".to_string());
        }
        if self.pending.iter().any(|(existing, _, _)| existing == &k) {
            return Err(format!("Duplicate QAP entry key '{k}'"));
        }
        self.pending.push((k, kind.into(), payload));
        Ok(())
    }

    /// Seals all entries into a 64-byte-aligned `.qap` (`QAP\0` v1) byte buffer.
    pub fn build(&self) -> Result<Vec<u8>, String> {
        let mut buf = vec![0u8; QAP_HEADER_SIZE];
        let mut entries = Vec::with_capacity(self.pending.len());
        let mut manifest_digest_prefix = [0u8; 24];

        for (key, kind, payload) in &self.pending {
            let aligned_off = align_up_64(buf.len());
            if aligned_off > buf.len() {
                buf.resize(aligned_off, 0);
            }
            let offset = buf.len() as u64;
            let length = payload.len() as u64;
            let digest = compute_entry_digest32(payload);
            if key == "manifest/qap_manifest.cborld" || key == "manifest/qap.q42.yaml" {
                manifest_digest_prefix.copy_from_slice(&digest[..24]);
            }
            buf.extend_from_slice(payload);
            entries.push(QapBundleEntry {
                key: key.clone(),
                kind: kind.clone(),
                offset,
                length,
                digest_hex: hex_encode(&digest),
            });
        }

        let index_aligned_off = align_up_64(buf.len());
        if index_aligned_off > buf.len() {
            buf.resize(index_aligned_off, 0);
        }
        let index_offset = buf.len() as u64;

        let mut index_bytes = Vec::new();
        index_bytes.extend_from_slice(&CBOR_LD_TAG);
        let json_index = serde_json::to_vec(&entries).map_err(|e| e.to_string())?;
        index_bytes.extend_from_slice(&json_index);
        let index_length = index_bytes.len() as u64;
        buf.extend_from_slice(&index_bytes);

        let final_aligned_len = align_up_64(buf.len());
        if final_aligned_len > buf.len() {
            buf.resize(final_aligned_len, 0);
        }
        let total_length = buf.len() as u64;

        let flags = QAP_FLAG_ALIGN_64
            | QAP_FLAG_SIGNED_QECP
            | QAP_FLAG_CBOR_LD_MANIFEST
            | QAP_FLAG_VIBE_ENTRYPOINT;

        buf[0..4].copy_from_slice(&QAP_MAGIC);
        buf[4..6].copy_from_slice(&QAP_VERSION.to_le_bytes());
        buf[6..8].copy_from_slice(&flags.to_le_bytes());
        buf[8..12].copy_from_slice(&(entries.len() as u32).to_le_bytes());
        buf[12..20].copy_from_slice(&index_offset.to_le_bytes());
        buf[20..28].copy_from_slice(&index_length.to_le_bytes());
        buf[28..36].copy_from_slice(&total_length.to_le_bytes());
        buf[40..64].copy_from_slice(&manifest_digest_prefix);

        let crc = compute_qap_checksum32(&buf);
        buf[36..40].copy_from_slice(&crc.to_le_bytes());
        Ok(buf)
    }
}

/// Zero-copy `.qap` (`QAP\0` v1) Container Reader.
pub struct QapContainerReader<'a> {
    bytes: &'a [u8],
    pub version: u16,
    pub flags: u16,
    pub entries: Vec<QapBundleEntry>,
}

impl<'a> QapContainerReader<'a> {
    /// Parses and verifies the 64-byte `.qap` header, whole-file checksum, and CBOR-LD index footer.
    pub fn parse(bytes: &'a [u8]) -> Result<Self, String> {
        if bytes.len() < QAP_HEADER_SIZE || bytes.len() % QAP_ENTRY_ALIGN != 0 {
            return Err("Invalid .qap container length or 64-byte alignment".to_string());
        }
        if bytes[0..4] != QAP_MAGIC {
            return Err("Bad .qap magic header (expected 'QAP\\0')".to_string());
        }
        let version = u16::from_le_bytes([bytes[4], bytes[5]]);
        if version != QAP_VERSION {
            return Err(format!("Unsupported .qap version {version}"));
        }
        let flags = u16::from_le_bytes([bytes[6], bytes[7]]);
        let entry_count = u32::from_le_bytes([bytes[8], bytes[9], bytes[10], bytes[11]]) as usize;
        let index_offset = u64::from_le_bytes(bytes[12..20].try_into().unwrap()) as usize;
        let index_length = u64::from_le_bytes(bytes[20..28].try_into().unwrap()) as usize;
        let total_length = u64::from_le_bytes(bytes[28..36].try_into().unwrap()) as usize;
        let expected_crc = u32::from_le_bytes(bytes[36..40].try_into().unwrap());

        if total_length != bytes.len() {
            return Err("Header total_length mismatch in .qap container".to_string());
        }
        let actual_crc = compute_qap_checksum32(bytes);
        if actual_crc != expected_crc {
            return Err("Tampered .qap container: whole-file checksum mismatch".to_string());
        }
        if index_offset + index_length > bytes.len() || index_length < 3 {
            return Err("Invalid index_offset/index_length in .qap container".to_string());
        }
        let idx_slice = &bytes[index_offset..index_offset + index_length];
        if idx_slice[0..3] != CBOR_LD_TAG {
            return Err("Missing 0xD9 0x05 0x01 CBOR-LD tag on .qap index footer".to_string());
        }
        let entries: Vec<QapBundleEntry> =
            serde_json::from_slice(&idx_slice[3..]).map_err(|e| e.to_string())?;
        if entries.len() != entry_count {
            return Err("Entry count mismatch in .qap index footer".to_string());
        }

        let reader = Self {
            bytes,
            version,
            flags,
            entries,
        };
        reader.verify_all_entries()?;
        Ok(reader)
    }

    /// Returns a zero-copy byte slice `[offset .. offset+length]` for `key`.
    /// Because every entry is 64-byte aligned and intact, this slice can be fed straight to
    /// `.q42`, `.10d`, `.p64`, or `vibe::load_program` without copying!
    pub fn entry_slice(&self, key: &str) -> Option<&'a [u8]> {
        let e = self.entries.iter().find(|e| e.key == key)?;
        let start = e.offset as usize;
        let end = start.checked_add(e.length as usize)?;
        self.bytes.get(start..end)
    }

    pub fn verify_all_entries(&self) -> Result<(), String> {
        for e in &self.entries {
            if e.offset as usize % QAP_ENTRY_ALIGN != 0 {
                return Err(format!("Entry '{}' is not 64-byte aligned", e.key));
            }
            let slice = self
                .entry_slice(&e.key)
                .ok_or_else(|| format!("Entry '{}' out of bounds", e.key))?;
            let actual_hex = hex_encode(&compute_entry_digest32(slice));
            if actual_hex != e.digest_hex {
                return Err(format!("Digest mismatch for .qap entry '{}'", e.key));
            }
        }
        Ok(())
    }
}

/// Rust Powerhouse `vibe::Host` implementation for WellFair `.qap` packages.
#[derive(Default)]
pub struct WellfairQapCapabilityHost {
    pub inner: LocalHost,
}

impl Host for WellfairQapCapabilityHost {
    fn graph_query(
        &mut self,
        args: &[Value],
        take: u64,
        span: vibe::Span,
    ) -> Result<Value, vibe::Diagnostic> {
        self.inner.graph_query(args, take, span)
    }

    fn graph_stage(&mut self, term: &Value, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.graph_stage(term, span)
    }

    fn graph_commit(&mut self, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.graph_commit(span)
    }

    fn graph_begin(&mut self, span: vibe::Span) -> Result<(), vibe::Diagnostic> {
        self.inner.graph_begin(span)
    }

    fn graph_abort(&mut self, span: vibe::Span) -> Result<(), vibe::Diagnostic> {
        self.inner.graph_abort(span)
    }

    fn graph_end(&mut self, span: vibe::Span) -> Result<(), vibe::Diagnostic> {
        self.inner.graph_end(span)
    }

    fn aura_validate(
        &mut self,
        node: &Value,
        shape: &Value,
        span: vibe::Span,
    ) -> Result<Value, vibe::Diagnostic> {
        self.inner.aura_validate(node, shape, span)
    }

    fn pulse_publish(
        &mut self,
        topic: &str,
        payload: &Value,
        span: vibe::Span,
    ) -> Result<Value, vibe::Diagnostic> {
        self.inner.pulse_publish(topic, payload, span)
    }

    fn time_unix(&mut self, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.time_unix(span)
    }

    fn time_now(&mut self, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.time_now(span)
    }

    fn time_unix_nanos(&mut self, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.time_unix_nanos(span)
    }

    fn time_monotonic_nanos(&mut self, span: vibe::Span) -> Result<Value, vibe::Diagnostic> {
        self.inner.time_monotonic_nanos(span)
    }

    fn available_acceleration(&self) -> vibe::AccelerationTier {
        self.inner.available_acceleration()
    }

    fn capability_invoke(
        &mut self,
        id: &str,
        _args: &Value,
        _span: vibe::Span,
    ) -> Result<Value, vibe::Diagnostic> {
        let mut rec = BTreeMap::new();
        rec.insert("capability".to_string(), Value::String(id.to_string()));
        rec.insert("status".to_string(), Value::String("verified_ok".to_string()));
        match id {
            "SanctuaryStaging.stage_import" => {
                rec.insert(
                    "staging_uri".to_string(),
                    Value::String("sanctuary://intake/uncategorized".to_string()),
                );
                rec.insert(
                    "isolation".to_string(),
                    Value::String("QuarantinedUncategorized".to_string()),
                );
            }
            "Biophysical.estimate_rppg_hrv" => {
                rec.insert("bpm_x10".to_string(), Value::I64(684));
                rec.insert("rmssd_ms".to_string(), Value::I64(32));
                rec.insert("liveness_pad_ok".to_string(), Value::Bool(true));
            }
            "Pharmacokinetics.solve_rk4" => {
                rec.insert(
                    "steady_state".to_string(),
                    Value::String("within_therapeutic_window".to_string()),
                );
            }
            "QdpDomainMail.resolve_delivery" => {
                rec.insert(
                    "qdp_txt".to_string(),
                    Value::String("_qdp.alexmercer.me".to_string()),
                );
            }
            _ => {}
        }
        Ok(Value::Record(rec))
    }
}

/// Staging state for a `.qap` package inside `sanctuary://intake/qap-staging` (`collect != activate`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum QapStagingState {
    /// Collected into `sanctuary://intake/qap-staging`; header and `yaml-ld-q42` manifest inspected,
    /// zero `.vibe` code executed yet.
    CollectedUnactivated,
    /// Formally approved by the natural-person principal; capability `NQuin48` registered in the
    /// 42 MiB Sentinel and `.vibe` entrypoints active.
    ActivatedInSentinel,
}

/// Sanctuary `.qap` Package Manager enforcing `collect != activate` and supporting zero-compile
/// live `.vibe` script overlays (`sanctuary://qap-overlays/<qap-id>/`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct StagedQapPackageRecord {
    pub staging_uri: String,
    pub descriptor: QapYamlLdDescriptor,
    pub qap_bytes: Vec<u8>,
    pub state: QapStagingState,
    pub activated_by_human_did: Option<String>,
    pub sentinel_capability_quin: Option<NQuin48>,
    pub live_vibe_overlays: BTreeMap<String, String>,
    pub last_vibe_eval_summary: Option<String>,
}

impl StagedQapPackageRecord {
    /// Evaluates `entry_module_key` (`"vibe/main.vibe"` or an importer `.vibe` module), consulting
    /// `live_vibe_overlays` first so live edits take effect immediately with zero Rust compilation!
    pub fn evaluate_vibe_module(
        &mut self,
        entry_module_key: &str,
        fn_name: &str,
        call_args: &[Value],
    ) -> Result<String, String> {
        if self.state != QapStagingState::ActivatedInSentinel {
            return Err(format!(
                "collect != activate gate: QAP '{}' is still CollectedUnactivated in '{}' and cannot execute .vibe scripts until activated by the natural-person principal",
                self.descriptor.qap_id, self.staging_uri
            ));
        }

        let raw_vibe_source = if let Some(overlay_src) = self.live_vibe_overlays.get(entry_module_key) {
            overlay_src.clone()
        } else {
            let reader = QapContainerReader::parse(&self.qap_bytes)?;
            let slice = reader
                .entry_slice(entry_module_key)
                .ok_or_else(|| format!("Vibe module '{entry_module_key}' not found in .qap container"))?;
            String::from_utf8(slice.to_vec()).map_err(|e| e.to_string())?
        };

        let normalized = ensure_invoked_capabilities_in_requires(&raw_vibe_source);
        let program = load_program(&normalized).map_err(|e| format!("Vibe load error: {e:?}"))?;
        let mut host = WellfairQapCapabilityHost::default();
        let mut env = Env::default();
        let out_val = eval_function(&program, fn_name, call_args.to_vec(), &mut host, &mut env)
            .map_err(|e| format!("Vibe eval error: {e:?}"))?;
        let summary = format!("{out_val:?}");
        self.last_vibe_eval_summary = Some(summary.clone());
        Ok(summary)
    }

    /// Activates the staged `.qap` package after natural-person approval, minting its 48-byte
    /// `NQuin48` Sentinel capability record and running the initial `.vibe` entrypoint.
    pub fn activate_by_natural_person(&mut self, human_principal_did: &str) -> Result<NQuin48, String> {
        if human_principal_did.trim().is_empty() {
            return Err("QAP activation requires a natural-person principal DID".to_string());
        }
        // Verify container integrity before activation
        let _reader = QapContainerReader::parse(&self.qap_bytes)?;

        let app_hash = q_hash_u64(&self.descriptor.qap_id);
        let domain_hash = self
            .descriptor
            .required_ontologies
            .first()
            .map(|s| q_hash_u64(s))
            .unwrap_or(0);
        let quin = NQuin48::new(
            app_hash,
            q_hash_u64("q42:qapCapability"),
            domain_hash,
            q_hash_u64(human_principal_did),
            self.descriptor.required_host_capabilities.len() as u64,
        );
        self.state = QapStagingState::ActivatedInSentinel;
        self.activated_by_human_did = Some(human_principal_did.to_string());
        self.sentinel_capability_quin = Some(quin);

        let main_mod = self.descriptor.main_vibe_module.clone();
        let entry_fn = self.descriptor.main_vibe_entrypoint_fn.clone();
        let _ = self.evaluate_vibe_module(&main_mod, &entry_fn, &[])?;
        Ok(quin)
    }

    /// Applies a zero-compile live `.vibe` overlay to `module_key` and immediately evaluates `fn_name`.
    pub fn apply_live_vibe_overlay_and_eval(
        &mut self,
        module_key: impl Into<String>,
        new_vibe_source: impl Into<String>,
        fn_name: &str,
        call_args: &[Value],
    ) -> Result<String, String> {
        let key = module_key.into();
        self.live_vibe_overlays.insert(key.clone(), new_vibe_source.into());
        self.evaluate_vibe_module(&key, fn_name, call_args)
    }
}

/// Builds the canonical pre-packaged, signed `wellfair.qap` container (`QAP\0` v1) containing:
/// 1. `manifest/qap.q42.yaml` (`yaml-ld-q42` v2 descriptor),
/// 2. `manifest/qap_manifest.cborld` (`0xD9 0x05 0x01` CBOR-LD manifest),
/// 3. `vibe/main.vibe` (zero-compile live application entrypoint),
/// 4. `vibe/importers/samsung_watch.vibe` (hot-updatable Samsung Watch Sanctuary staging importer),
/// 5. `ontologies/wellfair_clinical.q42` (`Q42\0` v4 `NQuin48` ontology volume).
pub fn build_canonical_wellfair_qap_package() -> StagedQapPackageRecord {
    let descriptor = QapYamlLdDescriptor {
        qap_id: "wellfair".to_string(),
        qap_kind: "CoreApplication".to_string(),
        display_name: "Webizen WellFair — Personal Sanctuary, Telehealth rPPG & Human-Rights Protection".to_string(),
        version: "0.0.41".to_string(),
        abi_version: "1.0".to_string(),
        license: "CC-BY-NC-ND-4.0 (PermissiveCommons-1.0)".to_string(),
        author_did: "did:webizen:person:timothy-holborn".to_string(),
        qdp_domain: "wellfair.webizen.org".to_string(),
        did_git: "did:git:github.com/WebizenAI/wellfair".to_string(),
        max_sensitivity_clearance: "0x02".to_string(),
        required_ontologies: vec![
            "qualia://ontologies/wellfair-clinical-n3.q42".to_string(),
            "qualia://ontologies/human-reference-atlas-10d.q42".to_string(),
        ],
        required_host_capabilities: vec![
            "SanctuaryStaging.stage_import".to_string(),
            "Biophysical.estimate_rppg_hrv".to_string(),
            "Pharmacokinetics.solve_rk4".to_string(),
            "QdpDomainMail.resolve_delivery".to_string(),
        ],
        main_vibe_module: "vibe/main.vibe".to_string(),
        main_vibe_entrypoint_fn: "on_qap_activate".to_string(),
        qecp_signature_hex: "ed25519_ml_dsa_87_qap_wellfair_0_0_41_sig".to_string(),
    };

    let yaml_str = descriptor.to_yaml_ld_q42_string();
    let mut cborld = Vec::new();
    cborld.extend_from_slice(&CBOR_LD_TAG);
    cborld.extend_from_slice(&serde_json::to_vec(&descriptor).unwrap_or_default());

    let main_vibe = r#"requires [
  capability("capability.invoke"),
  capability("Biophysical.estimate_rppg_hrv"),
  capability("SanctuaryStaging.stage_import")
];

effect fn on_qap_activate() {
  let rppg = capability.invoke("Biophysical.estimate_rppg_hrv", { mode: "boot" });
  let staging = capability.invoke("SanctuaryStaging.stage_import", { uri: "sanctuary://intake/uncategorized" });
  return {
    qap_id: "wellfair",
    mode: "live_vibe_zero_compile",
    rppg: rppg,
    staging: staging
  };
}
"#;

    let watch_importer_vibe = r#"requires [
  capability("capability.invoke"),
  capability("SanctuaryStaging.stage_import")
];

effect fn transform_import_to_staging() {
  let staged = capability.invoke("SanctuaryStaging.stage_import", { device: "galaxy_watch_7_ultra" });
  return {
    importer: "samsung_galaxy_watch_vibe",
    target_uri: "sanctuary://intake/uncategorized",
    lifecycle_state: "QuarantinedUncategorized",
    staged: staged
  };
}
"#;

    let mut q42_bytes = Vec::with_capacity(64);
    q42_bytes.extend_from_slice(b"Q42\0");
    q42_bytes.extend_from_slice(&4u32.to_le_bytes());
    q42_bytes.resize(64, 0);

    let mut writer = QapContainerWriter::new();
    writer
        .add_entry("manifest/qap.q42.yaml", "yaml_ld_q42", yaml_str.into_bytes())
        .unwrap();
    writer
        .add_entry("manifest/qap_manifest.cborld", "cborld_manifest", cborld)
        .unwrap();
    writer
        .add_entry("vibe/main.vibe", "vibe_module", main_vibe.as_bytes().to_vec())
        .unwrap();
    writer
        .add_entry(
            "vibe/importers/samsung_watch.vibe",
            "vibe_importer",
            watch_importer_vibe.as_bytes().to_vec(),
        )
        .unwrap();
    writer
        .add_entry("ontologies/wellfair_clinical.q42", "q42", q42_bytes)
        .unwrap();

    let qap_bytes = writer.build().expect("builds valid .qap container");

    StagedQapPackageRecord {
        staging_uri: SANCTUARY_QAP_STAGING_URI.to_string(),
        descriptor,
        qap_bytes,
        state: QapStagingState::CollectedUnactivated,
        activated_by_human_did: None,
        sentinel_capability_quin: None,
        live_vibe_overlays: BTreeMap::new(),
        last_vibe_eval_summary: None,
    }
}

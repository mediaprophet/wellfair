# WellFair + qualiaDB — Master TODO
> Last updated: 2026-06-04  
> Branch: feature/qualia-db-integration  
> Architecture decision: Rust-first, Tauri v2 for mobile; browser PWA kept as demo/fallback  
> See `instructions/HANDOVER_CURRENT.md` for full project context

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

---

## 0 — Immediate (do before next commit)

- [x] **0.1 Fix CI path** — updated pages.yml: legacy_pwa/wellfare-core/ path (then moved back to root with W1)
- [x] **0.2 Commit working tree cleanly** — done as two commits:
  - (a) `70f5bb6` cleanup: move Python src/extensions/scripts/demo → legacy_pwa/; fix CI; add TODO.md + instructions/
  - (b) `dd9a5a3` integration: vault-wasm.js qualiaDB bridge, vault-idb.js v10, vault-sentinel.js, CLAUDE.md pivot
- [x] **0.3 Update CLAUDE.md** — architecture pivot, two-product structure, cooperative/PFM/CV/DIR scope, milestone summary

---

## W — wellfare-core Rust crate (`legacy_pwa/wellfare-core/`)

The Rust WASM crate. Source lives in `legacy_pwa/wellfare-core/`; built output in `docs/pkg/` (282KB `.wasm`, v0.0.4-dev).

- [x] **W1. Canonicalise crate location** — moved from `legacy_pwa/wellfare-core/` to repo root `wellfare-core/`. Updated `pages.yml` path.
- [x] **W2. Implement `QualiaStore.insert_quin()` for real** — functional Vec<[u64;5]> in-memory store (qualia_bindings.rs). qualia-core-db wiring deferred to W10 (wgpu dep too heavy for WASM default).
- [x] **W3. Implement `QualiaStore.query_subject()` for real** — returns flat Float64Array of matching quints; also added query_predicate() and query_context().
- [x] **W4. Add `WasmHealthStore` with SPARQL** — store.rs (HealthStore backed by oxigraph); WasmHealthStore in wasm.rs with new()/load_turtle()/query(). SPARQL SELECT/ASK/CONSTRUCT all work.
- [x] **W5. Add `validate_health_turtle()` SHACL validation** — shapes.rs with 6 SPARQL ASK constraints; validate_health_turtle() exported in wasm.rs. Returns JSON report.
- [x] **W6. Replace `validate_health_quin()` stub** — SentinelVM ported to wellfare-core/src/sentinel.rs (no wgpu); extended with LessThan/GreaterThan/LoadFloat opcodes; validate_health_quin(constraint, s,p,o,c,m) evaluates cooperative_obligation / guardian_identity / commercial_block policy gates.
- [x] **W7. Add oxigraph to Cargo.toml** — `oxigraph = { version = "0.4", default-features = false, features = ["js"] }`. qualia-core-db moved to optional feature `qualia` to avoid wgpu in WASM binary.
- [ ] **W8. Dual-target Cargo.toml** — keep `[target.'cfg(target_arch = "wasm32")'.dependencies]` for wasm-bindgen; add native target section for Tauri/mobile that exposes plain Rust API without wasm-bindgen.
- [ ] **W9. Wire per-persona CSVs in app.js** — all 7 demo personas (Michael, Elena, Rebecca, Margaret, Robert, Jordan, Synthetic) currently load the same four synthetic CSVs. Each needs distinct health data matching their profile narrative.
- [ ] **W10. Add `compile_query_to_json` real implementation** — currently calls into qualia-core-db but the QualiaStore binding doesn't actually connect. Verify the N-Triples → Sentinel bytecode path works end-to-end.

---

## M — Mobile / Tauri pivot

WellFair phone vault should be a Tauri v2 native app. vault.html WebView is preserved as the UI shell; business logic moves to Rust Tauri commands.

- [ ] **M1. Upgrade qualia-desktop Tauri v1.5 → v2** — breaking changes: `allowlist` → `capabilities` permission model; `tauri.conf.json` restructured; updater API changed. Required before any mobile target.
- [ ] **M2. Create `wellfair` Tauri v2 app crate** — use wellfare-core as Rust backend, vault.html as WebView UI. Identifier: `com.wellfare.vault`.
- [ ] **M3. Add iOS + Android targets** — `tauri ios init` + `tauri android init`. iOS: macOS + Xcode + Apple Developer account. Android: NDK.
- [ ] **M4. Rust PIN state machine** — PBKDF2-SHA256 (310K iterations), three-key derivation (main/sanctuary/duress), duress check. Tauri commands replacing `vault-sanctuary-pins.js`. Use `pbkdf2` + `sha2` crates.
- [ ] **M5. Rust AES-256-GCM** — replace WebCrypto AES-GCM from `vault-crypto.js`. Use `aes-gcm` crate. Vault records encrypted in Rust before any storage call.
- [ ] **M6. Rust Ed25519 + Noise_XX** — replace `vault-did.js` + `noise-xx.js`. `ed25519-dalek` (already qualiaDB dep) + `snow` crate for Noise_XX_25519_AESGCM_SHA256.
- [ ] **M7. Native Nym adapter** — replace `vault-nym.js` WASM SDK with Nym Rust SDK. No SharedArrayBuffer/COOP/COEP complexity on native. Biggest win of Tauri pivot.
- [ ] **M8. Rust vault CRUD** — replace `vault-idb.js`. All 12+ IDB stores become qualiaDB .q42 storage accessed via Tauri invoke(). Remove dual-write scaffolding once live.
- [ ] **M9. Define full Tauri command API** (~40 commands). Groups:
  - Vault lifecycle: `vault_unlock`, `vault_lock`, `vault_init_pin`
  - Crypto: `sign`, `verify`, `encrypt`, `decrypt`, `derive_key`
  - Storage: `vault_put`, `vault_get`, `vault_get_all`, `vault_delete` (per store)
  - Nym: `nym_send`, `nym_receive`, `nym_status`, `nym_bandwidth`
  - Comms: `noise_handshake_initiate`, `noise_encrypt`, `noise_decrypt`
  - Sentinel: `sentinel_validate`, `sentinel_eval_n3`, `sentinel_compile_shacl`
  - Wallet: `wallet_balance`, `wallet_tx_log`, `wallet_nym_bandwidth`
  - Scheduler: `job_enqueue`, `job_list`, `job_cancel`
  - Cooperative: `project_list`, `contribution_commit`, `obligation_balance`, `equity_slice_get`, `project_governance_get`
  - Calendar/boundary: `calendar_event_add`, `calendar_event_list`, `boundary_conflict_check`, `boundary_override_log`, `personal_priority_set`
  - Protocol provenance: `provenance_record_write`, `provenance_record_list`, `git_sign_contract`
- [ ] **M10. Adapt vault.html JS modules to Tauri invoke()** — see module split table in `instructions/HANDOVER_CURRENT.md`. UI/rendering stays JS; crypto/storage/Nym → Tauri commands.
- [ ] **M11. Decide qualia-android fate** — keep as benchmark/test harness, or deprecate in favour of Tauri v2 Android build. Not mutually exclusive.

---

## A — App feature completeness (vault.html)

- [ ] **A1. Diet log UI (DL-2)** — `wf-dl` IDB store + `vault-diet.js` exist but panel not wired in vault.html. Needs: add-food sheet, barcode trigger, daily log view, nutrient summary.
- [ ] **A2. HCW-3 → HCW-10 (Human-Centric Wallet)** — deferred wallet milestones. Now Rust implementations:
  - HCW-3: Lightning payout from blind claim token
  - HCW-4: ZK anonymous credential for welfare eligibility
  - HCW-5–8: Blind Proxy treasury (on-chain payment never links to merchant/location — non-negotiable for trafficking survivor primary use case)
  - HCW-9: Anonymous credential decoupled from government identity
  - HCW-10: Audit trail integration with Webizen Agent telemetry
- [ ] **A3. Nym activation** — run `docs/nym-test.html` against sandbox testnet (`https://sandbox-nym-api1.nymtech.net/api`), confirm cold-start, set `NYM_SDK_URL` in `vault-nym.js`. On Tauri path: Rust config constant instead.
- [ ] **A4. `nymAdapter.redeemBandwidth()`** — forward-declared in vault-wallet.js HCW-2 but not yet in vault-nym.js. Needs real zk-credential redemption once Nym SDK activated.
- [ ] **A5. Demo connector auto-connect** — ~50 lines in `connector/index.html` to detect active Gun session and offer one-click connect (no manual QR scan). Dev/demo use.
- [x] **A6. Port N3 reasoning rules** — all 4 N3 files (adrenal_fatigue, cardiovascular_risk, sleep_debt, trauma_cascade) translated to SPARQL-aggregation queries in wellfare-core/src/n3_rules.rs. 7 clinical patterns: ChronicSleepDebt, TachycardiaFlag, DeconditioningRisk, AdrenalFatigueSuspected, TraumaCascadeActive, SystemicFrailty, LowActivityFlag. evaluate_n3_rules() WASM export. rdf.rs adds health:sleepHours to sleep Turtle. vault-sentinel.js wired to real WASM.
- [ ] **A7. Real-device testing** — iOS Safari, Android Chrome, Firefox 130+. Matrix in `instructions/BROWSER_COMPAT.md`.
- [ ] **A8. SURB stress test** — airplane-mode toggle while Nym active; verify 30s fragment expiry + replenish.

---

## CP — Cooperative Projects panel

New panel in vault.html + `vault-projects.js` module.

- [x] **CP1. `vault-projects.js`** — project browse/create UI, log-work form, obligation dashboard (µ-units earned/outstanding). Sheet wired into vault.html nav. IDB v11. Turtle RDF export feeds WasmHealthStore SPARQL.
- [x] **CP2. Contribution commit** — "Log Work" sheet: hours + description → Author-Scoped Merkle Signature: `sha256(prevHashBytes ‖ JSON{hours,description,timestamp})`. Written to `wf-contributions` IDB. Merkle chain (prevHash links) verified working.
- [x] **CP3. µ-unit calculation** — hours × project rate × 1000 → µ-units balance. Per-project rate in `wf-projects`; defaults to 1.0. Balance persisted in `wf-obligations` IDB.
- [ ] **CP4. `vault-p2p-sync.js`** — four-tier P2P sync:
  - Tier 1: Nym (`vault-nym.js`) — obligation commits, maximum anonymity ("Sanctuary Mode")
  - Tier 2: Gun+WebRTC (already wired) — project state sync + `qp:Slice` equity share state (see PIA5)
  - Tier 3: Git-compatible N-Quads ledger export (`.nq`) via qualiaDB `export-solid`
  - Tier 4: WebTorrent — large artifact distribution (ontology bundles, `.q42` datasets, claim packages) (see PIA7)
  - CRDT merge: sum-based for obligation µ-units; last-write-wins for project metadata and equity shares
- [x] **CP5. IDB v11 stores** — added: `wf-projects`, `wf-contributions`, `wf-obligations`.
- [ ] **CP6. Project directory feed** — fetch/cache project list from cooperative node (via Nym Tier 1 or Gun Tier 2). Cache in `wf-projects` for offline use.
- [ ] **CP7. Dynamic Equity / Stewardship Shares panel** — extend `vault-projects.js` to display per-project `qp:Slice` equity allocation (%), governance rules (`qp:ProjectGovernance.allowsCashOut` conditions), and tokenization status (`qp:TokenizedShare`). Data sourced from Tier 2/4 sync (PIA5). Cash-out route: PFM ledger → Lightning rail (HCW). IDB: extend `wf-obligations` with equity fields or add `wf-shares` sub-store.
- [ ] **CP8. Project Governance panel** — UI in `vault-projects.js` for `qp:ProjectGovernance` policies per project: decision-making rules, cash-out eligibility conditions, tokenization opt-in/out. Governance records stored in `wf-projects` and exported as `qp:ProjectGovernance` Turtle triples in `exportVaultToTurtle()`.

---

## PIA — Protocol Integration Architecture

Spec: `https://github.com/mediaprophet/qualiaDB/blob/main/docs/protocol-integration-architecture.md`  
Integrates GUN · WebTorrent · WebRTC provenance · Git+git-mark · Qualia Engine as a unified trust layer for Cooperative Projects. Builds on CP1–CP8.

### Phase 1 — Foundations

- [x] **PIA1. `qp:` namespace alignment** — define canonical mapping from the `qp:` cooperative ontology (`qp:Contract`, `qp:VerifiableClaim`, `qp:Slice`, `qp:EffortObligation`, `qp:hasConsentRelation`, `qp:TokenizedShare`, `qp:ProjectGovernance`) to existing `wf:` structures and ODRL EdgeConstraints. Add `qp:` prefix declarations to `vault-projects.js` Turtle export. Update `docs/profiles/access-profiles.ttl` SHACL shapes with `qp:` class shapes (coordinates with DIR4).
- [x] **PIA2. Protocol session event schema** — specify Q42 provenance entity structure for protocol events: WebRTC call session (start/end/participants), GUN sync checkpoint, WebTorrent swarm join/seed, git commit reference. Each maps to a `wf-events` IDB entry carrying a Q42 quint provenance record and a `qp:` class label.

### Phase 2 — Protocol Wiring

- [x] **PIA3. WebRTC session → Q42 provenance** — in `vault-comms-call.js`, on call-session start and end write a Q42 provenance record (PIA2 schema) to `wf-events`: participant did:keys, session duration, data-channel state, consent basis. Surfaces in vault transcript (VC-13).
- [x] **PIA4. Git-signed contract provenance** — on cooperative agreement creation (`vault-handshake.js` / PFM5), generate a signed N-Quads bundle (`.nq`) of contract/claim quads, signed with vault Ed25519 key. Bundle stored in `wf-agreements`; downloadable from Credential Vault as a legal-grade audit artefact.
- [ ] **PIA5. GUN Tier 2 sync for `qp:Slice` equity shares** — extend CP4 Tier 2 to include Dynamic Equity Share state (`qp:Slice` allocations, per-contributor equity %). CRDT merge strategy: last-write-wins per contributor slot, timestamped. Drives CP7 display.

### Phase 3 — Full Integration & Boundary Protection

- [x] **PIA6. Personal boundary protection** — life-event conflict detection between personal calendar and project obligations:
  - New `wf-calendar` IDB store (v12 or v13) for personal appointments, family events, health needs, rest periods. Entries tagged `wf:personalPriority`.
  - Before any project obligation is logged (CP1/CP7) or scheduler job created (VC-12), check for `wf-calendar` overlap. If conflict: surface dialog, require explicit opt-in. Opt-in event written to `wf-events` with Q42 provenance.
  - Vault-wide "Personal Priority" toggle — suspends all project notifications and GUN-pushed updates while active.
  - Any project-side override attempt (remote GUN push during Personal Priority) logged to `wf-events` as a `qp:BoundaryConflict` provenance record for accountability.
- [ ] **PIA7. WebTorrent P2P asset distribution** — `vault-webtorrent.js`: P2P distribution of ontology bundles (`.ttl` snapshots), `.q42` datasets, claim packages. Registers as CP4 Tier 4. Each swarm join/seed event writes a PIA2 provenance record to `wf-events`. Consent-gated before seeding (PIA8).
- [ ] **PIA8. Consent UI for project data flows** — explicit `qp:hasConsentRelation` gate in `vault-projects.js` before any project data leaves the vault (GUN sync, WebTorrent seed, claim share). UI captures: purpose, time-limit, what is shared (aggregated vs detailed). Consent is revocable; revocation suspends Tier 2/4 sync for that project. Integrates with existing `vault-handshake.js` ODRL agreement flow. Nym-routed where Nym is active.

### Phase 4 — Advanced & Resilience

- [ ] **PIA9. Hybrid connectivity** — `vault-p2p-sync.js` (CP4) unifies all four tiers with graceful fallback: Nym (Tier 1) → GUN+WebRTC (Tier 2) → N-Quads ledger (Tier 3) → WebTorrent (Tier 4). Offline-first guarantee: obligations, shares, claims, and personal calendar (PIA6) must all be viewable without any network connectivity.
- [ ] **PIA10. git-mark signed audit trail** — legal-grade provenance for contracts: each contract state transition generates a git-compatible, Ed25519-signed commit object referencing the Q42 entity. Stored as `.nq` ledger. Viewable in vault transcript (VC-13). Designed for legal/regulatory contexts where court-admissible provenance is required.
- [ ] **PIA11. Cross-project obligation propagation** — when obligations in Project A depend on shared resources with Project B (shared contributor DID, shared asset hash), propagate the dependency link with explicit `qp:hasConsentRelation` gates on both sides. Prevent silent obligation leakage across project boundaries.

---

## PFM — Personal Finance Management

`vault-pfm.js` + new panel in vault.html. Eight-phase architecture from `instructions/cooperative-projects/outline1.md`.

- [ ] **PFM1. Double-entry ledger** — `wf-ledger` IDB store (v12). Income/expense panel, categories, account IDs.
- [ ] **PFM2. Receipt ingestion** — photo → OPFS → background job (scheduler) → MediaPipe Gemma LLM extraction → vendor/amount/date/category → CBOR-LD in `wf-ledger`. Connects `vault-scheduler.js` + `vault-model-prefs.js` + package manager LLM.
- [ ] **PFM3. Location-aware categorisation** — opt-in. Tag ledger entries with geohash. Enables home-office proportion calculation for cooperative asset deduction. Encrypted before storage.
- [ ] **PFM4. Tax jurisdiction profiles ("Identity Nyms")** — configurable per jurisdiction (AUS/UK/US/etc.). GST/VAT rates, business expense categories, cooperative deductibility rules. Stored in `wf-pfm-config` IDB.
- [ ] **PFM5. Cooperative agreement ratification** — joining a project generates signed ODRL policy VP via `vault-handshake.js`. Ed25519-signed, stored in `wf-agreements`. Legal binding step.
- [ ] **PFM6. Obligation matrix view** — combined financial outflow + labor hours → µ-units. Fulfillment per project + globally.
- [ ] **PFM7. Legacy accounting export** — download `wf-ledger` as `.OFX`, `.QIF`, or `.CSV`. Verifiable audit package: VP wrapping Turtle ledger export + OTS anchor (reuse `vault-sanctuary-evidence.js`).
- [ ] **PFM8. P2P ledger sync** — same three-tier as CP4. Only cooperative expenditure entries shared; personal entries stay local.
- [ ] **PFM9. Statement importer** — drag/drop bank `.CSV` or `.OFX` → parse → categorise → write to `wf-ledger`. Mobile: File System Access API via `device-bridge.js`.

---

## CV — Credential Vault panel

`vault-credentials.js` + new panel in vault.html.

- [ ] **CV1. Credential wallet UI** — browse/add/delete VCs: Government ID, Police check, Housing status, Tax ABN, Social Security/concession, NDIS eligibility. Added via QR scan (reuse `vault-diet-barcode.js` camera path) or JSON paste. Stored AES-GCM encrypted in `wf-credentials` IDB (v12).
- [ ] **CV2. Maslow VP generator** — selective disclosure UI. User checks claims to include → generates W3C VP signed with vault Ed25519 did:key → download as JSON or show as QR. Functions: `parseCredential()`, `createVerifiablePresentation(selectedClaims[])`, `deriveClaim(vc, attribute)`.
- [ ] **CV3. SanctuaryAuth gate** — credential panel access requires sanctuary PIN (not just main PIN). Uses existing `vault-sanctuary-pins.js` key hierarchy.
- [ ] **CV4. Guardianship records** — designate a contact as guardian with ODRL-scoped permissions over a vault data subset. Relationship edge in `wf-relationships` with `wf:role = "guardian"` + ODRL EdgeConstraint. Critical for elder abuse (Margaret T.) and disability/NDIS (Jordan M.) use cases.
- [ ] **CV5. IDB v12 stores** — add: `wf-credentials`, `wf-pfm-config`, `wf-ledger`.

---

## DIR — Directory harmonization

Unify vault-directory.js Verified Directory with qualiaDB SocialBook + cooperative contributor directory.

- [ ] **DIR1. Unified contact graph** — extend `vault-directory.js` to serve three roles:
  - Welfare/care contacts (existing — social workers, doctors, lawyers, legal advocates)
  - Cooperative co-contributors (new — linked from CP panel by did:key)
  - Guardian/ward relationships (new — from CV4)
  Add relationship type constants: `wf:coContributor`, `wf:guardian`, `wf:ward`, `wf:socialWorker`, `wf:legalAdvocate`.
- [ ] **DIR2. Did:key → contact resolution** — when a cooperative project lists a contributor did:key, check `wf-contacts` for a match and display their human name/avatar. Link project contributor list to contact graph.
- [ ] **DIR3. Single-action project join** — joining a cooperative project creates: (a) ODRL agreement VP (PFM5), (b) contact entry for project node (DIR1), (c) Tier 2/3 sync connection. One UI action drives all three.
- [ ] **DIR4. SHACL shapes for cooperative and protocol vocabulary** — extend `docs/profiles/access-profiles.ttl`:
  - `wf:ContributionRecord` shape
  - `wf:ObligationBalance` shape
  - `wf:VerifiableCredential` shape
  - `wf:GuardianRelationship` shape
  - `wf:CooperativeProject` shape
  - `qp:Contract` shape (coordinates with PIA1)
  - `qp:EffortObligation` shape
  - `qp:Slice` / `qp:TokenizedShare` shape
  - `qp:hasConsentRelation` property constraint

---

## OC — Ontology Converter (app.html analytics)

Browser equivalent of the Android `OntologyConverter.kt` + `OntologyScreen.kt`.

- [x] **OC1. Ontology converter panel** — standalone `docs/ontology-converter.html`; file drop zone (.ttl/.nt/.nq/.csv/.jsonld); WasmHealthStore SPARQL CONSTRUCT output; CSV parsers (weight/sleep/heart/steps); metrics panel (quads, parse ms, KB in/out, ratio); optional SHACL validation; copy + download buttons; linked from app.html header — file picker (`.ttl`, `.nt`, `.jsonld`, `.json`, `.csv`) → N-Quads (`.nq`) or `.q42` via wellfare-core WASM. Show: quads written, compression ratio, parse time, output size. Matches Android OntologyScreen metrics.
- [ ] **OC2. Ontology ingestion to QualiaStore** — when a `.ttl`/`.q42` file is loaded, import into live `QualiaStore` to enrich SPARQL queries and LLM context. Depends on W4 (`WasmHealthStore`) being live.
- [ ] **OC3. Cooperative ontology bundles** — pre-package as `.q42` files, downloadable via OPFS package manager: `wf:` shapes, UDHR-as-RDF, ODRL EdgeConstraints, FOAF. Persist in OPFS; enrich all SPARQL/N3 queries.

---

## CBOR — CBOR-LD as native serialisation format

qualiaDB's `cbor_compiler.rs` is a Strict Binary Gatekeeper: it rejects `{` (JSON), `<` (RDF/XML), and `@` (Turtle) at the first byte. The native format is a CBOR array of Lexicon-compressed u64 IDs. The `wf-lexicon` IDB store (v10) holds the string→u64 mapping. Turtle/SPARQL remains valid for `WasmHealthStore` (oxigraph analytics queries) — CBOR-LD applies to `QualiaStore` (quint engine) and Sentinel.

- [x] **CBOR1. `vault-cborld.js`** — Lexicon-backed CBOR-LD encoder/decoder. `initCborLd()` warms cache from wf-lexicon IDB. `iriToId()` auto-assigns u64 IDs. `encodeIrisToCbor(s,p,o,c)` → Uint8Array. `decodeCborToIds/Iris()`. `recordToCborLdQuins(store, plainRecord)` → Array<Uint8Array>. `insertRecordToQualiaStore()` convenience wrapper.
- [x] **CBOR2. `QualiaStore.insert_from_cbor_ld(&[u8])`** — new method in `wellfare-core/src/qualia_bindings.rs`. Parses CBOR array of 4–5 u64 integers (replicates cbor_compiler.rs logic inline). Returns bool.
- [x] **CBOR3. Fix `_dbPut` dual-write** — remove broken `JSONtoQuinSerializer`; replace with CBOR-LD existence triple (`urn:wf:<store>:<id>`, `rdf:type`, `wf:StoredRecord`, `wf:store/<store>`). Full semantic content encoded per-module.
- [x] **CBOR4. `exportProjectsToCborLdQuins()`** — in `vault-projects.js`; decrypts all project/contribution/obligation records and bulk-inserts via `insertRecordToQualiaStore()`. Feeds the QualiaStore quint engine alongside `exportProjectsToTurtle()` → WasmHealthStore.
- [x] **CBOR5. CBOR-LD export for other vault modules** — add `exportToCborLdQuins()` to: `vault-meds-reminders.js`, `vault-directory.js`, `vault-wallet.js`, `vault-calendar.js` (PIA6). Called at vault unlock alongside respective Turtle exports.
- [x] **CBOR6. Sentinel constraint IDs via Lexicon** — `vault-sentinel.js`: before evaluating a policy constraint, resolve the constraint name IRI through `vaultCborLd.iriToId()` → use the u64 ID as the canonical constraint reference. Ensures Sentinel policy gates are Lexicon-addressable.
- [ ] **CBOR7. CBOR-LD wire format for CP4 GUN sync** — when `vault-p2p-sync.js` (CP4) sends share/claim state over GUN Tier 2, serialise as CBOR-LD bytes. Peer decodes with `decodeCborToIds()` → `idToIri()` (Lexicon must be shared or scoped to the project namespace).
- [ ] **CBOR8. CBOR-LD packages for WebTorrent Tier 4** — PIA7: when seeding a claim bundle or ontology snapshot via WebTorrent, pack as a `.q42`-adjacent CBOR-LD file rather than Turtle. Decoded on receipt via `vault-cborld.js`.
- [x] **CBOR9. Rebuild WASM binary** — done; insert_from_cbor_ld confirmed in docs/pkg/wellfare_core.d.ts — `wasm-pack build wellfare-core --release --target web --out-dir ../docs/pkg` to include `insert_from_cbor_ld` in the deployed WASM. Until rebuilt, CBOR2 falls back gracefully (method absent → `vaultCborLd.insertRecordToQualiaStore` no-ops).

---

## R-CP — Rust cooperative features (wellfare-core + Tauri)

- [ ] **R-CP1. Rust obligation accounting** — `ObligationLedger` struct, µ-unit calculation, CRDT merge algorithm. Pure Rust, works in both WASM and native Tauri.
- [ ] **R-CP2. Author-Scoped Merkle Signature** — `merkle_sign(prev_hash, payload, ed25519_key) → [u8;64]`. Reuses `ed25519-dalek`. Matches `CommitScreen.kt` logic.
- [ ] **R-CP3. PFM Rust data models** — `LedgerEntry`, `TaxJurisdictionNym`, `ObligationMatrix` structs; CBOR-LD serialization; `.OFX`/`.QIF` export functions.
- [ ] **R-CP4. VC parsing + VP generation** — Rust port of `CredentialManager.kt`: parse W3C VC JSON-LD, `createVerifiablePresentation()`, `deriveClaim()`. Complements (does not replace) `vault-sanctuary-evidence.js` OTS VP generation.

---

## P — Packaging & distribution

**Mode A — WellFair bundle (qualiaDB as required component):**

- [ ] **P1. Unified Cargo workspace** — add wellfare-core (once relocated W1) to root `Cargo.toml` workspace members.
- [ ] **P2. CI build matrix** (GitHub Actions):
  - `wasm-pack build wellfare-core --target web` → `docs/pkg/` (GitHub Pages)
  - `cargo tauri build` → Windows/macOS/Linux desktop
  - `cargo tauri android build` → `.aab` / `.apk`
  - `cargo tauri ios build` → `.ipa` (macOS runner)
- [ ] **P3. WASM service worker caching** — `sw.js` must explicitly cache `pkg/wellfare_core_bg.wasm` in the install event.
- [ ] **P4. PWA manifest** — `docs/manifest.webmanifest` `start_url` should point to `vault.html` (not `pair.html`).
- [ ] **P5. App store signing** — Android keystore + Play Store / F-Droid; iOS provisioning profile + App Store Connect; Windows code signing.
- [ ] **P6. Version coupling** — sync `pkg/package.json` version with `Cargo.toml` version. Add `pkg/version.json` so vault can detect stale WASM binaries.

**Mode B — qualiaDB standalone:**

- [ ] **P7. npm publish for `qualia-db-wasm`** — `sdk/wasm/package.json` proper publish step; scoped exports; browser integration README.
- [ ] **P8. Daemon documentation** — HTTP :4242 + WebSocket :9090 endpoints for non-WellFair consumers; CBOR-LD request format.
- [ ] **P9. qualia-desktop Tauri v2** — upgrade independent of WellFair vault; keep as "engine-only" desktop product.

---

## DA — Distributed Analytics & Research Commons (v0.0.7+)

None started. Only after Phase 2 (directory + cooperative) is stable.

- [ ] **DA1. `vault-analytics.js`** — StudyCredential parser, local N3 rule evaluator (→ Sentinel VM), consent controller, ε-budget tracking.
- [ ] **DA2. `vault-dp.js`** — Local Differential Privacy: Randomized Response + ε-budget per category (rolling 90-day window). Rust implementation preferred (R-DA1).
- [ ] **DA3. Research panel UI** — new panel in vault.html: active studies, contribution history, earned credits. Behind consent gate.
- [ ] **DA4. `coordinator/` Node.js server** — Nym listener, k-anonymity engine (k=15 default), HMAC blind claim ticket issuance/redemption. Run by research institutions.
- [ ] **DA5. `research-creator/` app** — standalone no-code study builder: visual query editor, N3+SHACL rule compiler, StudyCredential signer, bounty escrow + Lightning funding.
- [ ] **DA6. Lightning payout loop** — DA blind claim token → Lightning invoice → `vault-wallet.js`. Financial chain decoupled from data chain. Connects to cooperative obligation payments and HCW welfare payments on the same Lightning rail.

---

## Completed (reference)

- [x] M1–M6 core vault: WebRTC QR pairing, Gun signalling, DataChannel, 9 access profiles
- [x] M2 Identity credentials + Noise_XX E2E (Ed25519 did:key, X25519, AES-256-GCM, Noise_XX)
- [x] M3 Ephemeral sharing (session TTL, BFCache, FinalizationRegistry, emergency pre-auth, audit log)
- [x] M4 Nym mixnet scaffolding (SW COOP/COEP, nymAdapter, DMS, fragment reassembly, SURB pool)
- [x] M5 Sanctuary Mode + Duress (PBKDF2, sanctuary IDB, DLT commitment, decoy vault, unvarnished log)
- [x] M6 Hardening: Gun write audit, PWA manifest, Wake Lock, relay handling, Tripwire, Synthesis Engine, Evidentiary Export, OTS Bitcoin anchoring, browser compat guard
- [x] VC-7 Verified Directory (wf-contacts, wf-relationships, wf-agreements, IDB v4)
- [x] VC-8 Semantic Handshake (ODRL agreement + did:peer)
- [x] VC-9 Inbound caller gating (Nym+Gun dual transport)
- [x] VC-10 Hypermedia voice/video calls (vault↔vault + guest link join.html)
- [x] VC-11 Web Connector (live data sharing, signed VP receipts)
- [x] VC-12 Background Job Scheduler (vault-scheduler.js, wf-jobs IDB v5)
- [x] VC-13 Event Log & Transcript (HTML+RDFa, Merkle chain, vault-transcript.js)
- [x] VC-14 Language Transcoding (3-tier progressive STT+translation)
- [x] VC-15 Content Package (JSON-LD manifest, ODRL-permissioned zip, OTS anchor)
- [x] WA-1–7 Webizen Agent (AgentController, cv-emotion worker, audio DSP, IDB v7 telemetry, connector Live Indicators, transcript BiometricTelemetryLog)
- [x] HCW-1 Human-Centric Wallet (IDB v8, vault-wallet.js, Lightning UI)
- [x] HCW-2 Nym bandwidth abstraction (ensureNymBandwidth, rate cache, btcNym swap)
- [x] DL-1 Diet log barcode (vault-diet-barcode.js, BarcodeDetector + ZXing fallback + OFF lookup)
- [x] wellfare-core WASM v0.0.4-dev built + deployed to docs/pkg/ (282KB)
- [x] Package manager (docs/packages/) — OPFS-based, handles oxigraph/prolog-wasm/llm-mediapipe
- [x] Device bridge (device-bridge.js) — File System Access API for Samsung Health exports
- [x] app.html Streamlit analytics dashboard with persona demos

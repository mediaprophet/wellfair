# WellFair + qualiaDB — Master TODO
> Last updated: 2026-06-03  
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
- [ ] **W2. Implement `QualiaStore.insert_quin()` for real** — `qualia_bindings.rs` is a stub returning `true` without storing. Wire through to `qualia-core-db` engine.
- [ ] **W3. Implement `QualiaStore.query_subject()` for real** — currently returns empty `Float64Array`. Should return matching Quins from the store.
- [ ] **W4. Add `WasmHealthStore` with SPARQL** — vault-wasm.js calls `new wasm.WasmHealthStore()` → `.load_turtle()` → `.query()`. Add oxigraph-backed struct to `wasm.rs`:
  ```rust
  #[wasm_bindgen] pub struct WasmHealthStore { store: oxigraph::MemoryStore }
  ```
- [ ] **W5. Add `validate_health_turtle()` SHACL validation** — called in vault-wasm.js but absent from d.ts. Wire to SHACL-to-Sentinel compiler path from qualiaDB, or lightweight oxigraph validator.
- [ ] **W6. Replace `validate_health_quin()` stub** — always returns `{"valid":true}`. Wire to real Sentinel VM constraint check via `qualia-core-db`.
- [ ] **W7. Add oxigraph to Cargo.toml** — `oxigraph = { version = "0.4", features = ["js"] }`. Required for W4/W5. This is what `registry.json` claims is `bundled: true` for the `core:rdf`/`core:sparql` capabilities.
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
  - Cooperative: `project_list`, `contribution_commit`, `obligation_balance`
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
- [ ] **A6. Port N3 reasoning rules** — `legacy_pwa/extensions/n3_reasoner/rules/` has four rules (adrenal_fatigue, cardiovascular_risk, sleep_debt, trauma_cascade). Move to `wellfare-core/rules/` and compile via qualiaDB's SHACL-to-Sentinel compiler as part of build.
- [ ] **A7. Real-device testing** — iOS Safari, Android Chrome, Firefox 130+. Matrix in `instructions/BROWSER_COMPAT.md`.
- [ ] **A8. SURB stress test** — airplane-mode toggle while Nym active; verify 30s fragment expiry + replenish.

---

## CP — Cooperative Projects panel

New panel in vault.html + `vault-projects.js` module.

- [ ] **CP1. `vault-projects.js`** — project discovery/browse UI, join project, my-contributions view, obligation dashboard (µ-units earned/outstanding).
- [ ] **CP2. Contribution commit** — "Log Work" sheet: hours + description → Author-Scoped Merkle Signature: `sign(sha256(prev_hash ‖ hours ‖ description ‖ timestamp))` using existing Ed25519 key. Written to `wf-contributions` IDB.
- [ ] **CP3. µ-unit calculation** — hours × agreed project rate → µ-units balance. Per-project rate stored in `wf-projects`; falls back to cooperative global rate.
- [ ] **CP4. `vault-p2p-sync.js`** — three-tier P2P sync:
  - Tier 1: Nym (`vault-nym.js`) — obligation commits, maximum anonymity ("Sanctuary Mode")
  - Tier 2: Gun+WebRTC (already wired) — project state sync
  - Tier 3: Git-compatible N-Quads ledger export (`.nq`) via qualiaDB `export-solid`
  - CRDT merge: sum-based for obligation µ-units; last-write-wins for project metadata
- [ ] **CP5. IDB v11 stores** — add: `wf-projects`, `wf-contributions`, `wf-obligations`.
- [ ] **CP6. Project directory feed** — fetch/cache project list from cooperative node (via Nym Tier 1 or Gun Tier 2). Cache in `wf-projects` for offline use.

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
- [ ] **DIR4. SHACL shapes for cooperative vocabulary** — extend `docs/profiles/access-profiles.ttl`:
  - `wf:ContributionRecord` shape
  - `wf:ObligationBalance` shape
  - `wf:VerifiableCredential` shape
  - `wf:GuardianRelationship` shape
  - `wf:CooperativeProject` shape

---

## OC — Ontology Converter (app.html analytics)

Browser equivalent of the Android `OntologyConverter.kt` + `OntologyScreen.kt`.

- [ ] **OC1. Ontology converter panel in app.html** — file picker (`.ttl`, `.nt`, `.jsonld`, `.json`, `.csv`) → N-Quads (`.nq`) or `.q42` via wellfare-core WASM. Show: quads written, compression ratio, parse time, output size. Matches Android OntologyScreen metrics.
- [ ] **OC2. Ontology ingestion to QualiaStore** — when a `.ttl`/`.q42` file is loaded, import into live `QualiaStore` to enrich SPARQL queries and LLM context. Depends on W4 (`WasmHealthStore`) being live.
- [ ] **OC3. Cooperative ontology bundles** — pre-package as `.q42` files, downloadable via OPFS package manager: `wf:` shapes, UDHR-as-RDF, ODRL EdgeConstraints, FOAF. Persist in OPFS; enrich all SPARQL/N3 queries.

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

# WellFair — Session Start Prompt
> Paste the block below at the start of a new Claude Code session.
> Update the "Last session" and "Start here" lines when the active task changes.

---

```
You are picking up the WellFair + qualiaDB project. Read the following documents before doing anything else — in this order:

1. CLAUDE.md                              — mandatory project orientation, terminology, architecture constraints
2. instructions/HANDOVER_CURRENT.md       — current state, decisions made, what is blocked, what to do next
3. TODO.md                                — master task list; find the first unchecked [ ] item in your area

Do NOT start writing code until you have read all three. They are short and contain decisions that will save you from going the wrong direction.

---

LAST SESSION (2026-06-04 — session 5):

Protocol Integration Architecture from qualiaDB/docs/protocol-integration-architecture.md was read and
fully incorporated. Two major work streams completed:

1. PIA — Protocol Integration Architecture (5 of 11 tasks complete):
   - PIA1: qp: namespace (https://qualia.id/ns/) added to access-profiles.ttl — 8 classes, 14 properties,
     5 SHACL shapes; vault-projects.js Turtle export dual-types all entities as both wf: and qp:
   - PIA2: wf:ProtocolEvent schema defined in access-profiles.ttl — 7 event types, SHACL shape
   - PIA3: vault-comms-call.js — _writeProtocolEvent() writes webrtc_session_start/end records to
     wf-events on every call with participants + duration
   - PIA4: vault-handshake.js — _agreementToNQuads() + _writeContractEvent() write git_commit_ref
     event to wf-events on finalise/accept; bundle Ed25519-signed with local key
   - PIA6: Personal boundary protection — IDB bumped to v12; wf-calendar store added (indexed by
     startIso); vault-calendar.js created (CRUD + checkBoundaryConflict + logBoundaryConflict +
     setPersonalPriority toggle); logContribution() in vault-projects.js checks calendar overlaps before
     committing; logContributionForced() bypass for after user opt-in confirmation

2. CBOR-LD as native QualiaStore format (CBOR1–4 complete):
   - Architectural decision: qualiaDB cbor_compiler.rs REJECTS { JSON, < RDF/XML, @ Turtle.
     QualiaStore must receive CBOR arrays of Lexicon-compressed u64 IDs.
     Turtle/oxigraph remains valid for WasmHealthStore SPARQL analytics.
   - vault-cborld.js created: Lexicon cache (wf-lexicon IDB v10 backed), iriToId(), encodeIrisToCbor(),
     decodeCborToIds/Iris(), recordToCborLdQuins(), insertRecordToQualiaStore()
   - qualia_bindings.rs: QualiaStore.insert_from_cbor_ld(&[u8]) + private parse_cbor_quin() added
   - vault-idb.js _dbPut fixed: removed broken JSONtoQuinSerializer; now emits CBOR-LD existence triple
   - vault-projects.js: exportProjectsToCborLdQuins() added — decrypts + bulk-inserts into QualiaStore

Also added TODO.md §PIA (11 tasks) and §CBOR (9 tasks) to the master task list.

---

START HERE (next session):
1. Read the three documents above
2. CBOR9 (recommended first — unblocks all CBOR testing):
   cd wellfare-core && wasm-pack build --release --target web --out-dir ../docs/pkg
   This deploys QualiaStore.insert_from_cbor_ld() to docs/pkg/. Without it, CBOR-LD wiring
   runs silently at no-op (vault-cborld.js checks qStore.insert_from_cbor_ld existence at runtime).
3. CBOR5 — add exportToCborLdQuins() to: vault-meds-reminders.js, vault-directory.js,
   vault-wallet.js, vault-calendar.js. Pattern is identical to vault-projects.js CBOR4.
4. OC1 — Ontology Converter in app.html (file picker → Turtle/JSON-LD → N-Quads via WasmHealthStore).
   Fully unblocked. See TODO.md §OC.
5. PIA8 — Consent UI for project data flows (qp:hasConsentRelation gate in vault-projects.js).
   Required before CP4 GUN sync is activated.

---

KEY FACTS — CURRENT STATE:

Files created/changed this session:
  docs/profiles/access-profiles.ttl   — qp: vocab + SHACL shapes (PIA1) + wf:ProtocolEvent (PIA2)
  docs/js/vault-cborld.js             — NEW: CBOR-LD encoder/decoder + Lexicon manager
  docs/js/vault-calendar.js           — NEW: personal calendar CRUD + boundary protection (PIA6)
  docs/js/vault-projects.js           — qp: Turtle dual-typing (PIA1) + boundary gate (PIA6) +
                                        exportProjectsToCborLdQuins (CBOR4)
  docs/js/vault-comms-call.js         — WebRTC session Q42 provenance (PIA3)
  docs/js/vault-handshake.js          — git-signed contract N-Quads bundle (PIA4)
  docs/js/vault-idb.js                — IDB v12, wf-calendar store, fixed _dbPut dual-write (CBOR3)
  wellfare-core/src/qualia_bindings.rs — insert_from_cbor_ld + parse_cbor_quin (CBOR2)

IDB version history (current: v12):
  v11: wf-projects, wf-contributions, wf-obligations (CP1/CP5)
  v12: wf-calendar (PIA6 personal boundary protection)
  v13 planned: wf-credentials, wf-pfm-config, wf-ledger (CV5 + PFM1)

WASM binary (docs/pkg/): v0.0.4-dev + oxigraph (3.3 MB) — insert_from_cbor_ld NOT YET DEPLOYED
  → CBOR9 rebuild required before CBOR-LD QualiaStore path is live in browser

Remaining PIA tasks:
  PIA5  — GUN Tier 2 sync for qp:Slice equity shares
  PIA7  — vault-webtorrent.js: WebTorrent Tier 4
  PIA8  — qp:hasConsentRelation consent UI gate in vault-projects.js
  PIA9  — Hybrid four-tier connectivity in vault-p2p-sync.js (CP4)
  PIA10 — git-mark legal audit trail (extends PIA4)
  PIA11 — Cross-project obligation propagation with consent

Remaining CBOR tasks:
  CBOR5 — CBOR-LD export for other vault modules
  CBOR6 — Sentinel constraint IDs via Lexicon
  CBOR7 — CBOR-LD wire format for CP4 GUN sync
  CBOR8 — CBOR-LD packages for WebTorrent (PIA7)
  CBOR9 — Rebuild WASM (deploy insert_from_cbor_ld)

Still incomplete from earlier:
  CP4  — vault-p2p-sync.js (Tier 1 Nym blocked on A3; Tier 2 Gun available)
  CP6  — project directory feed
  CP7  — Dynamic Equity / Stewardship Shares panel (qp:Slice)
  CP8  — Project Governance panel (qp:ProjectGovernance)
  OC1  — Ontology Converter in app.html (FULLY UNBLOCKED)
  DIR1 — Unified contact graph wf:coContributor
  W8   — Dual-target Cargo.toml (native + WASM)
  W10  — wire compile_query_to_json (--features qualia)

---

KEY FILES:
  docs/vault.html              Primary phone vault (PIN → all panels)
  docs/app.html                Analytics Dashboard (512KB — read in chunks)
  docs/js/                     29 JS modules (vault-cborld.js, vault-calendar.js newly added)
  docs/pkg/                    Built WASM (needs CBOR9 rebuild)
  docs/profiles/access-profiles.ttl  SHACL shapes (now includes qp: + wf:ProtocolEvent)
  wellfare-core/               Rust WASM crate source
    src/qualia_bindings.rs     QualiaStore + insert_from_cbor_ld (not yet in WASM pkg)
    src/store.rs               WasmHealthStore (oxigraph SPARQL)
    src/shapes.rs              SHACL validation
    src/sentinel.rs            SentinelVM policy gates
    src/n3_rules.rs            Clinical N3 pattern rules
  instructions/HANDOVER_CURRENT.md   Full detail on what's done / blocked / next

---

ARCHITECTURE DECISIONS THIS SESSION (now locked):
- CBOR-LD is the native format for QualiaStore quint writes — not JSON, not Turtle
  qualiaDB cbor_compiler.rs rejects text at the binary gatekeeper
  vault-cborld.js is the browser-side Lexicon + encoder
- Personal boundary protection (PIA6) is non-negotiable: project obligations cannot auto-schedule
  over wf:personalPriority calendar entries — equivalent to Sanctuary Mode for the cooperative layer
- qp: prefix (https://qualia.id/ns/) is the canonical cooperative ontology namespace in WellFair

---

TERMINOLOGY (enforced — do not use the wrong terms):
- "Identity credentials" — never "DIDs" or "VCs" in user-facing text
- "Verified Directory" in code — "Contacts"/"Directory" in UI — never "sovereign"
- SHACL/RDFS for shapes about people — OWL only for policy artefacts (EdgeConstraint etc.)
- wf: namespace → https://wellfare.social/ns/vault#
- qp: namespace → https://qualia.id/ns/ (cooperative projects)

---

ARCHITECTURE (locked — do not revisit without explicit instruction):
- Phone is authoritative vault; desktop is always stateless
- Gun.eco for WebRTC signalling only — health data never touches Gun relay nodes
- Tauri v2 is the target mobile platform — vault.html WebView is the UI shell
- wellfare-core is the bridge crate (Rust, wraps qualia-core-db with health-specific WASM bindings)
- Lightning + Nym is the unified payment rail (HCW + cooperative + research bounties)
- Directory harmonization: Verified Directory + SocialBook + cooperative contributor list = one wf-contacts
- CBOR-LD → QualiaStore (quint/Sentinel); Turtle/oxigraph → WasmHealthStore (SPARQL analytics)

---

Demo PIN: 1234 | vault.html?demo skips PIN (UI-only)
Dev server: python -m http.server 3000 --directory docs
Testing: always use mcp__Claude_in_Chrome__* tools — Claude app preview lacks WebCrypto

Update instructions/HANDOVER_CURRENT.md and TODO.md at the end of this session.
```

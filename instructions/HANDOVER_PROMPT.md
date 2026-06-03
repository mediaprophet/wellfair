# WellFair — Session Start Prompt
> Paste the block below at the start of a new Claude Code session.
> Update "Last session" and "Start here" lines when the active task changes.

---

```
You are picking up the WellFair + qualiaDB project. Read the following documents before doing anything else — in this order:

1. CLAUDE.md                              — mandatory project orientation, terminology, architecture constraints
2. instructions/HANDOVER_CURRENT.md       — current state, decisions made, what is blocked, what to do next
3. TODO.md                                — master task list; find the first unchecked [ ] item in your area

Do NOT start writing code until you have read all three. They are short and contain decisions that will save you from going the wrong direction.

---

LAST SESSION (2026-06-04 — session 6):

Six epics completed in one session:

1. CBOR5-6, CBOR7, CBOR9 (CBOR-LD wiring complete):
   - exportToCborLdQuins() added to vault-meds-reminders.js, vault-directory.js,
     vault-wallet.js, vault-calendar.js (CBOR5)
   - evaluatePolicyConstraintByIri() in vault-sentinel.js — IRI strings resolved through
     Lexicon before Sentinel evaluation (CBOR6)
   - WASM rebuilt; insert_from_cbor_ld confirmed in docs/pkg/wellfare_core.d.ts; CI deployed (CBOR9)

2. OC1 — docs/ontology-converter.html created:
   - Standalone page: drag-drop file picker (.ttl/.nt/.nq/.csv/.jsonld)
   - Auto-detection, SPARQL CONSTRUCT, CSV parsers, SHACL validation, metrics, copy/download

3. CP4 — docs/js/vault-p2p-sync.js created (four-tier P2P sync):
   - Tier 1: Nym obligation commits (Sanctuary Mode)
   - Tier 2: GUN project/obligation state with CBOR-LD wire format (CBOR7 satisfied)
   - Tier 3: N-Quads (.nq) ledger export + browser download
   - Tier 4: WebTorrent stub (registers for PIA7)
   - CRDT: max-wins for µ-units, last-write-wins for project metadata
   - window.vaultP2pSync public API: init/pushProject/pullProject/pushAll/pullAll/
     exportNQuads/downloadNQuads/seedWebTorrent/pushEquityShares/pullEquityShares

4. PIA5 — equity share sync (real implementation, not stub):
   - pushEquityShares: encodes each contributor slot as CBOR-LD quints (wf:did/wf:pct/wf:ts)
   - pullEquityShares: decodes CBOR-LD, merges mini-lexicon, CRDT-merges into wf-shares
   - _mergeEquityShares: last-write-wins per contributor did, governance merged by updatedAt

5. CP7 — Dynamic Equity Shares panel in vault.html project detail view:
   - Contributor list with % allocations (own slot highlighted)
   - Set-own-slice input → updateContributorSlot → auto-push to peers
   - Sync button → push + pull cycle → panel reloads
   - Cash-out / tokenized governance checkboxes → auto-save + push
   - Download ledger (.nq) button
   - Handlers: _projSaveEquitySlice / _projSyncEquity / _projSaveGovernance

6. Bug fixes and hardening:
   - vault-cborld.js, vault-calendar.js, vault-p2p-sync.js now wired into vault.html
   - initCalendar() + vaultCborLd.initCborLd() + vaultP2pSync.init() in all unlock paths
   - vault-projects.js: getAllProjects/getAllObligations/getContributions now use
     Promise.allSettled — OperationError from stale ciphertext no longer aborts the list
   - mergeObligationBalance(projectId, newMuUnits) added to vault-projects.js public API
   - IDB bumped to v13: wf-shares store added for qp:Slice equity allocations

---

START HERE (next session):
1. Read the three documents above
2. Recommended first task: CP6 — Project directory feed
   - Gun read from cooperative node project listing → cache in wf-projects
   - Add "Discover" button to projects sheet header in vault.html
   - See TODO.md §CP for full spec
3. Alternative: PIA8 — Consent UI gate before GUN sync
   - qp:hasConsentRelation dialog in vault-p2p-sync.js pushProject()
   - Purpose, time-limit, what-is-shared capture → stored in wf-agreements
4. Or: PFM1 — vault-pfm.js + IDB v14 (wf-ledger, wf-pfm-config)
   - Double-entry ledger — income/expense, categories, account IDs
   - See TODO.md §PFM for full 9-task arc

Also see instructions/GROK_COLLABORATION.md — tasks suitable for Grok to implement
in parallel (Rust modules, SHACL shapes, PFM/CV skeletons, test data).

---

KEY FACTS — CURRENT STATE:

IDB version history (current: v13):
  v11: wf-projects, wf-contributions, wf-obligations (CP1/CP5)
  v12: wf-calendar (PIA6 personal boundary protection)
  v13: wf-shares (CP7/PIA5 equity shares)
  v14 planned: wf-credentials, wf-pfm-config, wf-ledger (CV5 + PFM1)

Script load order (vault.html) — critical dependencies:
  vault-cborld.js  → must load BEFORE vault-projects.js
  vault-calendar.js → must load BEFORE vault-projects.js (boundary check)
  vault-p2p-sync.js → must load AFTER vault-wallet.js

WASM binary (docs/pkg/): v0.0.4-dev + oxigraph (3.3 MB)
  insert_from_cbor_ld IS deployed (CBOR9 complete)
  CI builds on every push to feature/qualia-db-integration

Remaining high-priority tasks (TODO.md):
  CP6  — Project directory feed from cooperative node
  CP8  — Project Governance panel (qp:ProjectGovernance)
  PIA7 — vault-webtorrent.js: WebTorrent Tier 4
  PIA8 — Consent UI for project data flows (qp:hasConsentRelation)
  PIA9 — Hybrid four-tier connectivity + offline-first guarantee
  PIA10 — git-mark legal audit trail (extends PIA4)
  PIA11 — Cross-project obligation propagation with consent
  PFM1–9 — Personal Finance Management (double-entry ledger, receipts, OFX export)
  CV1–5 — Credential Vault (VC wallet, Maslow VP, guardianship)
  DIR1–4 — Directory harmonization (unified contact graph)
  CBOR8 — WebTorrent CBOR-LD packages (blocked on PIA7)
  R-CP1–4 — Rust cooperative features (wellfare-core)

GUN namespaces:
  wf-v1-signal    — WebRTC signalling (connector/index.html, join.html)
  wf-v1-project   — P2P project sync (vault-p2p-sync.js)

P2P sync architecture (vault-p2p-sync.js):
  window.vaultP2pSync.init({ did, gunRelays, nymAddress, projectIds, sanctuaryMode })
  pushProject(id) / pullProject(id) / pushAll() / pullAll()
  pushEquityShares(id, shares) / pullEquityShares(id) — PIA5
  exportNQuads() / downloadNQuads() — Tier 3
  seedWebTorrent() — Tier 4 stub (PIA7)

CRDT rules (vault-p2p-sync.js):
  Obligations:        max(muUnits) wins (Merkle chain append-only)
  Project metadata:   last-write-wins by updatedAt timestamp
  Equity shares:      last-write-wins per contributor did by ts
  Governance:         last-write-wins by overall updatedAt

---

KEY FILES:
  docs/vault.html              Primary phone vault (PIN → all panels)
  docs/app.html                Analytics Dashboard (512KB — read in chunks)
  docs/ontology-converter.html Standalone ontology converter (OC1)
  docs/js/vault-idb.js         IDB v13, store constants, _dbPut dual-write
  docs/js/vault-cborld.js      CBOR-LD Lexicon + encoder/decoder
  docs/js/vault-calendar.js    Personal calendar + boundary protection (PIA6)
  docs/js/vault-projects.js    Cooperative Projects + equity CRUD (CP1-3,5,7)
  docs/js/vault-p2p-sync.js    Four-tier P2P sync (CP4, CBOR7, PIA5)
  docs/js/vault-sentinel.js    SentinelVM + policy gates + Lexicon-IRI bridge (CBOR6)
  docs/profiles/access-profiles.ttl  SHACL shapes (wf: + qp: + wf:ProtocolEvent)
  wellfare-core/src/
    qualia_bindings.rs          QualiaStore + insert_from_cbor_ld
    store.rs                    WasmHealthStore (oxigraph SPARQL)
    sentinel.rs                 SentinelVM policy gates
    n3_rules.rs                 Clinical N3 → SPARQL rules
  instructions/HANDOVER_CURRENT.md   Full detail on what's done / blocked / next
  instructions/GROK_COLLABORATION.md Tasks for Grok + reporting format

---

ARCHITECTURE DECISIONS (locked):
- CBOR-LD is the native format for QualiaStore quint writes — not JSON, not Turtle
- Personal boundary protection (PIA6) is non-negotiable
- qp: prefix (https://qualia.id/ns/) is the canonical cooperative ontology namespace
- Gun.eco for signalling only; wf-v1-project namespace for P2P project state
- Sanctuary Mode → Tier 1 (Nym) only; no GUN traffic when Sanctuary is active
- Promise.allSettled for all IDB decrypt operations (never abort list on stale ciphertext)

---

TERMINOLOGY (enforced):
- "Identity credentials" — never "DIDs" or "VCs" in user-facing text
- "Verified Directory" in code — "Contacts"/"Directory" in UI — never "sovereign"
- SHACL/RDFS for shapes about people — OWL only for policy artefacts (EdgeConstraint etc.)
- wf: namespace → https://wellfare.social/ns/vault#
- qp: namespace → https://qualia.id/ns/ (cooperative projects)

---

Demo PIN: 1234 | vault.html?demo skips PIN (UI-only, throwaway AES key)
Dev server: python -m http.server 3000 --directory docs
Testing: ALWAYS use mcp__Claude_in_Chrome__* tools — Claude app preview lacks WebCrypto

Update instructions/HANDOVER_CURRENT.md and TODO.md at the end of this session.
```

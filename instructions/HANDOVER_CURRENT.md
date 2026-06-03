# WellFair — Current Handover
> **Living document — update this at the end of every session.**  
> Last updated: 2026-06-04  
> Updated by: session 6 (CBOR5-9, OC1, CP4, CBOR7, PIA5, CP7)

---

## How to use this file

At the start of every session, read in order:
1. `CLAUDE.md` — project orientation, terminology, architecture (mandatory)
2. This file — current state, decisions made, active work
3. `TODO.md` — full task list; find the first unchecked item in your area
4. Any source files listed under "Read first" for the active task

At the end of every session, update the sections below that changed.

---

## Project in one paragraph

WellFair is a privacy-first personal health vault. The phone is the authoritative vault; the desktop/laptop is a stateless compute terminal. Data flows phone → desktop over an end-to-end-encrypted Noise_XX DataChannel. Nothing persistent lives on the desktop after the tab closes. The system is built around a founding use case: a person escaping organised exploitation who needs welfare payments and care services without any transaction or identity record being linkable to their physical location.

---

## Current architecture (as of 2026-06-04)

### Two apps, one engine

| App | Entry point | Purpose |
|---|---|---|
| **Privacy Vault** | `docs/vault.html` | PIN, sanctuary, Nym, meds, identity credentials, calls, cooperative projects, wallet |
| **Analytics Dashboard** | `docs/app.html` | Streamlit-in-browser ("Holographic Engine") — persona demos, health visualisations, Prolog inference, LLM |

Both share `docs/pkg/wellfare_core_bg.wasm` (3.3 MB, v0.0.4-dev + oxigraph).

### Engine: wellfare-core

- **Source**: `wellfare-core/` (Rust, cdylib, edition 2024) — at repo root
- **Built output**: `docs/pkg/wellfare_core.js` + `wellfare_core_bg.wasm` (3.3 MB with oxigraph)
- **CI builds it**: `.github/workflows/pages.yml` — `cd wellfare-core && wasm-pack build --release --target web --out-dir ../docs/pkg`
- **qualia-core-db** is now an **optional** Cargo feature (`--features qualia`); heavy for WASM, excluded from default build
- **WASM exports**: `WasmHealthStore` (new/load_turtle/query), `validate_health_turtle()`, `QualiaStore` (insert_quin/query_subject/query_predicate/query_context/insert_from_cbor_ld/len/clear)

### Engine: qualiaDB (external repo)

- Repo: `https://github.com/mediaprophet/qualiaDB`
- v0.0.3; Rust workspace: `qualia-core-db`, `qualia-cli`, `qualia-desktop` (Tauri v1.5)
- `qualia-desktop` is Tauri v1.5 — must upgrade to v2 before mobile targets work

### Primary vault: Rust → Tauri v2 (decided 2026-06-03)

The browser PWA (`vault.html`) is the current working implementation. The **target** is a Tauri v2 native app for iOS/Android where:
- vault.html + CSS is the WebView UI (preserved)
- All crypto, storage, and Nym operations move to Rust Tauri commands
- qualiaDB `.q42` replaces IndexedDB as the primary store
- Nym Rust SDK replaces the WASM SDK (no SharedArrayBuffer headaches)

---

## Active branch

`feature/qualia-db-integration` — **9 commits ahead of master, all pushed to origin.**

| Commit | What |
|---|---|
| `70f5bb6` | Cleanup: legacy Python/Rust → `legacy_pwa/`; CI fix; `TODO.md`; instruction docs |
| `dd9a5a3` | Integration: `vault-wasm.js` qualiaDB bridge, IDB v10, `vault-sentinel.js`, `CLAUDE.md` |
| `20c5f80` | W1: `wellfare-core/` at repo root; CI path restored |
| `b1814e9` | W2–W7: real QualiaStore, WasmHealthStore SPARQL, SHACL validation; WASM rebuilt |
| `bfe151e` | W6, A6: SentinelVM policy gates + N3Logic clinical rules |
| `b565f5a` | CP1–CP3, CP5: Cooperative Projects panel + qualiaDB integration |
| `4927ac2` | PIA1–4, PIA6, CBOR1–4: protocol integration + CBOR-LD native QualiaStore format |
| `0b08620` | CBOR5-6, OC1: CBOR-LD exports for all vault modules + Sentinel Lexicon + Ontology Converter |
| `67f034a` | CP4, CBOR7: four-tier P2P sync layer + CBOR-LD wire format |
| `247da0e` | PIA5, CP7: equity share sync + Dynamic Equity Shares panel |

**Working tree: clean** (only `32-02.url` untracked Windows shortcut — ignore).

---

## Key architectural decisions (locked — do not revisit without explicit instruction)

All decisions from `CLAUDE.md` still apply, plus:

1. **Rust-first for mobile** — primary vault is a Tauri v2 app; browser PWA is demo/fallback
2. **Two-app structure** — `vault.html` (privacy vault) and `app.html` (analytics) are separate products sharing the engine
3. **wellfare-core is the bridge crate** — wraps qualia-core-db with health-specific WASM bindings; will have a native (non-WASM) target for Tauri
4. **Directory harmonization** — Verified Directory (`vault-directory.js`), qualiaDB SocialBook, and Cooperative Projects contributor list all resolve to the same `wf-contacts`/`wf-relationships` graph
5. **Lightning is the unified payment rail** — HCW welfare payments, cooperative obligation micropayments, and DA research bounties all use the same LDK node via Nym SOCKS5 proxy
6. **cooperative.html model adopted** — obligation matrix, Author-Scoped Merkle Signatures, µ-units, four-tier P2P sync, and PFM eight-phase architecture are all in scope for WellFair
7. **Protocol Integration Architecture adopted** — `qp:` namespace (`https://qualia.id/ns/`) for cooperative ontology; GUN/WebTorrent/WebRTC/git-mark as unified trust layer; see `TODO.md §PIA`
8. **Personal boundary protection is non-negotiable** — project obligations must never auto-schedule over personal calendar entries (`wf:personalPriority`). Override attempts logged with Q42 provenance.
9. **CBOR-LD is the native format for QualiaStore** — not JSON, not Turtle. `vault-cborld.js` is the browser-side Lexicon + encoder. Turtle/oxigraph remain valid for WasmHealthStore SPARQL analytics only.
10. **Gun.eco for signalling only** — project P2P state uses `wf-v1-project` GUN namespace; health data and signals never share relay nodes

---

## What is complete

See `TODO.md` for the full checked list. Session 6 completions:

- **CBOR5** — `exportToCborLdQuins()` added to `vault-meds-reminders.js`, `vault-directory.js`, `vault-wallet.js`, `vault-calendar.js`
- **CBOR6** — `evaluatePolicyConstraintByIri()` in `vault-sentinel.js`: resolves IRI strings through Lexicon before Sentinel evaluation
- **CBOR7** — CBOR-LD wire format for GUN Tier 2 in `vault-p2p-sync.js`: each push encodes quints + mini-lexicon; receiver decodes and merges
- **CBOR9** — WASM rebuilt; `insert_from_cbor_ld` confirmed in `docs/pkg/wellfare_core.d.ts`; CI deployed
- **OC1** — `docs/ontology-converter.html` (standalone page): file-drop + SPARQL CONSTRUCT + CSV parsers + SHACL validation + metrics + download
- **CP4** — `docs/js/vault-p2p-sync.js` created: four-tier P2P sync (Nym Tier 1 / GUN+CBOR7 Tier 2 / N-Quads Tier 3 / WebTorrent stub Tier 4); CRDT merge for obligations and metadata; wired into vault.html unlock flow
- **PIA5** — GUN Tier 2 sync for `qp:Slice` equity shares: CBOR-LD encoded per contributor slot; last-write-wins CRDT merge per `did`
- **CP7** — Dynamic Equity Shares panel in `vault-projects.js` project detail view: contributor list, set-own-slice, governance toggles (cash-out / tokenized), sync button, download .nq ledger

Also this session:
- `vault-cborld.js`, `vault-calendar.js`, `vault-p2p-sync.js` wired into `vault.html` script load (were missing)
- `initCalendar()` and `vaultP2pSync.init()` added to all three vault unlock paths (owner PIN, duress PIN, demo mode)
- `vault-projects.js` hardened: `getAllProjects()`, `getAllObligations()`, `getContributions()` now use `Promise.allSettled` so stale ciphertext from a different demo key never aborts the list
- `mergeObligationBalance(projectId, newMuUnits)` added to `vault-projects.js` public API for CRDT merge without synthetic contribution entries
- IDB bumped to **v13** — `wf-shares` store added for equity allocations

Earlier sessions (sessions 1–5):
- All vault milestones M1–M6, VC-7–VC-15, WA-1–7, HCW-1/2, DL-1
- W1–W7 (wellfare-core Rust engine: QualiaStore, WasmHealthStore SPARQL, SHACL, SentinelVM, N3Logic)
- CP1–CP3, CP5 (Cooperative Projects panel, Merkle contributions, µ-units)
- PIA1–4, PIA6 (qp: namespace, protocol event schema, WebRTC provenance, git-signed contracts, boundary protection)
- CBOR1–4 (vault-cborld.js, insert_from_cbor_ld Rust, _dbPut fixed, projects CBOR export)

---

## What is blocked

| Item | Blocked by |
|---|---|
| All M tasks (Tauri mobile) | qualia-desktop Tauri v1→v2 migration (M1) |
| W10 (compile_query_to_json) | qualia-core-db optional feature `--features qualia` — needs validation |
| CP6 Project directory feed | Nym activation preferred; GUN path available as fallback |
| W8 (dual-target Cargo) | M2 Tauri app crate doesn't exist yet |
| CBOR8 (WebTorrent packages) | PIA7 (vault-webtorrent.js) not yet built |
| HCW-3+ wallet | Rust Tauri command architecture (blocked by M4–M6) |
| DA1–DA6 analytics | Phase 2 (directory + cooperative) must be stable first |

---

## IDB version history

| Version | Added stores | Epic |
|---|---|---|
| v1–v3 | wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl | M1–M6 |
| v4 | wf-contacts, wf-relationships, wf-agreements | VC-7 |
| v5 | wf-jobs | VC-12 |
| v6 | wf-events | VC-13 |
| v7 | wf-telemetry | WA-1 |
| v8 | wf-wallet, wf-txlog | HCW-1 |
| v9 | wf-biometrics | WASM bridge |
| v10 | wf-lexicon | qualiaDB Lexicon |
| v11 | wf-projects, wf-contributions, wf-obligations | CP1/CP5 |
| v12 | wf-calendar | PIA6 Personal Boundary Protection |
| **v13** | **wf-shares** | **CP7/PIA5 Equity Shares** |
| **v14 (planned)** | wf-credentials, wf-pfm-config, wf-ledger | CV5 + PFM1 |

---

## Script load order in vault.html (as of session 6)

Critical: `vault-cborld.js` must load before `vault-projects.js`; `vault-p2p-sync.js` must load after `vault-projects.js` and `vault-wallet.js`.

```
gun.js (CDN)
vault-idb.js         — IDB v13, store constants, _dbPut dual-write
vault-crypto.js      — AES-GCM, key derivation, toB64/fromB64
vault-did.js         — did:key Ed25519 generation
vault-nym.js         — nymAdapter, DMS, anonymous notify
vault-mock.js        — mock data for demo mode
vault-cborld.js      — Lexicon cache + CBOR-LD encoder/decoder  ← session 6
vault-calendar.js    — personal calendar + boundary protection   ← session 6
vault-directory.js   — Verified Directory (VC-7)
vault-handshake.js   — Semantic Handshake (VC-8)
vault-comms-gate.js  — Inbound Caller Gating (VC-9)
vault-comms-call.js  — Call session (VC-10)
vault-scheduler.js   — Background Job Scheduler (VC-12)
vault-transcript.js  — Event log + transcript (VC-13)
vault-package.js     — Content Package (VC-15)
vault-sanctuary-*.js — PIN state machine + log + evidence
vault-meds-*.js      — Medications panel
vault-diet.js        — Diet / substance log
vault-projects.js    — Cooperative Projects + equity CRUD  ← updated session 6
vault-wasm.js        — wellfare-core WASM bridge
vault-sentinel.js    — SentinelVM + policy gates
vault-wallet.js      — HCW-1 Lightning wallet
vault-p2p-sync.js    — Four-tier P2P sync                  ← session 6
```

Unlock init chain (called on every unlock path — owner PIN, duress PIN, demo mode):
```javascript
deriveVaultKey(entered, _MAIN_SALT).then(k => {
  initDirectory(k);
  initProjects(k, vaultDidKey?.did);
  initCalendar(k);
  window.vaultCborLd?.initCborLd();
  window.vaultP2pSync?.init({ did: vaultDidKey?.did });
});
```

---

## Key file locations

```
docs/
  vault.html              Primary vault app (phone)
  app.html                Analytics/Streamlit dashboard (512KB — read in chunks)
  ontology-converter.html Standalone ontology converter (OC1) ← new session 6
  connector/index.html    Desktop connector (stateless)
  webconnect.html         WebRTC pairing bridge
  join.html               Call join page (guests)
  pair.html               Legacy monolithic page (keep as fallback)
  sw.js                   Service Worker (COOP/COEP headers)
  js/                     32 JS modules (vault-cborld.js, vault-calendar.js,
                           vault-p2p-sync.js newly active in vault.html)
  pkg/                    Built WASM: wellfare_core.js + wellfare_core_bg.wasm (3.3 MB)
  profiles/
    access-profiles.ttl   SHACL shapes (wf: + qp: + wf:ProtocolEvent)
    profiles.json         JS-loadable profile registry

wellfare-core/            Rust WASM crate source (THE primary Rust code)
  Cargo.toml              v0.0.4-dev; oxigraph (default); qualia-core-db optional "qualia"
  src/
    wasm.rs               All wasm_bindgen exports
    qualia_bindings.rs    QualiaStore + insert_from_cbor_ld
    store.rs              WasmHealthStore (oxigraph SPARQL)
    shapes.rs             SHACL validation (6 ASK constraints)
    sentinel.rs           SentinelVM policy gates
    n3_rules.rs           Clinical N3 pattern rules → SPARQL
    rdf.rs                Turtle serialisers
    parser.rs             CSV parsers
    models.rs             Rust data models

instructions/
  HANDOVER_CURRENT.md     THIS FILE
  HANDOVER_PROMPT.md      Session-start prompt (copy into new session)
  GROK_COLLABORATION.md   Tasks for Grok, reporting format ← new session 6
  COMMS_EPIC_PLAN.md      VC-7 through VC-15 implementation plan
  EPIC_PLAN_v0.0.7.md     WA + HCW epic plan
  ANALYTICS_EPIC_PLAN.md  DA/RC analytics epic plan
  BROWSER_COMPAT.md       Real-device test matrix

TODO.md                   MASTER TODO — always update alongside this file
CLAUDE.md                 Project orientation (mandatory reading every session)
```

---

## What to do next

Recommended order (most value, fewest dependencies):

1. **CP6** — Project directory feed: GUN read of cooperative node project listing → cache in `wf-projects`. Add "Discover projects" button to projects sheet header.
2. **CP8** — Project Governance panel: `qp:ProjectGovernance` policies per project (already started as UI stubs in CP7 equity panel). Turtle export via `exportProjectsToTurtle()`.
3. **PIA8** — Consent UI: `qp:hasConsentRelation` gate in `vault-p2p-sync.js` before any push. Brief dialog: purpose, time limit, what is shared. Consent revocable.
4. **PIA7** — `vault-webtorrent.js`: WebTorrent Tier 4 implementation. Registers with `vaultP2pSync` as Tier 4 backend. Unblocks CBOR8.
5. **PFM1** — `vault-pfm.js` + IDB v14: double-entry ledger store (`wf-ledger`, `wf-pfm-config`).
6. **CV1** — `vault-credentials.js` + IDB v14: VC wallet, QR-scan ingest, `wf-credentials` store.
7. **DIR1–DIR2** — Unified contact graph: `wf:coContributor` type + did:key → contact resolution.
8. **R-CP1/R-CP2** — Rust `ObligationLedger` + Author-Scoped Merkle Signature in `wellfare-core/src/`.

See `instructions/GROK_COLLABORATION.md` for tasks that can be delegated to Grok (Rust modules, SHACL shapes, PFM/CV skeletons).

Read first for next session: `TODO.md` sections CP, PIA, PFM, CV, DIR.

---

## Demo account

- **PIN**: `1234`
- `vault.html?demo` — skips PIN, loads mock data (UI-only testing)
- `vault.html` with PIN `1234` — full owner vault with real IDB persistence
- Dev server: `python -m http.server 3000 --directory docs`
- Testing: **always** use `mcp__Claude_in_Chrome__*` tools — Claude app preview lacks WebCrypto, IDB writes, and Service Worker registration

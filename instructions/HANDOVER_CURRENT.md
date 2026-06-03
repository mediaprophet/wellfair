# WellFair — Current Handover
> **Living document — update this at the end of every session.**  
> Last updated: 2026-06-03  
> Updated by: architecture review session (qualiaDB integration + cooperative projects)

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

## Current architecture (as of 2026-06-03)

### Two apps, one engine

| App | Entry point | Purpose |
|---|---|---|
| **Privacy Vault** | `docs/vault.html` | PIN, sanctuary, Nym, meds, identity credentials, calls, cooperative projects, wallet |
| **Analytics Dashboard** | `docs/app.html` | Streamlit-in-browser ("Holographic Engine") — persona demos, health visualisations, Prolog inference, LLM |

Both share `docs/pkg/wellfare_core_bg.wasm` (282 KB, v0.0.4-dev).

### Engine: wellfare-core

- **Source**: `wellfare-core/` (Rust, cdylib, edition 2024) — at repo root
- **Built output**: `docs/pkg/wellfare_core.js` + `wellfare_core_bg.wasm` (3.3 MB with oxigraph; previously 282 KB without)
- **CI builds it**: `.github/workflows/pages.yml` — `cd wellfare-core && wasm-pack build --release --target web --out-dir ../docs/pkg`
- **Depends on**: `qualia-core-db` via git (`https://github.com/mediaprophet/qualiaDB.git`)

### Engine: qualiaDB (external repo)

- Repo: `https://github.com/mediaprophet/qualiaDB`
- v0.0.3; Rust workspace: `qualia-core-db`, `qualia-cli`, `qualia-desktop` (Tauri v1.5)
- `qualia-desktop` is Tauri v1.5 — must upgrade to v2 before mobile targets work
- `qualia-android` is Kotlin/Gradle + JNI — separate from Tauri, used as benchmark harness
- Android app has extensive modules: projects, identity/credentials, PFM, wallet, social, ontology — see TODO.md sections CP/PFM/CV/DIR for what needs porting

### Primary vault: Rust → Tauri v2 (decided this session)

The browser PWA (`vault.html`) is the current working implementation. The **target** is a Tauri v2 native app for iOS/Android where:
- vault.html + CSS is the WebView UI (preserved)
- All crypto, storage, and Nym operations move to Rust Tauri commands
- qualiaDB .q42 replaces IndexedDB as the primary store
- Nym Rust SDK replaces the WASM SDK (no SharedArrayBuffer headaches)

The browser PWA continues working as demo/fallback throughout the migration.

---

## Active branch

`feature/qualia-db-integration`

This branch has **no commits ahead of master**. All the integration work described here is in the working tree only (not committed). See section "Uncommitted working tree" below.

---

## Uncommitted working tree

The following files are modified but not committed. **Do not commit blindly — fix the CI path (0.1) first.**

**Modified (staged or unstaged):**
- `CLAUDE.md` — needs update to reflect decisions from this session
- `docs/vault.html` — qualiaDB integration + new panels
- `docs/connector/index.html` — integration updates
- `docs/js/vault-idb.js` — IDB v10 + dual-write scaffolding for QualiaStore
- `docs/js/vault-scheduler.js` — updates
- `docs/js/vault-wallet.js` — HCW-2 + Nym bandwidth
- `docs/js/vault-wasm.js` — qualiaDB bridge (loads wellfare_core.js, Lexicon, JSONtoQuinSerializer)

**Effectively deleted (moved to `legacy_pwa/`):**
- `extensions/` (Python N3 reasoner, SHACL validator)
- `src/` (Python PHR models)
- `scripts/` (Python build/generate scripts)
- `demo/` (persona JSON files)

**Note:** The N3 reasoning rules (`adrenal_fatigue.n3`, `cardiovascular_risk.n3`, `sleep_debt.n3`, `trauma_cascade.n3`) were in `extensions/n3_reasoner/rules/` — they now live at `legacy_pwa/extensions/n3_reasoner/rules/`. Their logic is still needed; see TODO A6.

---

## Key architectural decisions (locked — do not revisit without explicit instruction)

All decisions from `CLAUDE.md` still apply, plus:

1. **Rust-first for mobile** — primary vault is a Tauri v2 app; browser PWA is demo/fallback
2. **Two-app structure** — `vault.html` (privacy vault) and `app.html` (analytics) are separate products sharing the engine
3. **wellfare-core is the bridge crate** — it wraps qualia-core-db with health-specific WASM bindings and will have a native (non-WASM) target for Tauri
4. **Directory harmonization** — Verified Directory (`vault-directory.js`), qualiaDB SocialBook, and Cooperative Projects contributor list all resolve to the same `wf-contacts`/`wf-relationships` graph
5. **Lightning is the unified payment rail** — HCW welfare payments, cooperative obligation micropayments, and DA research bounties all use the same LDK node via Nym SOCKS5 proxy
6. **cooperative.html model adopted** — obligation matrix, Author-Scoped Merkle Signatures, µ-units, three-tier P2P sync, and PFM eight-phase architecture are all in scope for WellFair

---

## What is complete

See the "Completed" section at the bottom of `TODO.md` for the full list. Summary:
- All vault milestones M1–M6 (pairing, crypto, session, Nym scaffolding, sanctuary, hardening)
- All VC-7 through VC-15 (communications ecosystem: directory, handshake, gating, calls, scheduler, transcript, transcoding, package)
- WA-1 through WA-7 (Webizen Agent: CV workers, audio DSP, telemetry)
- HCW-1 and HCW-2 (wallet init + Nym bandwidth)
- DL-1 (barcode diet log scanner)
- wellfare-core WASM built and deployed
- Package manager (OPFS-based, prolog-wasm + llm-mediapipe)
- Device bridge (File System Access API)
- app.html Streamlit analytics dashboard

---

## What is blocked

| Item | Blocked by |
|---|---|
| All M tasks (Tauri mobile) | qualia-desktop Tauri v1→v2 migration (M1) |
| W2–W6 (real QualiaStore) | W4 needs oxigraph in Cargo.toml (W7) |
| CP4 P2P sync (Tier 1) | Nym activation (A3) |
| DA1–DA6 analytics | Phase 2 (directory + cooperative) must be stable first |
| HCW-3+ wallet | Rust Tauri command architecture (decided: Rust, blocked by M4–M6) |
| OC2 ontology ingestion | W4 WasmHealthStore + oxigraph (W7) |

**Cleared this session**: 0.1 CI path (fixed + committed), 0.2 working tree committed cleanly,
0.3 CLAUDE.md updated, W1 wellfare-core moved to repo root.

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
| **v11 (planned)** | wf-projects, wf-contributions, wf-obligations | CP epic |
| **v12 (planned)** | wf-credentials, wf-pfm-config, wf-ledger | CV + PFM epics |

---

## Module split for Tauri migration (M10)

When adapting `vault.html` JS modules for Tauri invoke():

| Module | Keep in JS WebView | Move to Tauri command |
|---|---|---|
| vault-crypto.js | — | entirely |
| vault-did.js | — | entirely |
| vault-idb.js | — | entirely (→ vault_put/get) |
| vault-nym.js | — | entirely |
| vault-wasm.js | — | eliminated |
| vault-sentinel.js | — | eliminated |
| noise-xx.js | Gun/WebRTC signalling | Noise_XX crypto ops |
| vault-sanctuary-pins.js | UI state machine | PIN verify/derive |
| vault-sanctuary-evidence.js | VP assembly UI | OTS + Ed25519 signing |
| vault-meds-reminders.js | UI rendering | IDB read via invoke() |
| vault-directory.js | UI rendering | storage via invoke() |
| vault-scheduler.js | UI rendering | job queue via invoke() |
| vault-wallet.js | UI rendering | storage + Nym via invoke() |
| vault-projects.js (new) | UI rendering | obligation accounting via invoke() |
| vault-credentials.js (new) | UI rendering | VC parse/VP gen via invoke() |
| vault-pfm.js (new) | UI rendering | ledger CRUD via invoke() |
| vault-mock.js | entirely (no change) | — |
| profiles.js | entirely (no change) | — |

---

## Key file locations

```
docs/
  vault.html              Primary vault app (phone)
  app.html                Analytics/Streamlit dashboard (512KB — read in chunks)
  app.js                  Analytics JS (wellfare_core + Pyodide + Chart.js)
  connector/index.html    Desktop connector (stateless)
  webconnect.html         WebRTC pairing bridge
  join.html               Call join page (guests)
  pair.html               Legacy monolithic page (keep as fallback)
  sw.js                   Service Worker (COOP/COEP headers)
  device-bridge.js        File System Access API for Samsung Health exports
  device-ui.js            Device sources UI controller
  package-download-ui.js  Package install overlay
  manifest.webmanifest    PWA manifest (needs start_url → vault.html, see P4)
  js/                     28 JS modules — see CLAUDE.md for full list
  pkg/                    Built WASM: wellfare_core.js + wellfare_core_bg.wasm (282KB)
  packages/               OPFS package manager (PackageManager, registry.json, capabilities.js)
  profiles/               access-profiles.ttl (SHACL), profiles.json
  pyodide/wellfair_demo.py Python analytics app (loaded by app.html stlite)
  sample_data/            Synthetic CSV files (4 types)
  models/                 .glb persona models (7 personas)

wellfare-core/          Rust WASM crate source (THE primary Rust code)
  Cargo.toml            v0.0.4-dev; depends on qualia-core-db via git
  src/
    wasm.rs             All wasm_bindgen exports
    qualia_bindings.rs  QualiaStore (STUB — needs W2/W3)
    rdf.rs              Turtle serializers (working)
    parser.rs           CSV parsers (working)
    models.rs           Rust data models

legacy_pwa/
  extensions/n3_reasoner/rules/  Four N3 clinical rules (needed for A6)
  src/                    Python PHR models
  expert-authoring-tool/  Medical paper parser + Prolog rule compiler
  user-runtime-lib/       Rule evaluation engine

instructions/
  HANDOVER_CURRENT.md     THIS FILE
  COMMS_EPIC_PLAN.md      VC-7 through VC-15 implementation plan
  EPIC_PLAN_v0.0.7.md     WA + HCW epic plan
  ANALYTICS_EPIC_PLAN.md  DA/RC analytics epic plan
  BROWSER_COMPAT.md       Real-device test matrix

TODO.md                   MASTER TODO (repo root) — update alongside this file
CLAUDE.md                 Project orientation (mandatory reading every session)
.github/workflows/pages.yml  CI — builds wellfare-core WASM + Stlite + deploys GitHub Pages
```

---

## Cooperative projects: what was decided

The `cooperative.html` page and the Android app modules (`projects/`, `identity/`, `pfm/`, `wallet/`, `social/`, `ontology/`) define a complete system that needs to be integrated into WellFair:

- **Cooperative Projects panel** in vault.html (CP1–CP6)
- **Personal Finance Management** module (PFM1–PFM9)
- **Credential Vault** panel with Maslow VP selective disclosure (CV1–CV5)
- **Directory harmonization** — Verified Directory + SocialBook + cooperative contributor list are one unified contact graph (DIR1–DIR4)
- **Ontology Converter** in app.html analytics dashboard (OC1–OC3)
- **Lightning** is the unified payment rail for welfare payments (HCW), obligation micropayments (cooperative), and research bounties (DA)

The obligation model: contributor hours → µ-units → obligation cost. Three fulfilment paths: Lightning micropayments, donations, sponsorship. All tracked via Author-Scoped Merkle Signatures (Ed25519-signed Merkle chain, like git commits).

---

## Demo account

- **PIN**: `1234`
- `vault.html?demo` — skips PIN, loads mock data (UI-only testing)
- `vault.html` with PIN `1234` — full owner vault with real IDB persistence
- Dev server: `python -m http.server 3000 --directory docs`
- Testing: always use `mcp__Claude_in_Chrome__*` tools — Claude app preview lacks WebCrypto

---

## What to do next (suggested first session after this handover)

1. Fix 0.1 (CI path) — 15 min
2. Commit working tree cleanly as two commits (0.2) — 20 min
3. Update CLAUDE.md (0.3) — 20 min
4. Move wellfare-core to repo root (W1) and verify CI still builds — 30 min
5. Then: either start W2–W7 (complete QualiaStore + SPARQL + SHACL) OR start CP1 (cooperative projects panel) depending on priority

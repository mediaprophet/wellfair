# WellFair — Current Handover
> **Living document — update this at the end of every session.**  
> Last updated: 2026-06-04  
> Updated by: sessions 2–3 (W1–W7 Rust engine) + session 4 (CP1–CP3,CP5 + W6,A6)

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

Both share `docs/pkg/wellfare_core_bg.wasm` (3.3 MB, v0.0.4-dev + oxigraph).

### Engine: wellfare-core

- **Source**: `wellfare-core/` (Rust, cdylib, edition 2024) — at repo root
- **Built output**: `docs/pkg/wellfare_core.js` + `wellfare_core_bg.wasm` (3.3 MB with oxigraph; previously 282 KB without)
- **CI builds it**: `.github/workflows/pages.yml` — `cd wellfare-core && wasm-pack build --release --target web --out-dir ../docs/pkg`
- **qualia-core-db** is now an **optional** Cargo feature (`--features qualia`); it uses `wgpu` which is heavy for WASM so it is excluded from the default build. Enable when implementing W10.
- **New modules**: `store.rs` (HealthStore/oxigraph), `shapes.rs` (SPARQL ASK constraints), `qualia_bindings.rs` (functional QualiaStore)
- **New WASM exports**: `WasmHealthStore` (new/load_turtle/query), `validate_health_turtle()`, `QualiaStore` (insert_quin/query_subject/query_predicate/query_context/len/clear)

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

`feature/qualia-db-integration` — **6 commits ahead of master, all pushed to origin.**

| Commit | What |
|---|---|
| `70f5bb6` | Cleanup: legacy Python/Rust → `legacy_pwa/`; CI fix; `TODO.md`; instruction docs |
| `dd9a5a3` | Integration: `vault-wasm.js` qualiaDB bridge, IDB v10, `vault-sentinel.js`, `CLAUDE.md` |
| `20c5f80` | W1: `wellfare-core/` at repo root; CI path restored |
| `2a6c00f` | Docs: handover prompt session 2 |
| `b1814e9` | W2–W7: real QualiaStore, WasmHealthStore SPARQL, SHACL validation; WASM rebuilt |
| `44df0ea` | Docs: handover prompt session 3 |

**Working tree: clean** (only `32-02.url` untracked Windows shortcut — ignore).

**N3 rules note:** `adrenal_fatigue.n3`, `cardiovascular_risk.n3`, `sleep_debt.n3`, `trauma_cascade.n3` now live at `legacy_pwa/extensions/n3_reasoner/rules/`. Their logic is still needed; see TODO A6.

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
- **W1** — wellfare-core at repo root; CI path correct
- **W2/W3** — QualiaStore: functional Vec<[u64;5]> store; insert/query all working; BigInt-safe
- **W4** — WasmHealthStore: oxigraph-backed; SPARQL SELECT/ASK/CONSTRUCT via load_turtle()/query()
- **W5** — validate_health_turtle(): 6 SPARQL ASK health shape constraints; JSON report
- **W7** — oxigraph added to Cargo.toml; qualia-core-db moved to optional `qualia` feature
- wellfare-core WASM rebuilt to 3.3 MB; all exports verified in .d.ts
- Package manager (OPFS-based, prolog-wasm + llm-mediapipe)
- Device bridge (File System Access API)
- app.html Streamlit analytics dashboard
- **CP1** — `docs/js/vault-projects.js` created; "🤝 Projects" nav button + bottom-sheet in vault.html; IDB v11 with `wf-projects`, `wf-contributions`, `wf-obligations`
- **CP2** — Author-Scoped Merkle Signature: `sha256(prevHashBytes ‖ JSON{hours,description,timestamp})` in `logContribution()`; chain integrity verified
- **CP3** — µ-unit balance: `totalHours × ratePerHour × 1000`; stored in `wf-obligations`; per-project and global summary in UI
- **CP5** — IDB v11 stores added (wf-projects, wf-contributions, wf-obligations); all encrypted via AES-GCM `_sEnc/_sDec`; dual-write to QualiaStore via existing `_dbPut` hook
- **vault-wasm.js** — `exportVaultToTurtle()` includes cooperative project RDF; `evaluateVaultN3Rules()` convenience wrapper
- **W6** — `sentinel.rs`: SentinelVM with extended opcodes (LessThan/GreaterThan/LoadFloat); `validate_health_quin(constraint,s,p,o,c,m)` evaluates 3 policy gates: `cooperative_obligation` (lane 1), `guardian_identity` (lane 2), `commercial_block` (lane 2). No wgpu dependency.
- **A6** — `n3_rules.rs`: 7 clinical patterns from 4 N3 files translated to SPARQL-aggregation queries over oxigraph. `evaluate_n3_rules(turtle)` WASM export returns triggered patterns with routingLane. `rdf.rs` adds `health:sleepHours` numeric property to sleep Turtle.
- **vault-sentinel.js** — real implementation: `SentinelCompiler.classify()`, `evaluatePolicyConstraint()`, `evaluateN3Rules()`, `evaluateVaultN3Rules()`

---

## What is blocked

| Item | Blocked by |
|---|---|
| All M tasks (Tauri mobile) | qualia-desktop Tauri v1→v2 migration (M1) |
| W10 (compile_query_to_json) | qualia-core-db optional feature `--features qualia` — needs validation |
| CP4 P2P sync (Tier 2 Gun) | Gun/WebRTC available; Tier 1 (Nym) blocked on A3 |
| CP6 Project directory feed | needs Nym activation (A3) or Gun signalling node |
| W8 (dual-target Cargo) | M2 Tauri app crate doesn't exist yet |
| W10 (compile_query_to_json) | qualia-core-db optional feature needs validation |
| CP4 P2P sync (Tier 1) | Nym activation (A3) |
| DA1–DA6 analytics | Phase 2 (directory + cooperative) must be stable first |
| HCW-3+ wallet | Rust Tauri command architecture (decided: Rust, blocked by M4–M6) |
| OC2 ontology ingestion | ~~W4 WasmHealthStore + oxigraph~~ **UNBLOCKED** — W4 complete |

**Cleared sessions 2+3**: 0.1–0.3 CI/commit/CLAUDE.md, W1 crate location, W2–W5 and W7 Rust engine.

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
| **v11** | wf-projects, wf-contributions, wf-obligations | CP1/CP5 |
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
  pkg/                    Built WASM: wellfare_core.js + wellfare_core_bg.wasm (3.3 MB)
  packages/               OPFS package manager (PackageManager, registry.json, capabilities.js)
  profiles/               access-profiles.ttl (SHACL), profiles.json
  pyodide/wellfair_demo.py Python analytics app (loaded by app.html stlite)
  sample_data/            Synthetic CSV files (4 types)
  models/                 .glb persona models (7 personas)

wellfare-core/          Rust WASM crate source (THE primary Rust code)
  Cargo.toml            v0.0.4-dev; oxigraph 0.4 (default); qualia-core-db optional feature "qualia"
  src/
    wasm.rs             All wasm_bindgen exports (includes WasmHealthStore, validate_health_turtle)
    qualia_bindings.rs  QualiaStore — functional Vec<[u64;5]> store (W2/W3 complete)
    store.rs            HealthStore backed by oxigraph (W4 complete)
    shapes.rs           6 SPARQL ASK health constraints (W5 complete)
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

## What to do next

**CP1–CP3, CP5 + W6 + A6 complete.** Key remaining:

- **OC1** (recommended) — Ontology Converter panel in `app.html`. File picker → Turtle/JSON-LD → N-Quads via WasmHealthStore. Now fully unblocked. See TODO.md §OC.
- **DIR1** — Unified contact graph: add `wf:coContributor` relationship type to `vault-directory.js`
- **CP4** — `vault-p2p-sync.js` Tier 2 (Gun+WebRTC available now); Tier 1 Nym blocked on A3
- **N3 UI** — surface `evaluateVaultN3Rules()` results in the vault (Health Insights panel or Biometrics sheet). Currently working but not displayed to user.
- **W10** — wire `compile_query_to_json` from `qualia-core-db` (`--features qualia`) once WASM-safe path confirmed

Read first: `TODO.md` sections OC, DIR, CP, W.

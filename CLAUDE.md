# WellFair — Claude Code Orientation

## What this project is

A privacy-first personal health vault. The phone is the authoritative vault; the desktop
is a stateless terminal. Data flows phone → desktop over an end-to-end-encrypted WebRTC
DataChannel. Nothing is stored on the desktop — closing the tab destroys everything.

## Terminology (mandatory)

- **Identity credentials** — not "DIDs", not "VCs". Technical spec names (did:key, did:peer,
  W3C VC Data Model) may appear in technical contexts, but the *concept* is always
  "identity credentials".
- **SHACL/RDFS shapes** for data about people — never OWL class membership.
  OWL is used only for policy artefacts (EdgeConstraint etc.), never for a person or
  their health data.
- Health data namespace: `wf:` → `https://wellfare.social/ns/vault#`

## Architecture (locked — do not revisit without explicit instruction)

1. Phone is authoritative vault; desktop is always stateless
2. Gun.eco for WebRTC signalling only — health data never touches Gun relay nodes
3. SHACL for data shapes; OWL only for policy artefacts, never for people
4. `did:peer` per pairing, `did:key` for ephemeral sessions (no shared long-term identifier)
5. Nym for anonymous routing (not real-time calls); WebRTC for all live sessions
6. ODRL EdgeConstraints from `docs/profiles/access-profiles.ttl` govern receiver permissions
7. "Identity credentials" is the canonical term for what specs call DIDs + VCs
8. **Tauri v2 is the target mobile platform** — `vault.html` WebView is the UI shell; Rust
   Tauri commands handle all crypto, storage, and Nym operations on device. Browser PWA
   continues working as demo/fallback throughout the migration.
9. **wellfare-core is the bridge crate** (`legacy_pwa/wellfare-core/`, will move to root per W1)
   — wraps `qualia-core-db` (qualiaDB) with health-specific WASM bindings. Dual-target:
   WASM for browser, native for Tauri. Current WASM is v0.0.4-dev, deployed to `docs/pkg/`.
10. **qualiaDB** (`https://github.com/mediaprophet/qualiaDB`) is the primary storage engine
    — `.q42` files replace IndexedDB once the Tauri migration is complete.
11. **Two-product structure**: `vault.html` (Privacy Vault, phone) + `app.html` (Analytics
    Dashboard, any browser) — both share the `docs/pkg/wellfare_core_bg.wasm` engine.
12. **Lightning + Nym is the unified payment rail** — HCW welfare payments, cooperative
    obligation micropayments (µ-units), and DA research bounties all use the same LDK node
    routed via Nym SOCKS5 proxy.
13. **Cooperative projects, PFM, Credential Vault, and Directory harmonization are in scope**
    — see TODO.md sections CP, PFM, CV, DIR. The `cooperative.html` obligation model
    (µ-units, Author-Scoped Merkle Signatures, three-tier P2P sync) is adopted for WellFair.

## Current state (as of 2026-06-03) — branch feature/qualia-db-integration

### Architecture pivot (decided 2026-06-03)

Primary vault target is a **Tauri v2 native app** (iOS/Android) with `vault.html` as the
WebView UI shell and Rust Tauri commands for crypto/storage/Nym. Browser PWA continues working
as demo/fallback. `qualiaDB` (`.q42` store) replaces IDB as primary storage once Tauri migration
is complete. See `TODO.md` for the full task breakdown (sections W, M, CP, PFM, CV, DIR, DA).

### Code-complete features

- **M1–M6**: WebRTC QR pairing · Noise_XX E2E (Ed25519/X25519 WebCrypto) · session TTL/BFCache
  · Nym scaffolding (SURB pool, fragments, DMS, anon notify) · Sanctuary Mode + Duress (PBKDF2,
  IDB namespace, decoy vault, Unvarnished Log) · hardening (Tripwire, Synthesis Engine,
  Evidentiary Export + OTS Bitcoin anchoring, browser compat guard)
- **VC-7 – VC-15**: Verified Directory · Semantic Handshake · Inbound Caller Gating ·
  Hypermedia Voice/Video (vault↔vault + guest join.html) · Web Connector · Background Job
  Scheduler · Event Log & Transcript (RDFa + Merkle chain) · Language Transcoding ·
  Content Package (JSON-LD manifest + ODRL-permissioned zip + OTS anchor)
- **WA-1 – WA-7**: AgentController · cv-emotion MediaPipe worker · audio DSP worker ·
  IDB v7 telemetry · connector Live Indicators · transcript BiometricTelemetryLog
- **HCW-1, HCW-2**: vault-wallet.js init · Nym bandwidth abstraction (ensureNymBandwidth)
- **DL-1**: barcode diet-log scanner (BarcodeDetector + ZXing fallback + Open Food Facts)
- **wellfare-core WASM v0.0.4-dev** built + deployed to `docs/pkg/` (282 KB)
- **app.html** Streamlit analytics dashboard (512 KB — read in chunks with offset/limit)
- **Package manager** (OPFS-based, handles oxigraph/prolog-wasm/llm-mediapipe installs)
- **Device bridge** (File System Access API for Samsung Health `.zip` exports)

### Remaining runtime-only tasks (no code needed)

- **Nym Sandbox validation**: run `docs/nym-test.html` against testnet; set `NYM_SDK_URL`
  in `docs/js/vault-nym.js`. Sandbox API: `https://sandbox-nym-api1.nymtech.net/api`.
- **Real-device testing**: iOS Safari, Android Chrome, Firefox 130+ — matrix in
  `instructions/BROWSER_COMPAT.md`.
- **SURB stress test**: airplane-mode toggle while Nym active; verify 30 s fragment expiry.

### Planned epics (see TODO.md for tasks)

| Section | Epic | Status |
|---|---|---|
| W | wellfare-core Rust crate — real QualiaStore, SPARQL, SHACL | Not started |
| M | Tauri v2 mobile app | Blocked on qualia-desktop v1→v2 upgrade |
| CP | Cooperative Projects panel (µ-units, Merkle signatures) | Not started |
| PFM | Personal Finance Management (double-entry ledger, receipts, OFX export) | Not started |
| CV | Credential Vault (VC wallet, Maslow VP, guardianship) | Not started |
| DIR | Directory harmonization (Verified Directory + SocialBook + cooperative contacts) | Not started |
| OC | Ontology Converter in app.html | Not started |
| DA | Distributed Analytics & Research Commons | Not started |
| HCW-3+ | Human-Centric Wallet (blind proxy, ZK credentials, LDK Lightning) | Blocked on Tauri |

See `instructions/COMMS_EPIC_PLAN.md` · `instructions/ANALYTICS_EPIC_PLAN.md` ·
`instructions/EPIC_PLAN_v0.0.7.md` for full specs.

## Key files

```
docs/
  vault.html             Primary phone vault (PIN → meds, sanctuary, DMS, anon notify,
                         Directory, Calls, Queue, Wallet, Analytics stub)
  app.html               Analytics Dashboard — Streamlit/stlite (512 KB; read in chunks)
  webconnect.html        WebRTC pairing bridge (phone side — QR → profile → consent → serve)
  connector/index.html   Desktop connector (stateless — Noise initiator, Ed25519 verify)
  join.html              Lightweight call join page (guest or vault user)
  pair.html              LEGACY — original monolithic page, kept as working fallback
  nym-test.html          Nym SDK validation harness — run before activating NYM_SDK_URL
  sw.js                  Service Worker — injects COOP/COEP for Nym SharedArrayBuffer
  device-bridge.js       File System Access API for Samsung Health exports
  pkg/                   Built WASM: wellfare_core.js + wellfare_core_bg.wasm (282 KB)
  profiles/
    access-profiles.ttl  SHACL access profile shapes (canonical)
    profiles.json        JS-loadable profile registry
  js/
    vault-idb.js               IDB helpers + store constants (v10 = wf-lexicon)
    vault-crypto.js            Key derivation, AES-GCM, commitments, toB64/fromB64
    vault-did.js               did:key (Ed25519) generation
    vault-nym.js               Nym adapter, DMS, anonymous notification
    vault-wasm.js              qualiaDB WASM bridge (QualiaStore, Lexicon, SPARQL stub)
    vault-sentinel.js          Sentinel VM stub (constraint evaluation)
    vault-mock.js              Mock vault data + SECTION_LABELS
    vault-directory.js         VC-7 — contact graph, FOAF-inspired, encrypted IDB
    vault-handshake.js         VC-8 — Semantic Handshake, ODRL agreement signing
    vault-comms-gate.js        VC-9 — inbound caller gating, Nym+Gun dual transport
    vault-comms-call.js        VC-10 — call session, WebRTC media, link gen, guest cred
    vault-cv.js                VC-10 — OpenCV placeholder (emotion recognition, pulse)
    vault-scheduler.js         VC-12 — background job queue engine
    vault-transcript.js        VC-13 — event log → HTML+RDFa transcript
    vault-comms-transcode.js   VC-14 — language transcoding, 3-tier progressive
    vault-package.js           VC-15 — content package + JSON-LD manifest
    vault-sanctuary-pins.js    PIN state machine, canary/setup, duress check, wake lock
    vault-sanctuary-log.js     Unvarnished Log, Tripwire Dashboard, Synthesis Engine
    vault-sanctuary-evidence.js  Evidentiary Export, VP generation, OpenTimestamps
    vault-meds-reminders.js    MedNotifier, today schedule, take/skip, reminder panel
    vault-meds-lod.js          SUBSTANCE_INTERACTIONS, RxNorm/Wikidata, interaction engine
    vault-meds-manager.js      Add/cease medication sheet
    vault-wallet.js            HCW-1/2 — Lightning wallet init + Nym bandwidth
    vault-analytics.js         DA-1/2 stub — StudyCredential parser, N3 evaluator, consent
    vault-dp.js                DA-3 stub — Local Differential Privacy (Randomized Response)
    noise-xx.js                Noise_XX_25519_AESGCM_SHA256 (webconnect only)
    profiles.js                Profile loading, rendering, emergency pre-auth (webconnect only)

legacy_pwa/wellfare-core/      Rust WASM crate source (THE primary Rust code — moves to root W1)
  Cargo.toml                   v0.0.4-dev; depends on qualia-core-db via git
  src/
    wasm.rs                    All wasm_bindgen exports
    qualia_bindings.rs         QualiaStore stub (needs W2/W3)
    rdf.rs                     Turtle serialisers (working)
    parser.rs                  CSV parsers (working)
    models.rs                  Rust data models

mobile/                        Android Kotlin/Gradle scaffold (Jetpack Compose + JNI)
  app/src/main/java/com/example/wellfair/
    QualiaCliService.kt        qualiaDB daemon service stub
    NymMixnet.kt               Nym integration stub

instructions/
  HANDOVER_CURRENT.md          Living handover — update at end of every session
  HANDOVER_PROMPT.md           Session start prompt — copy into any new session
  ANALYTICS_EPIC_PLAN.md       DA/RC epic — distributed analytics + research creator
  COMMS_EPIC_PLAN.md           VC-7 to VC-15 implementation plan
  EPIC_PLAN_v0.0.7.md          WA + HCW epic plan
  BROWSER_COMPAT.md            Real-device test matrix
  VAULT_CONNECTOR_NEXT_STEPS.md  v0.0.5 milestone checklist

TODO.md                        Master task list (W, M, A, CP, PFM, CV, DIR, OC, R-CP, P, DA)
```

## Dev server

```
python -m http.server 3000 --directory docs
```
- Phone/daily vault: `http://localhost:3000/vault.html`
- Demo mode (no PIN): `http://localhost:3000/vault.html?demo`
- Desktop pairing: `http://localhost:3000/webconnect.html` (phone) + `http://localhost:3000/connector/` (desktop)
- Legacy: `http://localhost:3000/pair.html` (original monolithic page — still works)

## Testing — MANDATORY

**Always use the `mcp__Claude_in_Chrome__*` tools against a real Python dev server.**
The Claude app preview environment does not support WebCrypto (Ed25519/X25519), IndexedDB
writes, or Service Worker registration. Any test that touches encryption, the vault PIN,
IDB persistence, or the Nym adapter MUST be run via the Chrome Claude extension.

**Demo account PIN: `1234`**
- `vault.html?demo` skips PIN entirely and loads mock data — use for UI-only checks.
- `vault.html` with PIN `1234` is the full owner vault with real IDB persistence.
- The phone (`vault.html`) is the authoritative datastore; the desktop connector
  (`connector/index.html`) is stateless — it holds nothing after the tab closes.

Typical test flow:
1. Start dev server: `python -m http.server 3000 --directory docs`
2. Open `http://localhost:3000/vault.html` in Chrome via `mcp__Claude_in_Chrome__navigate`
3. Enter PIN `1234` to unlock owner workspace
4. Verify feature, check console via `mcp__Claude_in_Chrome__read_console_messages`

## Related external repos

- **mediaprophet/qualiaDB** — primary storage engine: `qualia-core-db` (Rust), `qualia-desktop`
  (Tauri v1.5 → v2 upgrade needed), `qualia-android` (Kotlin/JNI benchmark harness)
- **WebCivics/ontologies** (`2023` branch): `ttl/un/udhr.ttl`, `ttl/w3c/odrl.ttl` — rights instruments
- **mediaprophet/Episteme**: `custom-addons/rights-ontology.ttl` — defines `webizen:EdgeConstraint` etc.
- **Nym SDK**: `@nymproject/sdk-full-fat` — requires SharedArrayBuffer (COOP/COEP headers), cold start 3–8s
  On Tauri path, the Nym Rust SDK replaces this entirely (no SharedArrayBuffer requirement).

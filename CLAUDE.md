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

## Current state (as of 2026-05-30) — branch release/v0.0.6

### Completed
- **Milestone 1 (partial)** — WebRTC QR pairing, Gun signalling, DataChannel, 9 access profiles
  (SHACL TTL + JSON), owner workspace (docs/drag-drop, notes, mental health, social context),
  mock vault data, accessibility controls. *Polish deferred to Milestone 6.*
- **Milestone 2 (complete)** — Full identity credentials + Noise_XX encrypted channel:
  - Ed25519 `did:key` per session (both sides) via WebCrypto
  - X25519 static keys for Noise_XX_25519_AESGCM_SHA256 handshake
  - All DataChannel traffic AES-256-GCM encrypted after handshake
  - Vault signs every response with Ed25519; desktop verifies before rendering
  - Session keys are non-extractable CryptoKey objects; nulled on teardown
- **Milestone 3 (complete)** — Ephemeral sharing flow polish:
  - Session TTL (30 min, configurable) — vault overwrites Gun session node on expiry
  - `beforeunload` / `pagehide` (BFCache eviction) / `visibilitychange` (2-min grace) on connector
  - `FinalizationRegistry` in both files confirms session `CryptoKey` GC after teardown
  - Emergency pre-auth UI on phone (owner mode) — pre-approve profiles before an incident
  - Full ISO timestamp + accessor `did:key` in phone audit log for emergency sessions
  - Legal Advocate section picker — shows only profile sections, all unchecked by default
  - Connector sends its `did:key` in `hello` message so vault can record it in audit log
- **Milestone 4 (scaffolded — one activation step remaining)** — Nym Mixnet Integration:
  - `sw.js` injects `COOP: same-origin` + `COEP: require-corp` on all same-origin responses
  - Both `pair.html` and `connector/index.html` register `/sw.js` at startup; CDN scripts
    have `crossorigin="anonymous"` for COEP compatibility
  - `docs/nym-test.html` — standalone SDK validation harness (run this first)
  - `nymAdapter.send()` in `pair.html` — Gun `nym/` namespace adapter: routes vault outbound
    via Nym instead of Gun relay nodes; fragments payloads > 28 KB (Sphinx limit)
  - Fragment reassembly buffer keyed on `(msg_id, fragment_idx)`, 30 s expiry
  - SURB pool: `surbBudget = 20`, 3 attached per message, replenish when < 5
  - Dead Man's Switch UI (owner mode): configurable interval, two trustee Nym addresses,
    check-in / test-fire; fires `dmsFire()` → `nymAdapter.send()` to trustees on miss
  - Anonymous notification UI (owner mode): compose + send via Nym, no WebRTC
  - **Remaining activation step**: run `docs/nym-test.html` against Nym Sandbox testnet,
    confirm SDK loads and cold-start time, then set `NYM_SDK_URL` constant in `pair.html`.
    Sandbox API: `https://sandbox-nym-api1.nymtech.net/api` — test tokens from Nym Discord.
- **Milestone 5 (complete — core flow)** — Sanctuary Mode & Duress. All in `docs/pair.html`:
  - `deriveVaultKey(pin, salt)` — PBKDF2-SHA256, 310 000 iterations; three independent keys:
    sanctuary (`_SANC_SALT`), duress (`_DURS_SALT`), main-vault slot (`_MAIN_SALT`) reserved
  - Sanctuary IndexedDB namespace: DB `wf-vault` v2, stores `wf-s` (entries) + `wf-sc` (config);
    no string `"sanctuary"` in any store name or key; all entries AES-256-GCM encrypted
  - DLT commitment anchor: `commitment = sha256(sha256(entry) ‖ nonce)` computed before IDB
    write; nonce + commitment stored locally; commitment logged to console ready to publish
  - Decoy vault: duress PIN at owner PIN step opens identical owner workspace, fires silent
    Nym alert to configured contacts, suppresses `⚫ Sanctuary Mode` panel completely
  - Sanctuary workspace (`step-sanctuary`): dark-theme UI via `body.sanctuary-active` CSS
    variable override; first-use setup flow (sanctuary PIN → confirm → duress PIN → confirm);
    Unvarnished Log (Veiled Assertions + Hypothesis Nodes); Contingency Protocols panel
    (duress contact management, contacts encrypted under duress key)
  - `pinKey()` now async; duress check via `_checkAndFireDuress()` before returning wrong-PIN

  Deferred to M6: Tripwire Dashboard, Synthesis Engine, Evidentiary Export / VP generation,
  actual DLT write for commitment anchors.

### Milestone 6 — Hardening & Cross-Browser  *(code-complete as of 2026-05-30)*

Completed: Gun write audit (clean), connector storage audit (clean), PWA manifest wired to
`pair.html`, Wake Lock API, relay unreachable handling, Gun signalling cleanup post-handshake,
Tripwire Dashboard, Synthesis Engine, Evidentiary Export (VP + commitment manifest download),
browser compatibility guard (Ed25519 + X25519 WebCrypto feature detection on startup in both
`pair.html` and `connector/index.html`), Bitcoin commitment anchoring via OpenTimestamps
(feeless, anonymous — each commitment is one Merkle-tree leaf; `.ots` proof files downloadable;
per-entry `pending` → `confirmed` state tracked in IDB; silent upgrade on sanctuary unlock).

Remaining (runtime/device — no code tasks): real-device testing (see
`instructions/BROWSER_COMPAT.md`), SURB stress test, Nym Sandbox validation + `NYM_SDK_URL`
activation in `pair.html`.

See `instructions/VAULT_CONNECTOR_NEXT_STEPS.md` for the v0.0.5 checklist.
See `instructions/COMMS_EPIC_PLAN.md` for the v0.0.6 implementation plan (VC-7 through VC-15).

### Carry-over from v0.0.5 (not yet done)

**Needs code:**
- **Medication Sprint 6 — diet log**: `wf-dl` IDB store exists but UI and capture logic not built.
  Lives in `docs/js/vault-meds-manager.js` or a new `vault-diet.js`. Lower priority than comms epic;
  pick up when a session has capacity.
  **Review first:** https://github.com/ouisharelabs/food-dashboard — prior art for food taxonomy,
  data models, and nutrient schema; may inform `wf-dl` record structure.
- **Demo connector auto-connect**: `connector/index.html` should detect an active vault Gun session
  and offer one-click connect (no manual QR scan) for dev/demo use. Small task, ~50 lines.

**Runtime / device only (no code):**
- **Nym Sandbox validation**: run `docs/nym-test.html` against Nym Sandbox testnet; set
  `NYM_SDK_URL` constant in `docs/js/vault-nym.js`. Sandbox API: `https://sandbox-nym-api1.nymtech.net/api`.
- **Real-device testing**: iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md`.
- **SURB stress test**: airplane-mode toggle while Nym client active; verify fragment expiry + replenish.

### Milestone 7+ — Verifiable Communications Ecosystem *(v0.0.6-dev, in progress)*

New epic. See `instructions/COMMS_EPIC_PLAN.md` for full spec and session-by-session plan.
Short summary of what will be built:
- **VC-7** Verified Directory (contact graph, SHACL, encrypted IDB)
- **VC-8** Semantic Handshake (ODRL agreement, did:peer, Ed25519 signed)
- **VC-9** Inbound Caller Gating (Nym+Gun dual transport, VC verification before ring)
- **VC-10** Hypermedia Voice/Video (Topology A vault↔vault; Topology B guest link via join.html)
- **VC-11** Web Connector (live data sharing during calls, signed VP receipts)
- **VC-12** Background Job Scheduler (condition-triggered queue: idle/charging/desktop/manual)
- **VC-13** Event Log & Transcript (HTML+RDFa, Merkle event chain, participant revision signing)
- **VC-14** Language Transcoding (3-tier progressive STT+translation, provenance RDFa)
- **VC-15** Content Package (JSON-LD manifest, ODRL-permissioned zip, OTS anchor)

## Key files

```
docs/
  vault.html             Daily-use vault (PIN → meds, sanctuary, DMS, anon notify)
                         v0.0.6: + Directory, Calls, Queue panels
  webconnect.html        WebRTC pairing bridge (QR scan → profile → consent → serving)
  connector/index.html   Desktop connector (Noise initiator, Ed25519 verify)
                         v0.0.6: + Calls nav section
  join.html              NEW v0.0.6 — lightweight call join page (guest or vault user)
  pair.html              LEGACY — original monolithic page, kept as working fallback
  nym-test.html          Nym SDK validation harness — run before activating NYM_SDK_URL
  js/
    vault-idb.js               IDB helpers + store constants (v4+ in v0.0.6)
    vault-crypto.js            Key derivation, AES-GCM, commitments, toB64/fromB64
    vault-did.js               did:key (Ed25519) generation
    vault-nym.js               Nym adapter, DMS, anonymous notification
    vault-mock.js              VAULT mock data + SECTION_LABELS
    vault-directory.js         NEW VC-7 — contact graph, FOAF-inspired, encrypted IDB
    vault-handshake.js         NEW VC-8 — Semantic Handshake, ODRL agreement signing
    vault-comms-gate.js        NEW VC-9 — inbound caller gating, Nym+Gun dual transport
    vault-comms-call.js        NEW VC-10 — call session, WebRTC media, link gen, guest cred
    vault-cv.js                NEW VC-10 — OpenCV placeholder (emotional recognition, pulse)
    vault-scheduler.js         NEW VC-12 — background job queue engine
    vault-transcript.js        NEW VC-13 — event log → HTML+RDFa transcript
    vault-comms-transcode.js   NEW VC-14 — language transcoding, 3-tier progressive
    vault-package.js           NEW VC-15 — content package + JSON-LD manifest
    vault-sanctuary-pins.js    PIN state machine, canary/setup, duress check, wake lock
    vault-sanctuary-log.js     Unvarnished Log, Tripwire Dashboard, Synthesis Engine
    vault-sanctuary-evidence.js  Evidentiary Export, VP generation, OpenTimestamps
    vault-meds-reminders.js    MedNotifier, today schedule, take/skip, reminder panel
    vault-meds-lod.js          SUBSTANCE_INTERACTIONS, RxNorm/Wikidata, interaction engine
    vault-meds-manager.js      Add/cease medication sheet
    noise-xx.js                Noise_XX_25519_AESGCM_SHA256 (webconnect only)
    profiles.js                Profile loading, rendering, emergency pre-auth (webconnect only)
  profiles/
    access-profiles.ttl  SHACL access profile shapes (canonical); v0.0.6 adds Contact/Relationship shapes
    profiles.json        JS-loadable profile registry
  sw.js                  Service Worker — injects COOP/COEP for Nym SharedArrayBuffer

instructions/
  COMMS_EPIC_PLAN.md              v0.0.6 implementation plan — VC-7 to VC-15, session breakdown
  VAULT_CONNECTOR_NEXT_STEPS.md   v0.0.5 milestone checklist + architecture notes
  sanctuaryMode.md                Sanctuary Mode full specification (Milestone 5)
  BROWSER_COMPAT.md               Storage/Gun write audit results + real-device test matrix
```

## Dev server

```
python -m http.server 3000 --directory docs
```
- Phone/daily vault: `http://localhost:3000/vault.html`
- Desktop pairing: `http://localhost:3000/webconnect.html` (phone) + `http://localhost:3000/connector/` (desktop)
- Legacy: `http://localhost:3000/pair.html` (original monolithic page — still works)

## Related external repos

- **WebCivics/ontologies** (`2023` branch): `ttl/un/udhr.ttl`, `ttl/w3c/odrl.ttl` — rights instruments
- **mediaprophet/Episteme**: `custom-addons/rights-ontology.ttl` — defines `webizen:EdgeConstraint` etc.
- **Nym SDK**: `@nymproject/sdk-full-fat` — requires SharedArrayBuffer (COOP/COEP headers), cold start 3–8s

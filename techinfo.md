# WellFair — Technical Reference

*Technical implementation reference — see [README.md](README.md) for project overview.*

**v0.0.6-dev** (31 May 2026)

---

## Architecture

WellFair has two complementary layers:

### 1. Privacy Vault (primary — v0.0.4+)

The vault is a phone-first, zero-server, end-to-end encrypted personal health vault. The phone is the authoritative data store; the desktop is a stateless terminal. All session data is destroyed when the tab closes.

```
Phone (vault.html — vault)                Desktop (connector/index.html — terminal)
──────────────────────────────────        ─────────────────────────────────────────
WebCrypto Ed25519 did:key (ephemeral)     WebCrypto Ed25519 did:key (ephemeral)
X25519 static key (Noise_XX)             X25519 static key (Noise_XX)
│                                        │
└──── WebRTC DataChannel ────────────────┘
      Noise_XX_25519_AESGCM_SHA256
      AES-256-GCM per message

Gun.eco ─── WebRTC signalling only (health data never touches relay nodes)
Nym Mixnet ─ anonymous routing for non-real-time messages (DMS, notifications)
```

**Phone vault holds:**
- Health records (encrypted at rest, AES-256-GCM)
- Identity credentials (did:key per session, did:peer per pairing)
- Verified Directory (contact graph, encrypted IDB)
- Sanctuary Mode entries (double-encrypted, PBKDF2 key derivation)
- Audit log (every accessor, timestamp, did:key)

**Desktop terminal is stateless** — no IndexedDB writes, no cookies, no persistence. Closing the tab destroys all session state.

### 2. Semantic Health Core (legacy — v0.0.3)

The original WASM/Streamlit data analysis layer, still available for local research use:

```
Browser (WASM — runs on device)          Optional local extensions (Python)
────────────────────────────────         ──────────────────────────────────
wellfare-core (Rust → WASM)              extensions/
  ├── CSV → Turtle (RDF)                   ├── hra_client/   HuBMAP SPARQL
  ├── oxigraph RDF store + SPARQL           ├── shacl_validator/ pyshacl
  ├── SHACL-via-SPARQL shapes               ├── n3_reasoner/  EYE + N3 rules
  └── HRA/CCF/UBERON namespaces             └── local_llm/    Ollama PDF parsing
```

---

## Feature Reference

### Vault Core

#### Pairing & Access Profiles (M1)
- QR-code WebRTC session pairing — phone scans desktop QR to initiate
- Gun.eco signalling with automatic cleanup after Noise_XX handshake completes
- **9 SHACL access profiles** (Emergency Responder, Emergency Department, GP/Specialist, Mental Health, Social Worker, Researcher, Legal Advocate, Carer/Family, Personal/Partner) with ODRL EdgeConstraints governing what each receiver may see
- Owner workspace with drag-and-drop health panels, notes, mental health assessments, social context
- Emergency pre-auth: owner can pre-approve profiles before an incident

#### Identity Credentials & Encrypted Channel (M2)
- Ed25519 `did:key` generated per session via WebCrypto — both vault and connector get their own ephemeral key
- Vault signs every outbound response; desktop verifies the signature before rendering any data
- X25519 static keys for **Noise_XX_25519_AESGCM_SHA256** protocol handshake
- All DataChannel traffic AES-256-GCM encrypted post-handshake
- Session keys are non-extractable `CryptoKey` objects, nulled on teardown
- `FinalizationRegistry` confirms key garbage collection after every session

#### Session Lifecycle & Emergency Mode (M3)
- Session TTL (30 min default, configurable) — vault overwrites Gun session node on expiry
- `beforeunload` / `pagehide` (BFCache eviction) / `visibilitychange` (2-min grace) teardown on connector
- Legal Advocate section picker — all health sections unchecked by default
- Full ISO timestamp + accessor `did:key` logged to audit trail for every session

#### Nym Mixnet Integration (M4 — scaffolded, activation pending)
- COOP/COEP headers injected by Service Worker enabling SharedArrayBuffer for Nym SDK
- `nymAdapter.send()` routes vault outbound via Nym instead of Gun relay; fragments payloads > 28 KB (Sphinx packet limit)
- Fragment reassembly buffer keyed on `(msg_id, fragment_idx)` with 30-second expiry
- SURB pool: 20 budget, 3 attached per message, replenished when < 5 remaining
- **Dead Man's Switch**: configurable check-in interval, two trustee Nym addresses; fires silent alert to trustees on missed check-in
- **Anonymous notification**: compose and send via Nym with no WebRTC and no sender identity
- *Activation: run `docs/nym-test.html` against Nym Sandbox testnet, then set `NYM_SDK_URL` in `docs/js/vault-nym.js`*

#### Sanctuary Mode & Duress (M5)
- `deriveVaultKey(pin, salt)` — PBKDF2-SHA256, 310,000 iterations; three independent keys (sanctuary, duress, main-vault)
- Sanctuary IndexedDB namespace (`wf-vault`, stores `wf-s` + `wf-sc`) — obfuscated store names, all entries AES-256-GCM encrypted
- **Duress decoy vault**: duress PIN opens an identical owner workspace, fires a silent Nym alert, suppresses Sanctuary panel entirely
- Sanctuary workspace: dark-theme UI, **Unvarnished Log** (Veiled Assertions + Hypothesis Nodes), **Contingency Protocols** (duress contacts encrypted under duress key)
- DLT commitment anchor: `commitment = sha256(sha256(entry) ‖ nonce)` computed before every IDB write

#### Hardening & Evidentiary Export (M6 — code-complete)
- Gun write audit and connector storage audit — verified clean; no health data touches relay nodes
- PWA manifest + Wake Lock API
- Relay-unreachable timeout (12 seconds) with user-facing error
- Browser compatibility guard: startup checks Ed25519 + X25519 WebCrypto
- **Tripwire Dashboard** — log Active Opaque Collisions; mark as exported, noted, or resolved
- **Synthesis Engine** — Contradiction Audits, Incoherence Reports, configurable Sentinel Ruleset
- **Evidentiary Export** — signed Verifiable Presentation (JSON-LD, Ed25519, W3C VC Data Model)
- **Bitcoin anchoring via OpenTimestamps** — feeless, anonymous; each hash is one Merkle-tree leaf; `pending → confirmed` state tracked per entry; `.ots` proof files downloadable

---

### Medication Management

| Module | File | What it does |
|---|---|---|
| Reminders | `vault-meds-reminders.js` | Today's schedule, take/skip logging, overdue alerts |
| Drug interactions | `vault-meds-lod.js` | SUBSTANCE_INTERACTIONS engine, RxNorm/Wikidata LOD lookup, interaction severity badges |
| Medication manager | `vault-meds-manager.js` | Add / cease medications; dose, route, frequency, schedule times |
| Diet log | `vault-diet.js` + `vault-diet-barcode.js` | Daily food entry log, macro totals, barcode scanner |

---

### Diet Log (Sprint 6)

IDB store: `wf-dl`. Fields aligned with Open Food Facts / USDA FoodData Central:

| Field | Type | Notes |
|---|---|---|
| `name` | string | Required |
| `meal` | enum | breakfast / lunch / dinner / snack / drink |
| `date` | YYYY-MM-DD | |
| `time` | HH:MM | |
| `quantity` | number | |
| `unit` | enum | g / ml / serving / piece / cup / tbsp / tsp / oz |
| `kcal` | number | |
| `protein_g`, `carbs_g`, `fat_g` | number | |
| `fiber_g`, `sugar_g`, `sodium_mg` | number? | Optional |
| `brand`, `notes` | string | Optional |

---

### Verifiable Communications Ecosystem (VC-7 through VC-15)

#### VC-7 — Verified Directory
- Semantic contact graph (FOAF-inspired) in encrypted IDB (`wf-contacts`, `wf-relationships`, `wf-agreements`)
- AES-256-GCM at rest under vault key
- `lookupByDid(did)` for instant caller identification in VC-9

#### VC-8 — Semantic Handshake
- ODRL `Agreement` JSON-LD specifying permitted health data sections
- Both parties sign with Ed25519 `did:key`; `did:peer` created per relationship
- Signed agreement stored in `wf-agreements`

#### VC-9 — Inbound Caller Gating
- Dual transport: Nym + Gun simultaneously
- Known contacts ring immediately; unknown held at verification screen; invalid signatures silently rejected

#### VC-10 — Hypermedia Voice/Video
- **Topology A**: vault ↔ vault (both on `vault.html` + `connector/index.html`)
- **Topology B**: vault generates call link → guest opens `join.html?id=<session>` — no vault needed
- `vault-cv.js`: OpenCV stub for future emotion recognition + rPPG pulse (all client-side)

#### VC-11 — Web Connector (Live Data Sharing)
- In-call section approval panel; each section independently approved or denied
- Signed VP receipt generated per share; stored in IDB; available to VC-15

#### VC-12 — Background Job Scheduler
- Trigger conditions: `ALWAYS`, `IDLE`, `CHARGING`, `DESKTOP` (connector live), `MANUAL`
- Up to 3 retries with backoff; desktop offload over DataChannel when `DESKTOP` condition met
- IDB store: `wf-jobs`

#### VC-13 — Event Log & Transcript Engine
- SHA-256 Merkle hash chain on `wf-events`
- `generateTranscript(sessionId)` → HTML+RDFa (`wf:CommunicationTranscript`)
- Ed25519-signed revision delta chain; independently verifiable

#### VC-14 — Language Transcoding
- Tier 1: WebSpeech API (live, zero network)
- Tier 2: `transformers.js` local LLM (offline, higher accuracy)
- Tier 3: user-configured external API (explicit per-session consent required each time)
- `wf:LanguageService` provenance node written into transcript RDFa per segment

#### VC-15 — Content Package
- SHA-256 hashes all artefacts; JSON-LD `wf:ContentPackage` manifest with ODRL policy reference
- Pure-JS ZIP builder (PKWARE APPNOTE 6.3, no dependencies)
- OTS anchor job enqueued automatically on package build

---

### Human-Centric Wallet (HCW)

#### HCW-1 — Lightning Wallet (complete)
- IDB stores: `wf-wallet` (provider metadata), `wf-txlog` (local transaction log, never transmitted)
- Architecture: transaction-to-location linkage prevented by design

#### HCW-2 — Nym Bandwidth Abstraction (complete)
- `setModuleConsent()` session guard on all Nym operations
- Bandwidth metering layer between vault features and Nym adapter

#### HCW-3 through HCW-10 — not yet started
See `instructions/COMMS_EPIC_PLAN.md` for the full plan.

---

### WASM Bridge (wellfare-core ↔ vault.html)

`docs/js/vault-wasm.js` — lazy-loads `docs/pkg/wellfare_core.js` (built by CI from Rust source).
Vault remains fully functional without the WASM pkg; bridge degrades gracefully.

| Function | Description |
|---|---|
| `parseHealthCSV(type, csv)` | Parse Samsung Health CSV → JS records |
| `csvToTurtle(type, csv)` | Samsung Health CSV → Turtle RDF string |
| `importCSVToVault(type, csv)` | Parse + store into `wf-biometrics` IDB |
| `exportVaultToTurtle()` | All meds + diet + biometrics → single Turtle doc |
| `sparqlQuery(turtle, sparql)` | SPARQL SELECT/ASK/CONSTRUCT via oxigraph |
| `sparqlOverVault(sparql)` | Export vault → run SPARQL over it |
| `validateHealthTurtle(turtle)` | SHACL shape validation |
| `validateVault()` | Export vault → validate |

Rust additions in this release:
- `wf:` prefix (`https://wellfare.social/ns/vault#`) added to all RDF output
- `vault_meds_to_turtle`, `vault_diet_to_turtle`, `vault_biometrics_to_turtle` wasm-bindgen exports

To build locally:
```bash
cd wellfare-core && wasm-pack build --release --target web --out-dir ../docs/pkg
```

---

### Webizen Agent (WA-1 through WA-7 — complete)

| Milestone | What |
|---|---|
| WA-1 | AgentController, IDB v7, `wf-telemetry` store, worker path convention |
| WA-2 | cv-emotion worker (MediaPipe, classic worker + dynamic import) |
| WA-3–5 | rPPG pulse worker, audio prosody, linguistic pattern analysis |
| WA-6 | Connector Live Indicators panel |
| WA-7 | Transcript `BiometricTelemetryLog`, package `telemetry.ndjson` |

---

## IndexedDB Schema (v9)

| Store | Key | Contents |
|---|---|---|
| `wf-s` | `id` | Sanctuary entry log (AES-GCM encrypted, obfuscated name) |
| `wf-sc` | `id` | Sanctuary config / canaries |
| `wf-meds` | `id` | Medication records |
| `wf-ml` | `id` | Medication adherence log |
| `wf-pc` | `id` | Pharmacological LOD cache (7-day TTL) |
| `wf-dl` | `id` | Diet log entries |
| `wf-contacts` | `id` | Verified Directory — contact records (AES-GCM encrypted) |
| `wf-relationships` | `id` | Relationship edges + did:peer per pairing |
| `wf-agreements` | `id` | Signed ODRL usage agreements |
| `wf-jobs` | `id` | Background job queue |
| `wf-events` | `id` | Call event log with SHA-256 hash chain |
| `wf-telemetry` | `id` | Session biometric telemetry samples (WA-1) |
| `wf-wallet` | `id` | Wallet provider metadata (HCW-1) |
| `wf-txlog` | `id` | Local transaction log — never transmitted (HCW-1) |
| `wf-biometrics` | `id` | Samsung Health CSV import records, indexed by type + date (v9) |

---

## Technical Capabilities

| Capability | Implementation | Status |
|---|---|---|
| **Identity & Encryption** | | |
| QR WebRTC pairing | Gun.eco signalling + WebRTC DataChannel | ✅ |
| Identity credentials | Ed25519 did:key + did:peer via WebCrypto | ✅ |
| Encrypted channel | Noise_XX_25519_AESGCM_SHA256 | ✅ |
| SHACL access profiles + ODRL EdgeConstraints | 9 profiles (TTL + JSON) | ✅ |
| Session lifecycle & teardown | TTL, BFCache, FinalizationRegistry | ✅ |
| Browser compatibility guard | Ed25519 + X25519 feature detection | ✅ |
| **Data & Privacy** | | |
| Medication tracker | Take/skip logging, overdue alerts, drug interactions | ✅ |
| Diet log | Daily food entries, macro totals, barcode scanner | ✅ |
| Biometrics import | Samsung Health CSV via WASM, wf-biometrics IDB | ✅ |
| Sanctuary Mode (encrypted IDB) | PBKDF2-SHA256 310k iter, AES-256-GCM | ✅ |
| Duress decoy vault | Silent Nym alert + suppressed sanctuary panel | ✅ |
| Tripwire Dashboard | Active Opaque Collisions + Resolution Engine | ✅ |
| Synthesis Engine | Contradiction Audits + Sentinel Ruleset | ✅ |
| Verifiable Presentation export | JSON-LD, Ed25519, W3C VC Data Model | ✅ |
| Bitcoin commitment anchoring | OpenTimestamps (feeless, anonymous) | ✅ |
| PWA install + Wake Lock | manifest.webmanifest + Screen Wake Lock API | ✅ |
| **Communications** | | |
| Verified Directory | Encrypted contact graph, SHACL shapes | ✅ |
| Semantic Handshake | ODRL agreement, Ed25519 bilateral signing, did:peer | ✅ |
| Inbound Caller Gating | Dual Nym+Gun transport; unknown callers blocked | ✅ |
| Voice/Video calls | WebRTC media; vault↔vault + guest link | ✅ |
| Call profiles | 8 per-contact presets wired into directory + overlay | ✅ |
| Model preferences | Whisper model selector, CV module defaults | ✅ |
| Live data sharing | In-call DataChannel share + VP receipts | ✅ |
| Background Job Scheduler | Condition-triggered queue; desktop offload | ✅ |
| Event Log & Transcript | HTML+RDFa, SHA-256 Merkle chain, revision signing | ✅ |
| Language Transcoding | 3-tier: WebSpeech → local LLM → external (consent-gated) | ✅ |
| Content Package | JSON-LD manifest, ZIP builder, OTS anchor | ✅ |
| Nym Mixnet routing | Dead Man's Switch + anonymous notify | ✅ (activation pending) |
| **Webizen Agent** | | |
| AgentController + telemetry IDB | Worker orchestration, wf-telemetry | ✅ |
| CV emotion worker | MediaPipe face mesh (classic worker) | ✅ |
| rPPG pulse worker | Forehead ROI colour signal | ✅ |
| Audio prosody worker | Pitch/energy pattern analysis | ✅ |
| Linguistic pattern worker | Keyword + sentiment analysis | ✅ |
| Connector Live Indicators | Real-time telemetry panel in desktop connector | ✅ |
| Transcript telemetry log | BiometricTelemetryLog + package telemetry.ndjson | ✅ |
| **Human-Centric Wallet** | | |
| Lightning wallet (HCW-1) | wf-wallet + wf-txlog IDB, anonymous by design | ✅ |
| Nym bandwidth abstraction (HCW-2) | setModuleConsent, bandwidth metering | ✅ |
| Exchange on-ramp (HCW-3+) | | 🔲 planned |
| **WASM Bridge** | | |
| Samsung Health CSV → IDB | WASM parsers, wf-biometrics store | ✅ |
| Vault data → Turtle RDF | vault_meds/diet/biometrics_to_turtle | ✅ |
| SPARQL over vault data | oxigraph WasmHealthStore | ✅ |
| SHACL validation | Shape constraints via SPARQL ASK | ✅ |
| **Semantic Health Core (legacy)** | | |
| Samsung Health CSV ingestion | Rust WASM | ✅ |
| RDF/Turtle generation | Rust WASM (PROV-O, FHIR, SNOMED, QUDT) | ✅ |
| In-browser SPARQL | oxigraph via WASM | ✅ |
| SHACL validation | SPARQL shapes in WASM | ✅ |
| HuBMAP HRA semantic linking | Python SPARQL client + UBERON | ✅ |
| Mental health assessments | DASS-21, K10, PHQ-9 | ✅ |

---

## Project Layout

```
docs/
  vault.html              Daily-use vault — PIN → meds, contacts, calls, queue, diet, sanctuary
  webconnect.html         WebRTC pairing bridge — QR scan → profile selection → serving
  join.html               Lightweight call join page — guest or vault-user (Topology B)
  pair.html               Legacy monolithic vault — fully functional fallback
  connector/
    index.html            Desktop terminal — Noise initiator, Ed25519 verify, Calls panel
  nym-test.html           Nym SDK validation harness
  manifest.webmanifest    PWA manifest
  sw.js                   Service Worker — COOP/COEP headers for Nym SharedArrayBuffer
  pkg/                    WASM output (built by CI — not committed)
  profiles/
    access-profiles.ttl   SHACL access profile shapes + Contact/Relationship shapes
    profiles.json         JS-loadable profile registry
  js/
    vault-idb.js               IDB helpers + store constants (v9)
    vault-crypto.js            Key derivation, AES-GCM, commitments
    vault-did.js               did:key (Ed25519) generation
    vault-nym.js               Nym adapter, DMS, anonymous notification
    vault-mock.js              Mock vault data + SECTION_LABELS (demo mode)
    vault-wasm.js              WASM bridge — wellfare-core ↔ vault (NEW)
    vault-directory.js         VC-7 Verified Directory
    vault-handshake.js         VC-8 Semantic Handshake
    vault-comms-gate.js        VC-9 Inbound caller gating
    vault-comms-call.js        VC-10 Call session, WebRTC media
    vault-cv.js                VC-10 / WA-1 AgentController + CV workers
    vault-call-profiles.js     8 per-contact call profiles
    vault-model-prefs.js       Whisper model + CV module defaults
    vault-scheduler.js         VC-12 Background job queue
    vault-transcript.js        VC-13 Event log → HTML+RDFa transcript
    vault-comms-transcode.js   VC-14 Language transcoding, 3-tier
    vault-package.js           VC-15 Content package + ZIP builder
    vault-sanctuary-pins.js    PIN state machine, duress check, wake lock
    vault-sanctuary-log.js     Unvarnished Log, Tripwire Dashboard, Synthesis Engine
    vault-sanctuary-evidence.js  Evidentiary Export, VP generation, OpenTimestamps
    vault-meds-reminders.js    MedNotifier, today schedule, take/skip
    vault-meds-lod.js          Drug interaction engine, RxNorm/Wikidata
    vault-meds-manager.js      Add/cease medication sheet
    vault-diet.js              Diet log — daily food entries, macros
    vault-diet-barcode.js      Barcode scanner, Open Food Facts lookup
    vault-wallet.js            HCW-1 Lightning wallet UI
    noise-xx.js                Noise_XX_25519_AESGCM_SHA256 (webconnect only)
    profiles.js                Profile loading, emergency pre-auth (webconnect only)

wellfare-core/              Rust library (CSV → RDF, oxigraph, SHACL, WASM bindings)
  src/
    wasm.rs                 wasm-bindgen exports (including vault_meds/diet/biometrics_to_turtle)
    rdf.rs                  Turtle serialisers — all output uses wf: + health: prefixes
    store.rs                oxigraph HealthStore + SPARQL
    shapes.rs               SHACL-via-SPARQL constraints
    parser.rs               Samsung Health CSV parsers
    models.rs               WeightRecord, SleepRecord, HeartRateRecord, StepRecord

instructions/
  COMMS_EPIC_PLAN.md              VC-7 to VC-15 + HCW implementation plan
  VAULT_CONNECTOR_NEXT_STEPS.md   v0.0.5 milestone checklist
  sanctuaryMode.md                Sanctuary Mode full specification
  BROWSER_COMPAT.md               Storage audit + real-device test matrix

ui/                         Streamlit entry point (legacy semantic core)
wellfare-core/              Rust WASM library
extensions/                 Python extensions (shacl, n3, llm)
src/                        Python RDF pipeline + FHIR models
data/demo/                  Synthetic personas
```

---

## Remaining Tasks (v0.0.6)

### Runtime / device — no code required

| Task | Notes |
|---|---|
| **Nym Sandbox validation** | Run `docs/nym-test.html` against `https://sandbox-nym-api1.nymtech.net/api`; set `NYM_SDK_URL` in `docs/js/vault-nym.js` |
| **Real-device testing** | iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md` |
| **SURB stress test** | Airplane-mode toggle while Nym active; verify fragment expiry + replenishment |

### Deferred architecture

| Item | Notes |
|---|---|
| `webconnect.html` ↔ `vault.html` message relay | `initiate_call` / `call_control` from connector cannot reach vault.html without a BroadcastChannel bridge — scoped out for MVP |
| Wallet send/receive | HCW-3+ — UI frame present, backend not yet wired |
| Job offload persistence | `_callDc` offload only works during active vault↔vault calls |

---

## Related External Resources

| Resource | Relevance |
|---|---|
| WebCivics/ontologies (`2023` branch) — `ttl/un/udhr.ttl`, `ttl/w3c/odrl.ttl` | Rights instruments in ODRL agreements |
| mediaprophet/Episteme — `custom-addons/rights-ontology.ttl` | Defines `webizen:EdgeConstraint` used in access profiles |
| Nym SDK `@nymproject/sdk-full-fat` | Mixnet routing; requires SharedArrayBuffer, cold start 3–8s |
| OpenTimestamps public calendars (alice, bob, finney) | Feeless Bitcoin anchoring for commitment hashes |

---

## Dev Server

```bash
python -m http.server 3000 --directory docs
```

Always test using a real Chrome instance — WebCrypto (Ed25519/X25519), IndexedDB, and Service Worker registration are not available in sandboxed preview environments.

**Demo PIN: `1234`** · Demo mode (no PIN): `vault.html?demo`

# Episteme:WellFair

**Current Version: 0.0.6-dev** (31 May 2026)

> **WellFair: Welfare, wellness & Fairness, Fair Terms.**
> WellFair is a human-centric **P3-SWA** — a Personal Platform Provider App for the Social Web: peace infrastructure for the natural person, running entirely on your own hardware, connected to the world on your terms.

---

## What is WellFair?

**Episteme:WellFair** is a human-centric personal wellbeing vault — and an instance of a new category of software called a **P3-SWA**.

### The untransferable code

Around the year 2000, the internet hardened into an extraction model — one that treats human beings as data points to be harvested. The architectural response to this is what we call **the untransferable code**: genuine human agency, rooted in lived experience and the inalienable dignity of the natural person, cannot be extracted, commodified, or stolen. Any system that tries produces something hollow — it can verify a record, but it lacks the capacity to map the common sense needed to protect genuine human agency.

See: [*The Untransferable Code*](https://www.youtube.com/watch?v=HJJs-Ve-Dhg) — the philosophical foundation of this work.

WellFair is designed as **peace infrastructure**: an inalienable extension of the self, engineered to protect individuals from administrative violence by ensuring that the computational vault and the natural person it serves remain inseparable.

This principle flows through every layer of the design:

- **Maslow over metrics** — a sleep score or heart rate is understood in the context of safety, shelter, belonging, and psychological wellbeing; data points without lived context are hollow
- **Shapes, not classes** — people are described using SHACL/RDFS shapes rather than OWL class membership; reducing a natural person to an ontological class strips the nuance and dignity of lived experience
- **Consent is modelled, not assumed** — Proxy Consent and Sanctuary Mode treat the natural person's right to control their own information as a first-class architectural requirement, not an afterthought
- **The tool serves the person** — WellFair exists to extend your capacity to act; it has no interest in your data itself

### The P3 concept

| Term | Meaning |
|---|---|
| **P3** | *Personal Platform Provider* — a person who acts as their own digital platform, rather than relying on a corporation to hold and mediate their data |
| **P3A** | *Personal Platform Provider App* — software that gives a person the infrastructure to be their own P3: local storage, local compute, local reasoning |
| **P3-SWA** | *Personal Platform Provider — Social Web App* — a P3A that also participates in the Social Web (Solid, ActivityPub/Fediverse, WebID), so the vault can federate and share selectively without becoming a silo |

The dominant model of digital health makes corporations the platform provider: they ingest your data, control how you see it, and monetise it. WellFair inverts that. **You are the platform.** Your phone or computer is the server. Your data is yours — and when you choose to share it (with a doctor, a carer, a researcher), you do so on your own terms through open, decentralised protocols.

Developed independently by Timothy Charles Holborn, WellFair maps physiological data against **Maslow's Hierarchy of Needs**, ensuring that a sleep reading or heart rate is understood in the full context of a human life — safety, shelter, relationships, and psychological wellbeing — not just as a number.

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

## Quick Start

### Vault (phone + desktop pairing)

```bash
python -m http.server 3000 --directory docs
```

| Page | URL | Purpose |
|---|---|---|
| **Daily vault** | `http://localhost:3000/vault.html` | Phone — PIN → full owner workspace |
| **Demo mode** | `http://localhost:3000/vault.html?demo` | No PIN — loads sample data instantly |
| **Desktop connector** | `http://localhost:3000/connector/` | Desktop terminal — stateless |
| **Pairing bridge** | `http://localhost:3000/webconnect.html` | Phone — QR scan → profile selection → serving |
| **Call join** | `http://localhost:3000/join.html?id=<session>` | Guest call link (no vault required) |
| **Nym test harness** | `http://localhost:3000/nym-test.html` | Validate Nym SDK before activation |
| **Legacy vault** | `http://localhost:3000/pair.html` | Original monolithic page — still functional |

Requires **Chrome 111+**, **Edge 111+**, or **Firefox 130+** (Ed25519 + X25519 WebCrypto).

### Semantic Health Core (legacy)

```bash
# Windows
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui/app.py

# macOS / Linux
chmod +x run.sh && ./run.sh
```

Select a demo profile (e.g. **gemini**, **elena**, **margaret**) from the sidebar.

---

## Feature Reference

### Vault Core

#### Pairing & Access Profiles (M1)
- QR-code WebRTC session pairing — phone scans desktop QR to initiate
- Gun.eco signalling with automatic cleanup after Noise_XX handshake completes
- **9 SHACL access profiles** (Emergency Responder, Emergency Department, GP/Specialist, Mental Health, Social Worker, Researcher, Legal Advocate, Carer/Family, Personal/Partner) with ODRL EdgeConstraints governing what each receiver may see
- Owner workspace with drag-and-drop health panels, notes, mental health assessments, social context
- Emergency pre-auth: owner can pre-approve profiles before an incident (e.g. if expecting surgery)

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
- **Dead Man's Switch**: configurable check-in interval, two trustee Nym addresses; fires silent alert to trustees on missed check-in; test-fire available
- **Anonymous notification**: compose and send via Nym with no WebRTC and no sender identity
- *One activation step remaining: run `docs/nym-test.html` against Nym Sandbox testnet, then set `NYM_SDK_URL` in `docs/js/vault-nym.js`*

#### Sanctuary Mode & Duress (M5)
- `deriveVaultKey(pin, salt)` — PBKDF2-SHA256, 310,000 iterations; three independent keys (sanctuary, duress, main-vault)
- Sanctuary IndexedDB namespace (`wf-vault`, stores `wf-s` + `wf-sc`) — obfuscated store names, all entries AES-256-GCM encrypted
- **Duress decoy vault**: duress PIN at the owner PIN screen opens an identical owner workspace, fires a silent Nym alert to configured contacts, and suppresses the Sanctuary panel entirely
- Sanctuary workspace: dark-theme UI, **Unvarnished Log** (Veiled Assertions + Hypothesis Nodes), **Contingency Protocols** panel (duress contacts encrypted under duress key)
- DLT commitment anchor: `commitment = sha256(sha256(entry) ‖ nonce)` computed before every IDB write — entry content never leaves the device

#### Hardening & Evidentiary Export (M6 — code-complete)
- Gun write audit and connector storage audit — both verified clean; no health data touches relay nodes
- PWA manifest + Wake Lock API (screen stays on during active sessions)
- Relay-unreachable timeout (12 seconds) with user-facing error message
- Browser compatibility guard: startup checks Ed25519 + X25519 WebCrypto; unsupported browsers receive a clear error
- **Tripwire Dashboard** — log Active Opaque Collisions; mark as exported, noted, or resolved
- **Synthesis Engine** — Contradiction Audits, Incoherence Reports, configurable Sentinel Ruleset
- **Evidentiary Export** — select sanctuary entries, generate a cryptographically signed Verifiable Presentation (JSON-LD, Ed25519, W3C VC Data Model); download commitment manifest
- **Bitcoin anchoring via OpenTimestamps** — publish commitment hashes anonymously to Bitcoin via public calendar servers (alice, bob, finney); each hash is one anonymous Merkle-tree leaf with no on-chain identity; async `pending → confirmed` state tracked per entry in IDB; `.ots` proof files downloadable for offline verification

---

### Medication Management

The vault tracks medications across five modules with full IDB persistence:

| Module | File | What it does |
|---|---|---|
| Reminders | `vault-meds-reminders.js` | Today's schedule, take/skip logging, overdue alerts |
| Drug interactions | `vault-meds-lod.js` | SUBSTANCE_INTERACTIONS engine, RxNorm/Wikidata LOD lookup, interaction severity badges |
| Medication manager | `vault-meds-manager.js` | Add / cease medications; dose, route, frequency, schedule times |
| Diet log | `vault-diet.js` | Daily food entry log (Sprint 6 — see below) |

**Medication data is never sent to any server.** All lookups against external LOD sources are read-only and anonymised; no health context is transmitted.

---

### Diet Log (Sprint 6 — new in v0.0.6)

A full daily food entry log built on the `wf-dl` IDB store, accessible from the **🍽 Diet** button in the owner workspace.

**Data model** (aligned with Open Food Facts / USDA FoodData Central field names):

| Field | Type | Notes |
|---|---|---|
| `name` | string | Food name (required) |
| `meal` | enum | `breakfast` / `lunch` / `dinner` / `snack` / `drink` |
| `date` | `YYYY-MM-DD` | Date of consumption |
| `time` | `HH:MM` | Time of consumption |
| `quantity` | number | Amount consumed |
| `unit` | enum | `g` / `ml` / `serving` / `piece` / `cup` / `tbsp` / `tsp` / `oz` |
| `kcal` | number | Energy in kcal |
| `protein_g` | number | Protein in grams |
| `carbs_g` | number | Carbohydrates in grams |
| `fat_g` | number | Fat in grams |
| `fiber_g` | number? | Dietary fibre (optional) |
| `sugar_g` | number? | Sugar (optional) |
| `sodium_mg` | number? | Sodium in mg (optional) |
| `brand` | string | Brand / product name (optional) |
| `notes` | string | Free-text notes (optional) |

**UI features:**
- Date navigation (‹ Today ›) to browse any past day
- Daily totals bar: kcal · protein · carbs · fat
- Entries grouped by meal section (Breakfast / Lunch / Dinner / Snack / Drink)
- Per-entry macro breakdown and calorie display
- One-tap delete
- Optional fields panel (brand, fibre, sugar, sodium, notes) collapsed by default

---

### Verifiable Communications Ecosystem (VC-7 through VC-15 — code-complete in v0.0.6)

v0.0.6 replaces the native phone address book, dialler, and messaging apps with a locally-hosted, privacy-first communications layer. All calls, data sharing, and transcripts are cryptographically verifiable. Institutions must prove who they are before they can ring.

#### VC-7 — Verified Directory
- Semantic contact graph (FOAF-inspired) stored in encrypted IDB (`wf-contacts`, `wf-relationships`, `wf-agreements`)
- AES-256-GCM encryption at rest under vault key — same key derivation as medication records
- `lookupByDid(did)` enables caller gating (VC-9) to identify known contacts instantly
- Search by name or identity credential; contact detail sheet with relationship type and agreement status
- "Initiate handshake" button per contact links to VC-8 flow

#### VC-8 — Semantic Handshake
- Generates an ODRL `Agreement` JSON-LD document specifying exactly what health data sections may be shared
- Initiator encodes the agreement as a QR payload or sends via Nym if the contact has a Nym address
- Both parties sign with their Ed25519 `did:key`; signatures are verifiable by any standard WebCrypto implementation
- Signed agreement stored in `wf-agreements`; a `did:peer` is created for the relationship

#### VC-9 — Inbound Caller Gating
- Listens simultaneously on **Nym** and **Gun** for `call_request` messages
- Known contacts (matched via `lookupByDid`) ring immediately with name + relationship label
- Unknown callers are held at a verification screen
- Callers with invalid Ed25519 signatures are silently rejected — no ring, no alert

#### VC-10 — Hypermedia Voice/Video
- **Topology A**: vault-owner ↔ vault-owner — both use `vault.html` (phone) + `connector/index.html` (desktop)
- **Topology B**: vault-owner generates a call link → guest opens `join.html?id=<session>` — no vault installation required
- `join.html`: guest entry → ephemeral `did:key` generated → joins call P2P; `?vault=1` param prompts vault pairing before join
- Connector "Calls" panel: initiate calls to directory contacts, video tiles, mute/hold/end, call link share
- `vault-cv.js` stub: placeholder for future OpenCV emotional recognition + pulse estimation (all client-side, no frames leave device)

#### VC-11 — Web Connector (Live Data Sharing)
- Slide-up panel during active calls: requester specifies which health sections to access
- Vault owner approves or denies each section independently
- Approved sections served over the encrypted DataChannel with Ed25519 signature
- Signed Verifiable Presentation receipt generated for every approved share; stored in IDB and available to VC-15 package builder

#### VC-12 — Background Job Scheduler
- Condition-triggered job queue stored in `wf-jobs` IDB store
- Trigger conditions: `ALWAYS`, `IDLE` (visibilityState hidden), `CHARGING` (battery API / night-hours fallback), `DESKTOP` (connector DataChannel live), `MANUAL`
- Up to 3 retries with backoff; failed jobs marked `failed` in queue
- Desktop offload: heavy jobs sent over DataChannel to the paired desktop for processing when `DESKTOP` condition is met
- Queue panel in vault.html: status tabs (All / Pending / Running / Done / Failed), per-job "Run now" override, scheduler settings toggles

#### VC-13 — Event Log & Transcript Engine
- Every call event appended to `wf-events` with a SHA-256 Merkle hash chain
- Event types: `call.start/end`, `participant.join/leave`, `data.request/approve/deny/serve`, `message.text`, `speech.segment`, `call.record.start/stop`
- `generateTranscript(sessionId)` produces a full **HTML+RDFa** document (`wf:CommunicationTranscript`) with call segments, AmbiguityLog, RevisionHistory, and DataSharingLog sections
- `annotateTranscript()` adds `resource=` attributes for known medication/substance names via the LOD interaction engine
- `saveRevision()` produces an Ed25519-signed delta stored in the event chain; revision chain is independently verifiable

#### VC-14 — Language Transcoding
- **Tier 1**: WebSpeech API — live real-time transcription of the audio stream; zero latency, zero network calls
- **Tier 2**: `transformers.js` local LLM pipeline — higher accuracy translation, fully offline
- **Tier 3**: user-configured external API endpoint — blocked until explicit per-session consent is granted each time
- `wf:LanguageService` provenance node written into transcript RDFa for every transcribed segment
- Translation settings panel in the queue sheet: endpoint configuration, consent button, current tier label

#### VC-15 — Content Package & Manifest
- `buildPackage(sessionId)` collects transcript HTML, events NDJSON, and VP receipts; SHA-256 hashes all artefacts
- Generates a `wf:ContentPackage` JSON-LD manifest with ODRL policy reference and participant list
- Enqueues an `ots.submit` job to anchor the manifest hash to Bitcoin via OpenTimestamps
- Pure-JS ZIP builder (PKWARE APPNOTE 6.3, no dependencies): `downloadPackage()` triggers browser download via File System Access API with fallback to individual file downloads
- Package contents are self-contained: `transcript.html` renders RDFa in any browser; events NDJSON is independently parseable

---

### Demo & Development Utilities

- **`?demo` query param** — `vault.html?demo` skips PIN entry and loads mock data instantly; Contacts, Queue, Diet, and all panels are fully functional
- **Demo auto-connect** — `connector/index.html` shows "📱 Open vault connect page" and "📋 Copy link" buttons when the QR is displayed; clicking the link opens `webconnect.html` pre-loaded with the session ID, bypassing the QR scanner entirely
- **`vault.html?v=6` cache-bust** — all local script tags carry `?v=6` to prevent stale-cache loading during development

---

## IndexedDB Schema (v6)

| Store | Key | Contents |
|---|---|---|
| `wf-s` | `id` | Sanctuary entry log (AES-GCM encrypted, obfuscated name) |
| `wf-sc` | `id` | Sanctuary config / canaries |
| `wf-meds` | `id` | Medication records |
| `wf-ml` | `id` | Medication adherence log |
| `wf-pc` | `id` | Pharmacological LOD cache (7-day TTL) |
| `wf-dl` | `id` | Diet log entries (Sprint 6) |
| `wf-contacts` | `id` | Verified Directory — contact records (AES-GCM encrypted) |
| `wf-relationships` | `id` | Relationship edges + did:peer per pairing |
| `wf-agreements` | `id` | Signed ODRL usage agreements |
| `wf-jobs` | `id` | Background job queue |
| `wf-events` | `id` | Call event log with SHA-256 hash chain |

---

## Technical Capabilities

| Capability | Implementation | Status |
|---|---|---|
| **Vault — Identity & Encryption** | | |
| QR WebRTC pairing | Gun.eco signalling + WebRTC DataChannel | ✅ |
| Identity credentials | Ed25519 did:key + did:peer via WebCrypto | ✅ |
| Encrypted channel | Noise_XX_25519_AESGCM_SHA256 | ✅ |
| SHACL access profiles + ODRL EdgeConstraints | 9 profiles (TTL + JSON) | ✅ |
| Session lifecycle & teardown | TTL, BFCache, FinalizationRegistry | ✅ |
| Browser compatibility guard | Ed25519 + X25519 feature detection | ✅ |
| **Vault — Data & Privacy** | | |
| Medication tracker | Take/skip logging, overdue alerts, drug interactions | ✅ |
| Drug interaction engine | RxNorm/Wikidata LOD, severity badges | ✅ |
| Diet log | Daily food entries, macro totals, meal grouping | ✅ |
| Sanctuary Mode (encrypted IDB) | PBKDF2-SHA256 310k iter, AES-256-GCM | ✅ |
| Duress decoy vault | Silent Nym alert + suppressed sanctuary panel | ✅ |
| Tripwire Dashboard | Active Opaque Collisions + Resolution Engine | ✅ |
| Synthesis Engine | Contradiction Audits + Sentinel Ruleset | ✅ |
| Verifiable Presentation export | JSON-LD, Ed25519 signed, W3C VC Data Model | ✅ |
| Bitcoin commitment anchoring | OpenTimestamps (feeless, anonymous) | ✅ |
| PWA install + Wake Lock | manifest.webmanifest + Screen Wake Lock API | ✅ |
| **Vault — Communications** | | |
| Verified Directory | Encrypted contact graph, SHACL shapes | ✅ |
| Semantic Handshake | ODRL agreement, Ed25519 bilateral signing, did:peer | ✅ |
| Inbound Caller Gating | Dual Nym+Gun transport; unknown callers blocked | ✅ |
| Voice/Video calls | WebRTC media; vault↔vault + guest link topologies | ✅ |
| Live data sharing | In-call DataChannel share panel + VP receipts | ✅ |
| Background Job Scheduler | Condition-triggered queue; desktop offload | ✅ |
| Event Log & Transcript | HTML+RDFa, SHA-256 Merkle chain, revision signing | ✅ |
| Language Transcoding | 3-tier: WebSpeech → local LLM → external (consent-gated) | ✅ |
| Content Package | JSON-LD manifest, ZIP builder, OTS anchor | ✅ |
| Nym Mixnet routing | Dead Man's Switch + anonymous notify | ✅ (activation pending) |
| **Semantic Health Core (legacy)** | | |
| Samsung Health CSV ingestion | Rust WASM | ✅ |
| RDF/Turtle generation | Rust WASM (PROV-O, FHIR, SNOMED, QUDT) | ✅ |
| In-browser SPARQL | oxigraph via WASM | ✅ |
| SHACL validation | SPARQL shapes in WASM | ✅ |
| HuBMAP HRA semantic linking | Python SPARQL client + UBERON | ✅ |
| 3D anatomy viewer | Three.js + HuBMAP GLBs | ✅ |
| Mental health assessments | DASS-21, K10, PHQ-9 | ✅ |
| Proxy consent / guardianship | Pydantic models | ✅ |
| Local LLM / PDF parsing | Ollama extension | 🔲 planned |
| In-browser N3 (swipl-wasm) | SWI-Prolog WASM | 🔲 planned |

---

## Project Layout

```text
docs/
  vault.html              Daily-use vault — PIN → meds, contacts, calls, queue, diet, sanctuary
  webconnect.html         WebRTC pairing bridge — QR scan → profile selection → serving
  join.html               Lightweight call join page — guest or vault-user (Topology B)
  pair.html               Legacy monolithic vault — fully functional fallback
  connector/
    index.html            Desktop terminal — Noise initiator, Ed25519 verify, Calls panel
  nym-test.html           Nym SDK validation harness (run before activating NYM_SDK_URL)
  manifest.webmanifest    PWA manifest
  sw.js                   Service Worker — COOP/COEP headers for Nym SharedArrayBuffer
  profiles/
    access-profiles.ttl   SHACL access profile shapes (canonical) + Contact/Relationship shapes
    profiles.json         JS-loadable profile registry
  js/
    vault-idb.js               IDB helpers + store constants (v6)
    vault-crypto.js            Key derivation, AES-GCM encrypt/decrypt, commitments
    vault-did.js               did:key (Ed25519) generation
    vault-nym.js               Nym adapter, Dead Man's Switch, anonymous notification
    vault-mock.js              Mock vault data + SECTION_LABELS (demo mode)
    vault-directory.js         VC-7 — Verified Directory contact graph, encrypted IDB
    vault-handshake.js         VC-8 — Semantic Handshake, ODRL agreement signing
    vault-comms-gate.js        VC-9 — Inbound caller gating, Nym+Gun dual transport
    vault-comms-call.js        VC-10 — Call session, WebRTC media, link generation
    vault-cv.js                VC-10 — OpenCV stub (emotional recognition, pulse — future)
    vault-scheduler.js         VC-12 — Background job queue engine
    vault-transcript.js        VC-13 — Event log → HTML+RDFa transcript
    vault-comms-transcode.js   VC-14 — Language transcoding, 3-tier progressive
    vault-package.js           VC-15 — Content package + JSON-LD manifest + ZIP builder
    vault-sanctuary-pins.js    PIN state machine, canary/setup, duress check, wake lock
    vault-sanctuary-log.js     Unvarnished Log, Tripwire Dashboard, Synthesis Engine
    vault-sanctuary-evidence.js  Evidentiary Export, VP generation, OpenTimestamps
    vault-meds-reminders.js    MedNotifier, today schedule, take/skip, reminder panel
    vault-meds-lod.js          Drug interaction engine, RxNorm/Wikidata LOD
    vault-meds-manager.js      Add/cease medication sheet
    vault-diet.js              Diet log — daily food entries, macros, meal grouping
    noise-xx.js                Noise_XX_25519_AESGCM_SHA256 (webconnect only)
    profiles.js                Profile loading, emergency pre-auth (webconnect only)

instructions/
  COMMS_EPIC_PLAN.md              VC-7 to VC-15 implementation plan + progress tracker
  VAULT_CONNECTOR_NEXT_STEPS.md   v0.0.5 milestone checklist + architecture notes
  sanctuaryMode.md                Sanctuary Mode full specification
  BROWSER_COMPAT.md               Storage audit results + real-device test matrix

shared-schemas/
  biomarker-vocabulary.ttl        Shared RDF vocabulary
  test-profiles/                  SHACL test profile data

wellfare-core/                    Rust library (CSV → RDF, oxigraph, SHACL)
ui/
  app.py                          Streamlit entry point (legacy semantic core)
  tabs/                           Per-section UI modules
extensions/
  shacl_validator/                pyshacl integration
  n3_reasoner/                    EYE N3Logic daemon
  local_llm/                      Ollama PDF parsing (planned)
src/
  hra_client.py                   HuBMAP SPARQL client
  rdf_transformer.py              Python RDF pipeline
  phr_models/                     FHIR/Maslow Pydantic models
data/demo/                        Synthetic personas (Margaret, Jordan, Elena, Michael…)
```

---

## Remaining Tasks (v0.0.6)

### Runtime / device only — no code required

| Task | Notes |
|---|---|
| **Nym Sandbox validation** | Run `docs/nym-test.html` against `https://sandbox-nym-api1.nymtech.net/api`; confirm SDK load time; set `NYM_SDK_URL` in `docs/js/vault-nym.js` |
| **Real-device testing** | iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md` |
| **SURB stress test** | Airplane-mode toggle while Nym client active; verify fragment expiry + SURB replenishment |

### Deferred architecture (documented, not blocking)

| Item | Notes |
|---|---|
| `webconnect.html` ↔ `vault.html` message relay | `initiate_call` and `call_control` messages from connector cannot currently reach vault.html without a BroadcastChannel bridge — scoped out for MVP |
| Job offload persistence | `_callDc` offload only works during active vault↔vault calls; a persistent path requires webconnect.html forwarding |

---

## Related External Resources

| Resource | URL | Relevance |
|---|---|---|
| WebCivics/ontologies (`2023` branch) | `ttl/un/udhr.ttl`, `ttl/w3c/odrl.ttl` | Rights instruments used in ODRL agreements |
| mediaprophet/Episteme | `custom-addons/rights-ontology.ttl` | Defines `webizen:EdgeConstraint` used in access profiles |
| Nym SDK | `@nymproject/sdk-full-fat` | Mixnet routing; requires SharedArrayBuffer (COOP/COEP), cold start 3–8 s |
| OpenTimestamps | Public calendar servers (alice, bob, finney) | Feeless, anonymous Bitcoin anchoring for commitment hashes |

---

## 📜 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**.

Copyright © 2025–2026 Timothy Charles Holborn.

See [`LICENSE`](LICENSE) and [`COPYRIGHT.md`](COPYRIGHT.md) for full details.

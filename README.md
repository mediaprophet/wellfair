# Episteme:WellFair

**Current Version: 0.0.5-dev** (30 May 2026)

> **WellFair: Welfare, wellness & Fairness, Fair Terms.**
> WellFair is a human-centric **P3-SWA** — a Personal Platform Provider App for the Social Web: peace infrastructure for the natural person, running entirely on your own hardware, connected to the world on your terms.

See [RELEASE_NOTES_v0.0.3.md](RELEASE_NOTES_v0.0.3.md) for the last stable release notes.

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

Human-centricity is also the foundation of the P3 model:

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
Phone (pair.html — vault)               Desktop (connector/index.html — terminal)
─────────────────────────────────       ──────────────────────────────────────────
WebCrypto Ed25519 did:key (ephemeral)   WebCrypto Ed25519 did:key (ephemeral)
X25519 static key (Noise_XX)            X25519 static key (Noise_XX)
│                                       │
└──── WebRTC DataChannel ───────────────┘
      Noise_XX_25519_AESGCM_SHA256
      AES-256-GCM per message

Gun.eco ─── WebRTC signalling only (health data never touches relay nodes)
Nym Mixnet ─ anonymous routing for non-real-time messages (DMS, notifications)
```

**Phone vault holds:**
- Health records (encrypted at rest, AES-256-GCM)
- Identity credentials (did:key per session, did:peer per pairing)
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

## What's in v0.0.4

The v0.0.4 sprint delivered the complete privacy vault stack across six milestones:

### M1 — Pairing & Access Profiles
- QR-code WebRTC session pairing (phone scans desktop QR)
- Gun.eco signalling with automatic cleanup post-handshake
- 9 SHACL access profiles (Emergency Responder, Legal Advocate, GP, Carer, Researcher, and more) with ODRL EdgeConstraints governing what each receiver may see
- Owner workspace: drag-and-drop, notes, mental health assessments, social context panel

### M2 — Identity Credentials & Encrypted Channel
- Ed25519 `did:key` generated per session via WebCrypto (both sides); vault signs every response, desktop verifies before rendering
- X25519 static keys for **Noise_XX_25519_AESGCM_SHA256** handshake
- All DataChannel traffic AES-256-GCM encrypted after handshake
- Session keys are non-extractable `CryptoKey` objects; nulled on teardown
- `FinalizationRegistry` confirms key GC after session end

### M3 — Ephemeral Sharing & Emergency Mode
- Session TTL (30 min, configurable) — vault overwrites Gun session node on expiry
- `beforeunload` / `pagehide` (BFCache) / `visibilitychange` (2-min grace) teardown on connector
- Emergency pre-auth: owner can pre-approve access profiles before an incident
- Full ISO timestamp + accessor `did:key` written to phone audit log for every session
- Legal Advocate section picker — all sections unchecked by default

### M4 — Nym Mixnet Integration (scaffolded)
- COOP/COEP headers injected by Service Worker for SharedArrayBuffer support
- `nymAdapter.send()` routes vault outbound via Nym instead of Gun relay; fragments payloads > 28 KB (Sphinx packet limit)
- Fragment reassembly buffer with 30-second expiry
- SURB pool: 20 budget, 3 attached per message, replenish when < 5
- **Dead Man's Switch**: configurable check-in interval, two trustee Nym addresses; fires silent alert to trustees on missed check-in
- **Anonymous notification**: compose and send via Nym with no WebRTC required
- *Activation step remaining: run `docs/nym-test.html` against Nym Sandbox testnet, then set `NYM_SDK_URL` in `pair.html`*

### M5 — Sanctuary Mode & Duress
- `deriveVaultKey(pin, salt)` — PBKDF2-SHA256, 310,000 iterations; three independent keys (sanctuary, duress, main-vault slot)
- Sanctuary IndexedDB namespace (`wf-vault` v2, stores `wf-s` + `wf-sc`) — obfuscated store names, all entries AES-256-GCM encrypted
- **Duress decoy**: duress PIN at the owner PIN screen opens an identical owner workspace, fires a silent Nym alert to configured contacts, and suppresses the Sanctuary panel entirely
- Sanctuary workspace: dark-theme UI, Unvarnished Log (Veiled Assertions + Hypothesis Nodes), Contingency Protocols (duress contacts encrypted under duress key)
- DLT commitment anchor computed before every IDB write: `commitment = sha256(sha256(entry) ‖ nonce)` — content never leaves the device

### M6 — Hardening & Evidentiary Export (code-complete)
- Gun write audit and connector storage audit — both clean; no health data touches relay nodes
- PWA manifest wired to `pair.html`; Wake Lock API keeps screen on during active sessions
- 12-second relay-unreachable timeout with user-facing error
- **Tripwire Dashboard** — log Active Opaque Collisions; mark as exported, noted, or resolved
- **Synthesis Engine** — Contradiction Audits, Incoherence Reports, configurable Sentinel Ruleset
- **Evidentiary Export** — select sanctuary entries, generate a cryptographically signed Verifiable Presentation (JSON-LD, Ed25519, W3C VC Data Model); download commitment manifest
- **Bitcoin anchoring via OpenTimestamps** — publish commitment hashes anonymously to Bitcoin via public calendar servers (alice, bob, finney); each hash is one anonymous Merkle-tree leaf with no on-chain identity linking entries; async confirmation tracked per entry; `.ots` proof files downloadable for offline verification by any standard OTS tool
- Browser compatibility guard: startup checks for Ed25519 and X25519 WebCrypto support; unsupported browsers (Firefox < 130) receive a clear error rather than a cryptic failure

---

## What's next in v0.0.5-dev

| Task | Notes |
|---|---|
| Nym Sandbox validation | Run `docs/nym-test.html` against `https://sandbox-nym-api1.nymtech.net/api`; confirm cold-start time; set `NYM_SDK_URL` in `pair.html` |
| Real-device testing | iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md` |
| SURB stress test | Airplane-mode toggle while Nym client active; verify replenishment and fragment expiry |
| DLT chain write (secondary) | OTS Bitcoin anchoring is live; IOTA/Ethereum options deferred |

---

## Quick Start

### Vault (phone + desktop)

```bash
python -m http.server 3000 --directory docs
```

Open two browser tabs or devices:
- **Phone vault**: `http://localhost:3000/pair.html`
- **Desktop terminal**: `http://localhost:3000/connector/`

Scan the desktop QR from the phone vault to pair. Requires Chrome 111+ or Firefox 130+ (Ed25519 + X25519 WebCrypto).

### Semantic Health Core (local desktop, legacy)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui/app.py

# macOS / Linux
chmod +x run.sh && ./run.sh
```

Select a demo profile (e.g. **gemini**, **elena**, **margaret**) from the sidebar. No data export needed to explore.

### Building the WASM Bundle

```bash
cd wellfare-core && wasm-pack build --release --target web --out-dir ../ui/static/pkg
python scripts/build_stlite.py
```

---

## Technical Capabilities

| Capability | Implementation | Status |
|---|---|---|
| **Vault** | | |
| QR WebRTC pairing | Gun.eco signalling + WebRTC DataChannel | ✅ |
| Identity credentials | Ed25519 did:key + did:peer via WebCrypto | ✅ |
| Encrypted channel | Noise_XX_25519_AESGCM_SHA256 | ✅ |
| SHACL access profiles + ODRL EdgeConstraints | 9 profiles (TTL + JSON) | ✅ |
| Session lifecycle & teardown | TTL, BFCache, FinalizationRegistry | ✅ |
| Sanctuary Mode (encrypted IDB) | PBKDF2-SHA256 310k iter, AES-256-GCM | ✅ |
| Duress decoy vault | Silent Nym alert + suppressed sanctuary panel | ✅ |
| Tripwire Dashboard | Active Opaque Collisions + Resolution Engine | ✅ |
| Synthesis Engine | Contradiction Audits + Sentinel Ruleset | ✅ |
| Verifiable Presentation export | JSON-LD, Ed25519 signed, W3C VC Data Model | ✅ |
| Bitcoin commitment anchoring | OpenTimestamps (feeless, anonymous) | ✅ |
| Nym Mixnet routing | Dead Man's Switch + anonymous notify | ✅ (activation pending) |
| PWA install + Wake Lock | manifest.webmanifest + Screen Wake Lock API | ✅ |
| Browser compatibility guard | Ed25519 + X25519 feature detection on startup | ✅ |
| **Semantic Health Core** | | |
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
  pair.html                Phone vault (Noise responder, Sanctuary Mode, OTS anchoring)
  connector/
    index.html             Desktop terminal (Noise initiator, Ed25519 verify)
  nym-test.html            Nym SDK validation harness
  manifest.webmanifest     PWA manifest
  sw.js                    Service Worker — COOP/COEP for Nym SharedArrayBuffer
  profiles/
    access-profiles.ttl    SHACL access profile shapes (canonical)
    profiles.json          JS-loadable profile registry

instructions/
  VAULT_CONNECTOR_NEXT_STEPS.md   Full milestone checklist
  BROWSER_COMPAT.md               Audit results + real-device test matrix
  sanctuaryMode.md                Sanctuary Mode specification

shared-schemas/
  biomarker-vocabulary.ttl        Shared RDF vocabulary
  test-profiles/                  SHACL test profile data

wellfare-core/                    Rust library (CSV → RDF, oxigraph, SHACL)
ui/
  app.py                          Streamlit entry point
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

## 📜 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**.

Copyright © 2025–2026 Timothy Charles Holborn.

See [`LICENSE`](LICENSE) and [`COPYRIGHT.md`](COPYRIGHT.md) for full details.

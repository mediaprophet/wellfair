# Episteme:WellFair

**Current Version: 0.0.3-dev** (29 May 2026)

> **The untransferable code is you.**
> WellFair is a human-centric **P3-SWA** — a Personal Platform Provider App for the Social Web: peace infrastructure for the natural person, running entirely on your own hardware, connected to the world on your terms.

See [RELEASE_NOTES_v0.0.2.md](RELEASE_NOTES_v0.0.2.md) for the last stable release.
See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the v0.0.3 roadmap.

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

WellFair as a human-centric P3-SWA gives you:
- **Local compute** — ingest, reason over, and query your health data entirely on-device
- **Semantic interoperability** — data stored as RDF (Turtle/Solid) so it can speak to any system that understands linked data, without lock-in
- **Selective federation** — share specific records via Solid-compatible pod structure; Proxy Consent logic controls who sees what
- **Social Web participation** — your vault is a node, not a user account on someone else's node

Developed independently by Timothy Charles Holborn, WellFair maps physiological data against **Maslow's Hierarchy of Needs**, ensuring that a sleep reading or heart rate is understood in the full context of a human life — safety, shelter, relationships, and psychological wellbeing — not just as a number.

---

## 📱 Designed for Your Phone — No Cloud Required

WellFair is built mobile-first and local-first. The entire application — including semantic reasoning, 3D anatomy, and data analysis — runs on your device.

**How it works on a phone:**

1. Visit **<https://mediaprophet.github.io/wellfair/>** in your mobile browser
2. Tap **Add to Home Screen** (Android: "Install App" banner; iOS: Share → Add to Home Screen)
3. The vault installs as a PWA — it works offline from that point forward
4. Export your Samsung Health data and load it directly — it is processed on-device and never leaves your phone

> [!IMPORTANT]
> **No data is ever transmitted to a server.** There is no account, no login, no cloud sync. The GitHub Pages URL is just a delivery mechanism — once the app is installed, it runs 100% on your hardware using WebAssembly (WASM) compiled from Rust.

**What runs locally:**
- All CSV ingestion and RDF/Turtle generation (Rust → WASM)
- SPARQL queries over your health graph (oxigraph in-browser)
- SHACL shape validation of health records
- 3D anatomy viewer with HuBMAP organ models
- Semantic reasoning via N3Logic rules (optional EYE extension)

---

## 🏗️ Architecture

WellFair has two complementary modes:

| Mode | How to run | What it does |
|---|---|---|
| **Browser / PWA** | Install from GitHub Pages | Runs the full UI + Rust WASM core offline on your device |
| **Local desktop** | `streamlit run ui/app.py` | Full pipeline including Python extensions (SHACL, N3, Ollama) |

```
Browser (WASM — runs on device)          Optional local extensions (Python)
────────────────────────────────         ──────────────────────────────────
wellfare-core (Rust → WASM)              extensions/
  ├── CSV → Turtle (RDF)                   ├── hra_client/   HuBMAP SPARQL
  ├── oxigraph RDF store + SPARQL           ├── shacl_validator/ pyshacl
  ├── SHACL-via-SPARQL shapes               ├── n3_reasoner/  EYE + N3 rules
  └── HRA/CCF/UBERON namespaces             └── local_llm/    Ollama PDF parsing
```

### Core principles
- **The natural person is the ground truth** — lived experience cannot be reduced to transferable data; the system serves the person, not the other way around
- **Peace infrastructure** — the vault is an inalienable extension of the self, not a service platform
- **You are the platform (P3)** — your device is the server; there is no upstream provider
- **WellFair is a P3A** — it exists to extend your capacity to act, not to be a platform itself
- **Social Web, not social silo (P3-SWA)** — federation via Solid/WebID on your terms, not a walled garden
- **No cloud** — your data never leaves your device unless you explicitly choose to share it
- **No OWL for people** — natural persons described with SHACL/RDFS shapes, not OWL class membership; a human is not a class instance
- **N3Logic for reasoning** — causal/clinical rules grounded in relational context, not abstract entailment
- **Extensions are opt-in** — nothing loads until you trigger it; teardown() releases memory

---

## ✨ What's New in v0.0.3-dev

### Rust/WASM Core (`wellfare-core`)
- **oxigraph RDF store** — your health data is loaded into an in-browser SPARQL-queryable triple store (no server required)
- **SHACL-via-SPARQL validation** — shapes for sleep efficiency, HR range, and trauma fields run as SPARQL ASK queries in-browser
- **HRA/CCF/UBERON namespaces** — sleep and heart rate records link to HuBMAP anatomical identifiers (UBERON organ codes)
- **PROV-O provenance** — every generated triple records its Samsung Health source

### Semantic Integration
- **HuBMAP HRA SPARQL client** (`src/hra_client.py`) — queries `lod.humanatlas.io` for cell types and biomarkers mapped to UBERON organ IDs, with local TTL cache
- **Extension framework** — pluggable architecture for SHACL validator (pyshacl), N3 reasoner (EYE binary), and local LLM (Ollama)

### Developer Tools
- Built-in test suite (Dev Tools tab) covering WASM CSV parsing, Turtle generation, SPARQL, SHACL, Python RDF pipeline, HRA client, and static assets — all runnable from the UI

---

## 🌟 Key Features

### Welfare Modeling & Maslow's Hierarchy
Health data is not just numbers. WellFair maps physiological signals (sleep, heart rate, pathology) against higher-order needs (safety, shelter, mental health). The interface models how systemic stressors — housing instability, divorce, financial exploitation — impact physical health over time.

### 🔒 Sanctuary Mode & Proxy Consent
Personal vaults contain highly sensitive information. **Sanctuary Mode** instantly locks or obscures sensitive data (abuse records, psychiatric assessments, location history) on a specific trigger (device lock or duress PIN). This protects users in situations where their device could be accessed by someone who might use their data against them.

The platform also models **Proxy Consent** — legal delegations of authority (Designated Carers, Guardians, Medical Professionals) with strict privacy-mode limits.

**Demo PIN:** `8888`

### 🧬 3D Spatial Anatomy (HuBMAP Integration)
WellFair integrates the **HuBMAP Human Reference Atlas (HRA)** 3D Reference Object Library — medically-accurate GLB organ models mapped to UBERON and FMA ontologies. Clinical data is visualized spatially on a 3D body, linking biomarkers to the anatomical location they came from.

### 👥 Synthetic Personas for High-Stakes Testing
The repository ships with synthetic profiles that simulate complex, real-world systemic issues:

| Persona | Scenario |
|---|---|
| Margaret / Robert | Elder abuse and financial exploitation |
| Jordan | NDIS (disability insurance) funding exploitation |
| Elena / Rebecca | Chronic trauma, birth trauma, PTSD |
| Michael | Housing instability and family separation |

These personas allow developers and advocates to test semantic reasoning, Sanctuary Mode triggers, and Maslow dashboards against realistic, high-stakes scenarios — not just "healthy adult" dummy data.

---

## ⚙️ Technical Capabilities

| Capability | Implementation | Status |
|---|---|---|
| Samsung Health CSV ingestion | Rust WASM | ✅ |
| RDF/Turtle generation | Rust WASM (PROV-O, FHIR, SNOMED, QUDT) | ✅ |
| In-browser SPARQL | oxigraph via WASM | ✅ |
| SHACL validation | SPARQL shapes in WASM | ✅ |
| HuBMAP HRA semantic linking | Python SPARQL client + UBERON | ✅ |
| 3D anatomy viewer | Three.js + HuBMAP GLBs | ✅ |
| SHACL validator (extended) | pyshacl extension | ✅ |
| N3Logic reasoning | EYE binary extension | ✅ |
| FHIR diagnostic reports | Python phr_models | ✅ |
| Mental health assessments | DASS-21, K10, PHQ-9 | ✅ |
| Proxy consent / guardianship | Pydantic models | ✅ |
| PWA offline install | Service Worker + Stlite | ✅ |
| Local LLM / PDF parsing | Ollama extension | 🔲 Phase 6 |
| In-browser N3 (swipl-wasm) | SWI-Prolog WASM | 🔲 Phase 5 |

---

## 🚀 Quick Start (Local Desktop)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui/app.py
```

```bash
# macOS / Linux
chmod +x run.sh
./run.sh
```

Select a demo profile (e.g. **gemini**, **elena**, **margaret**) from the sidebar. No data export needed to explore.

To use your own Samsung Health data, point the export path to a folder containing your `com.samsung.health.*.csv` files.

### Building the WASM Bundle (for local PWA testing)
```bash
cd wellfare-core && wasm-pack build --release --target web --out-dir ../ui/static/pkg
python scripts/build_stlite.py
python -m http.server 8000 --directory docs
```

---

## 📁 Project Layout

```text
├── config/
│   └── ontology_template.yaml       # RDF namespace & mapping config
├── data/demo/                       # Synthetic personas (Margaret, Jordan, etc.)
├── docs/                            # Compiled Stlite WASM PWA bundle
│   ├── pkg/                         # wellfare-core WASM (built by CI)
│   ├── models/hra/                  # HuBMAP organ GLBs
│   └── sw.js                        # PWA service worker
├── extensions/
│   ├── shacl_validator/             # pyshacl integration
│   ├── n3_reasoner/                 # EYE N3Logic daemon
│   └── local_llm/                   # Ollama PDF parsing (Phase 6)
├── scripts/
│   └── build_stlite.py             # Stlite WASM bundler
├── src/
│   ├── hra_client.py                # HuBMAP SPARQL client
│   ├── rdf_transformer.py           # Python RDF pipeline
│   └── phr_models/                  # FHIR/Maslow Pydantic models
├── ui/
│   ├── app.py                       # Streamlit entry point
│   └── tabs/                        # Per-section UI modules
│       └── dev_tools.py             # Built-in test suite
├── wellfare-core/                   # Rust library (CSV → RDF, oxigraph, SHACL)
├── LICENSE
└── COPYRIGHT.md
```

---

## 📜 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**.

Copyright © 2025–2026 Timothy Charles Holborn.

See [`LICENSE`](LICENSE) and [`COPYRIGHT.md`](COPYRIGHT.md) for full details.

# Episteme:WellFair

**Current Version: 0.0.3-dev** (29 May 2026)

> **Your data. Your device. No cloud.**
> WellFair runs entirely on your phone, tablet, or computer — no account, no server, no upload.

See [RELEASE_NOTES_v0.0.2.md](RELEASE_NOTES_v0.0.2.md) for the last stable release.
See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the v0.0.3 roadmap.

---

## What is WellFair?

**Episteme:WellFair** is a personal wellbeing vault that runs entirely on your own device. It helps you own, understand, and protect your health story — across clinical, social, legal, and lived-context dimensions — without ever sending your data to a third party.

Unlike health apps that store your data in someone else's cloud, WellFair works the same way a private journal does: it lives on your device, processes everything locally, and shares nothing unless you explicitly choose to. If you install it as a PWA on your phone, it works entirely offline.

Developed independently by Timothy Charles Holborn, WellFair maps physiological data against frameworks like **Maslow's Hierarchy of Needs**, ensuring that a sleep reading or heart rate isn't just a number — it's understood in the context of safety, shelter, relationships, and psychological wellbeing.

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
- **No cloud** — your data never leaves your device
- **No OWL for people** — health subjects described with SHACL/RDFS shapes, not OWL class membership (which can dehumanise)
- **N3Logic for reasoning** — causal/clinical rules, not OWL entailment
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

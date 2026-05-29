# Episteme:WellFair

**Episteme:WellFair** is a locally-hosted Personal Wellbeing Informatics Vault designed to help individuals own, analyze, and protect their wellbeing story across clinical, social, legal, and lived-context dimensions. 

Developed independently by Timothy Charles Holborn, WellFair transcends traditional health trackers by harmonizing Rust, Python, WebAssembly (WASM), and semantic web standards (Solid/RDF) into a human-first, local-first vault. 

It is designed to evaluate holistic health against frameworks like **Maslow's Hierarchy of Needs**, ensuring that physiological data is contextualized alongside safety, belonging, and psychological wellbeing.

---

## 🌐 Browser Demo (WASM PWA)

A lightweight browser demo running the Python core compiled to WebAssembly (via Stlite) is available at:

**<https://mediaprophet.github.io/wellfair/>**

### 📱 Progressive Web App (PWA)
WellFair is fully PWA-compliant. On Android or supported desktop browsers, simply click the **Install App** button to save the Vault natively to your device. All subsequent interactions, calculations, and 3D rendering happen offline on your local hardware.

> [!NOTE]
> *All files you upload or interact with in the browser demo are processed entirely locally on your device. Data is never transmitted to a cloud server.*

### 🤫 Sanctuary Mode
When exploring the demo profiles, you can test the **Sanctuary Vault** feature using the default PIN: `8888`.

---

## 🏗️ The WellFair Architecture

While this repository originated as `health-to-solid` (a semantic mapping tool for Samsung Health exports), it has rapidly evolved into a comprehensive platform for personal advocacy, proxy consent orchestration, and wellbeing informatics. 

### Welfare Modeling & Maslow's Hierarchy
We do not view health as merely a collection of biometric data points. WellFair maps physiological signals (sleep, heart rate, pathology) against higher-order needs (safety, shelter, mental health). The interface actively models how systemic stressors (e.g., housing instability, divorce) impact physical health over time.

### Sanctuary Mode & Proxy Consent
Personal vaults contain highly sensitive information. **Sanctuary Mode** is a core architectural concept designed to instantly lock down or obscure sensitive data (such as abuse records, psychiatric assessments, or location history) upon a specific trigger (like a system lock or duress PIN). This ensures that victims of domestic or systemic abuse can safely use the platform without fear of their data being weaponized against them.
The platform also includes robust **Proxy Consent** logic, modeling legal delegations of authority (e.g., Designated Carers, Guardians, Medical Professionals) with strict privacy mode limits.

### 🧬 Spatial Anatomy & HuBMAP Integration
WellFair integrates the **HuBMAP Human Reference Atlas (HRA) 3D Reference Object Library**. The vault uses high-fidelity, medically-accurate `GLB` models directly mapped to the **UBERON** and **FMA** (Foundational Model of Anatomy) ontologies. This allows users to visualize where clinical data intersects with their physical body, mapping metadata directly to spatial mesh nodes in a WebGL environment.

### 👥 Synthetic Personas & Systemic Issue Modeling
To ensure the platform is built for the most vulnerable, we do not just test with generic "healthy" dummy data. The repository includes a suite of **Synthetic Profiles** meticulously crafted to simulate complex systemic issues, including:
- **Margaret / Robert**: Elder abuse and financial exploitation.
- **Jordan**: NDIS (National Disability Insurance Scheme) funding exploitation.
- **Elena / Rebecca**: Chronic trauma, birth trauma, and PTSD.
- **Michael**: Housing instability and family separation.

These personas allow developers and advocates to test the vault's semantic reasoning, Sanctuary Mode triggers, and Maslow-based dashboards against real-world, high-stakes scenarios.

---

## ⚙️ Technical Capabilities

- **Samsung Health Ingestion**: Ingests folders containing CSVs and optional `jsons/`, normalizing records into a unified internal format.
- **Semantic Mapping (RDF)**: Maps health and social data to RDF using configurable ontology templates (QUDT, PROV-O, schema.org) to emit Solid-compatible pod content (`/health/{type}/{YYYY-MM}.ttl`).
- **3D Biometric Hologram**: A premium WebGL spatial projection using HuBMAP reference organs and Three.js wrappers in Pyodide.
- **Diagnostic & Case Management**: Native schemas for FHIR-compliant diagnostic reports, pathology tracking, mental health assessments (DASS-21, K10), and multi-disciplinary case files.
- **Local-First Architecture**: Built to run entirely offline or in the browser via WASM, ensuring absolute data sovereignty. Includes OTA (Over-The-Air) update architecture via Service Workers.

---

## 🚀 Quick Start (Local Desktop)

```bash
cd c:\Projects\health
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run ui/app.py
```

On Unix/macOS:

```bash
chmod +x run.sh
./run.sh
```

### Recommended Data Setup
- Use the sample export data in `data/demo/` to explore the synthetic personas.
- Point the UI to a folder that contains your own `com.samsung.health.*.csv` files if you wish to analyze your own data.

### Building the WASM Bundle
To deploy the Pyodide/Stlite PWA locally:
```bash
python scripts/build_stlite.py
python -m http.server 8000 --directory docs
```

---

## 📁 Project Layout

```text
├── config/ontology_template.yaml
├── data/demo/                      # Synthetic Personas (Margaret, Jordan, etc.)
├── docs/                           # Compiled Stlite WASM bundle & PWA assets
│   ├── models/hra/                 # HuBMAP GLB Models
│   └── sw.js                       # PWA Service Worker
├── instructions/                   # Architectural philosophy & personas
├── scripts/build_stlite.py         # WASM bundling script
├── src/
│   ├── phr_models/                 # Python Pydantic representations (FHIR/Maslow)
│   └── utils/                      # Parsing, normalization, RDF logic
├── tests/
├── ui/                             # Streamlit interface
│   ├── tabs/                       # Individual application modules
│   └── app.py                      # Main Streamlit dashboard
├── wellfare-core/                  # Rust library crate
├── LICENSE
└── COPYRIGHT.md
```

## 📜 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.

Copyright © 2025–2026 Timothy Charles Holborn.

See `LICENSE` and `COPYRIGHT.md` for full details.
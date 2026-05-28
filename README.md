# Episteme:WellFair

**Episteme:WellFair** is a locally-hosted Personal Wellbeing Informatics Vault designed to help individuals own, analyze, and protect their wellbeing story across clinical, social, legal, and lived-context dimensions. 

Developed independently by Timothy Charles Holborn, WellFair transcends traditional health trackers by harmonizing Rust, Python, and semantic web standards (Solid/RDF) into a human-first vault. 

It is designed to evaluate holistic health against frameworks like **Maslow's Hierarchy of Needs**, ensuring that physiological data is contextualized alongside safety, belonging, and psychological wellbeing.

## Browser Demo (WASM)

A lightweight browser demo running the Python core compiled to WebAssembly (via Stlite) is available at:

**<https://mediaprophet.github.io/wellfair/>**

*All files you upload or interact with in the browser demo are processed entirely locally on your device. Data is never transmitted to a cloud server.*

## The WellFair Vision

While this repository originated as `health-to-solid` (a semantic mapping tool for Samsung Health exports), it has evolved into a comprehensive platform for personal advocacy and wellbeing informatics. 

### Welfare Modeling & Maslow's Hierarchy
We do not view health as merely a collection of biometric data points. WellFair maps physiological signals (sleep, heart rate, pathology) against higher-order needs (safety, shelter, mental health). The interface actively models how systemic stressors impact physical health.

### Sanctuary Mode
Personal vaults contain highly sensitive information. **Sanctuary Mode** is a core architectural concept designed to instantly lock down or obscure sensitive data (such as abuse records, psychiatric assessments, or location history) upon a specific trigger (like a duress PIN or system lock). This ensures that victims of domestic or systemic abuse can safely use the platform without fear of their data being weaponized against them.

### Synthetic Personas & Systemic Issue Modeling
To ensure the platform is built for the most vulnerable, we do not just test with generic "healthy" dummy data. The repository includes a suite of **Synthetic Profiles** meticulously crafted to simulate complex systemic issues, including:
- Elder abuse and financial exploitation.
- NDIS (National Disability Insurance Scheme) funding exploitation.
- Chronic trauma and housing instability.

These personas allow developers and advocates to test the vault's semantic reasoning, Sanctuary Mode triggers, and Maslow-based dashboards against real-world, high-stakes scenarios.

## Technical Capabilities

- **Samsung Health Ingestion**: Ingests folders containing CSVs and optional `jsons/`, normalizing records into a unified internal format.
- **Semantic Mapping (RDF)**: Maps health and social data to RDF using configurable ontology templates (QUDT, PROV-O, schema.org) to emit Solid-compatible pod content (`/health/{type}/{YYYY-MM}.ttl`).
- **3D Biometric Hologram**: A premium WebGL spatial projection of physiological data using advanced post-processing (Bloom, FilmPass) to visualize systemic stress on the human body.
- **Local-First Architecture**: Built to run entirely offline or in the browser via WASM, ensuring absolute data sovereignty.

## Quick Start (Local Desktop)

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

## Recommended Data Setup

- Use the sample export data in `data/demo/` to explore the synthetic personas (e.g., Margaret, Jordan, Elena).
- Point the UI to a folder that contains your own `com.samsung.health.*.csv` files if you wish to analyze your own data.

## Project Layout

```text
├── config/ontology_template.yaml
├── data/demo/                      # Synthetic Personas (Margaret, Jordan, etc.)
├── instructions/                   # Architectural philosophy & personas
├── scripts/build_stlite.py         # WASM bundling script
├── src/                            # Parsing, normalization, RDF logic
├── tests/
├── ui/app.py                       # Main Streamlit dashboard
├── wellfare-core/                  # Rust library crate
├── LICENSE
└── COPYRIGHT.md
```

## Extending the Ontology

Edit `config/ontology_template.yaml` to change mappings, add new data types, or override transform behavior. Supported transform functions include:
- `unix_ms_to_iso_with_offset`
- `minutes_to_iso_duration`

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.

Copyright © 2025–2026 Timothy Charles Holborn.

See `LICENSE` and `COPYRIGHT.md` for full details.
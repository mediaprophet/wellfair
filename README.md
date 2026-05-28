# wellfair

**wellfair** is a locally-hosted Personal Wellbeing Informatics Vault and semantic data services platform developed independently by Timothy Charles Holborn.

This repository includes the `health-to-solid` capability for Samsung Health export ingestion, ontology-driven semantic mapping, and Solid-compatible RDF export. It also provides the foundation for broader wellfair extensions such as welfare analytics, privacy-aware provenance, and secure local-first data controls.

It ingests Samsung Health export data, normalizes it with a YAML-driven ontology, and emits Solid-compatible RDF (Turtle + JSON-LD) for local prototyping, analysis, and visualization.

## Browser demo (WASM)

A lightweight browser demo running the Rust core compiled to WebAssembly is available at:

**<https://mediaprophet.github.io/wellfair/>**

All files you upload are processed locally in your browser and are not transmitted to any server.

## About Wellfair

`wellfair` is the broader project identity for this repository. `health-to-solid` remains the core Samsung Health-to-RDF ingest pipeline, while `wellfair` expands the scope to include:
- fair-terms wellbeing informatics and welfare-aware modeling
- local-first data control, provenance, and optional decentralized exports
- Sanctuary Mode for highly sensitive personal data
- future browser/WASM and cross-platform runtime support

## What it does

- Ingests Samsung Health export folders containing CSVs and optional `jsons/`
- Normalizes records into a unified internal format
- Maps health data to RDF using configurable ontology templates
- Outputs Solid-style pod content with `/health/{type}/{YYYY-MM}.ttl`
- Presents interactive dashboards and analysis via a Streamlit UI
- Includes sleep analytics, personal health, mental health, location, life events, and vault administration modules

## Key components

- `src/`: Python parsing, normalization, RDF transformation, and export logic
- `ui/`: Streamlit application and UI tabs for data exploration, analytics, and administration
- `config/ontology_template.yaml`: editable ontology mappings and transform rules
- `data/synthetic_samsung_export/`: self-contained synthetic Samsung Health export test set
- `data/demo/gemini/samsung_export/`: demo export folder structure
- `wellfare-core/`: Rust library crate for shared data processing and future WASM/portable runtime support
- `tests/`: validation tests for synthetic data processing
- `output/`: generated dataset exports and Solid pod artifacts

## Current feature set

- Samsung Health export ingestion with optional accompanying JSON payloads
- Template-driven semantic mapping via YAML
- Timezone-aware date/time normalization
- Multiple health domains: sleep, steps, heart rate, weight, activity, and more
- Streamlit UI organized for personal health, analytics, and vault management
- Sleep analytics with score generation, trend analysis, and recommendation insights
- Modular ontology strategy supporting schema.org, QUDT, PROV-O, and custom health properties

## Quick start

```bash
cd c:\Projects\health
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python scripts/generate_synthetic_export.py
streamlit run ui/app.py
```

On Unix/macOS:

```bash
chmod +x run.sh
./run.sh
```

## Recommended data setup

- Use the sample export data in `data/synthetic_samsung_export/` for first-time testing
- Use `data/demo/gemini/samsung_export/` for a more realistic Samsung export structure
- Point the UI to the folder that contains `com.samsung.health.*.csv` and optional `jsons/`

## Project layout

```text
├── config/ontology_template.yaml
├── data/demo/gemini/samsung_export/
├── data/demo/gemini/solid_pod/
├── data/synthetic_samsung_export/
├── output/
├── scripts/generate_synthetic_export.py
├── src/
├── tests/test_synthetic.py
├── ui/app.py
├── wellfare-core/
├── LICENSE
└── COPYRIGHT.md
```

## Extending the ontology

Edit `config/ontology_template.yaml` to change mappings, add new data types, or override transform behavior.

Supported transform functions include:

- `unix_ms_to_iso_with_offset`: convert `start_time` + `time_offset` to ISO datetime
- `minutes_to_iso_duration`: convert minutes to `PT{n}M`

See `config/ontology_template.yaml` for current mappings, aliases, and type definitions.

## Testing

```bash
python scripts/generate_synthetic_export.py
pytest tests/test_synthetic.py -v
```

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.

Copyright © 2025–2026 Timothy Charles Holborn.

See `LICENSE` and `COPYRIGHT.md` for full details.
 
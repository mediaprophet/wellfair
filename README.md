# health-to-solid

**Copyright:** © 2025–2026 **Timothy Charles Holborn** ([email](mailto:timothy.holborn@gmail.com), [LinkedIn](https://www.linkedin.com/in/ubiquitous/)). 

Desktop-first Python pipeline: **Samsung Health export** → **YAML-driven ontology** → **Solid-ready RDF** (Turtle + JSON-LD).

This app serves as a Personal Wellbeing Informatics Vault for local RDF prototyping, analysis, and visualization.

## Features

### Core Features
- Load Samsung Health export folders (CSVs + optional `jsons/`)
- **100% template-driven** RDF via `config/ontology_template.yaml` (reloadable at runtime)
- Timezone-aware timestamps from `start_time` + `time_offset`
- Solid-style pod output: `/health/{type}/{YYYY-MM}.ttl`
- Charts and tables: weight, steps, heart rate

### 💤 World-Class Sleep Analytics Dashboard (NEW!)
- **Sleep Quality Score** (0-100): AI-calculated metric combining duration, efficiency, and consistency
- **Advanced Trend Analysis**: Detect improving/declining/stable patterns with daily change rates
- **Personalized Insights**: Context-aware recommendations tailored to your sleep patterns
- **Week-over-Week Comparison**: Track progress and improvements automatically
- **Sleep Architecture Analysis**: REM/Deep/Light sleep distribution with optimal targets
- **Hypnogram Visualization**: Detailed night-by-night sleep stage analysis
- **Professional KPI Cards**: Real-time sleep metrics with visual indicators

For detailed sleep analytics documentation, see [SLEEP_ANALYTICS_GUIDE.md](SLEEP_ANALYTICS_GUIDE.md) and [SLEEP_ANALYTICS_QUICKSTART.md](SLEEP_ANALYTICS_QUICKSTART.md).

### 🎯 Improved Navigation (NEW!)
- **Cleaner Main Navigation**: Reduced to 5 core health data sections
- **Dedicated Settings Menu**: Vault Administration moved to toggleable settings panel
- **Better Information Architecture**: Administrative tasks separated from health exploration

For navigation details, see [NAVIGATION_UPDATE.md](NAVIGATION_UPDATE.md).

## Quick start

```bash
cd health-to-solid   # or project root (c:\Projects\health)
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python scripts/generate_synthetic_export.py
streamlit run ui/app.py
```

Or on Unix:

```bash
chmod +x run.sh
./run.sh
```

## Project layout

```
├── config/ontology_template.yaml   # editable mappings
├── 20250221_SamsungHealth/           # real Samsung export (default)
├── data/synthetic_samsung_export/    # small synthetic test set
├── src/                              # loader, normalizer, RDF, exporters
├── ui/app.py                         # Streamlit UI
├── tests/test_synthetic.py
└── output/solid_pod/                 # generated on export
```

## Ontology strategy (hybrid)

| Layer | Role |
|-------|------|
| **schema.org** | Primary types (`SleepAction`, `ExerciseAction`, `QuantitativeValue`) |
| **QUDT** | Units via `qudt-unit:` (Kilogram, BeatsPerMinute, …) |
| **PROV-O** | `prov:wasDerivedFrom` on each observation |
| **health:** | Samsung-specific properties + `health:semanticReference` |
| **SNOMED / LOINC / FHIR** | Optional URI links in **clinical mode** (UI sidebar) — no full ontology import |

Add or change data types under `mappings:` in `config/ontology_template.yaml`. Supported transforms:

| Transform | Purpose |
|-----------|---------|
| `unix_ms_to_iso_with_offset` | `start_time` ms + `time_offset` → ISO datetime |
| `minutes_to_iso_duration` | Minutes → `PT{n}M` |

## Real Samsung export

Point the UI at your unzipped export folder. Default: **`20250221_SamsungHealth/`** at the project root (the app auto-finds the inner `samsunghealth_*` folder with CSVs + `jsons/`).

CSV filenames follow `com.samsung.health.*.{timestamp}.csv` (and `com.samsung.shealth.*` variants). See `mapping_aliases` in the ontology template for tracker filename differences.

## Future extensions

- Pathology PDF loader → same normalized dict format
- Google Timeline / environmental data
- New YAML mapping blocks only — no core code changes

## Tests

```bash
python scripts/generate_synthetic_export.py
pytest tests/test_synthetic.py -v
```

## License

GNU General Public License v3.0 (or later), consistent with [HealthPod](https://github.com/humancentrichealth/healthpod). See [COPYRIGHT.md](COPYRIGHT.md).

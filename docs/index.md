# wellfair Documentation

This documentation site is published to GitHub Pages from the `docs/` folder.

## Overview

`wellfair` is the broader project for Personal Wellbeing Informatics and semantic data services. This site documents the project’s current capabilities and showcases the `health-to-solid` Samsung Health-to-RDF conversion demo.

It ingests Samsung Health export data, normalizes it using a YAML-driven ontology, and exports Solid-compatible RDF.

> Note: GitHub Pages hosts this documentation site only. The Streamlit app itself is a Python application and must be run locally or hosted on a proper application platform.

## Quick start

```bash
cd c:\Projects\health
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python scripts/generate_synthetic_export.py
streamlit run ui/app.py
```

## Documentation

- Main repository README: [README.md](../README.md)
- License: [LICENSE](../LICENSE)
- Copyright: [COPYRIGHT.md](../COPYRIGHT.md)
- WASM browser demo: [Run the demo](app.html)
- Sleep analytics docs: [SLEEP_ANALYTICS_GUIDE.md](../SLEEP_ANALYTICS_GUIDE.md)
- Quickstart: [SLEEP_ANALYTICS_QUICKSTART.md](../SLEEP_ANALYTICS_QUICKSTART.md)
- Navigation update: [NAVIGATION_UPDATE.md](../NAVIGATION_UPDATE.md)

## Status

This project is deployed as a documentation site only. App runtime hosting is not provided by GitHub Pages.

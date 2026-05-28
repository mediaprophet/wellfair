# health-to-solid Documentation

This documentation site is published to GitHub Pages from the `docs/` folder.

## Overview

health-to-solid is a locally-hosted Personal Wellbeing Informatics Vault and RDF export pipeline developed independently by Timothy Charles Holborn.

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
- Sleep analytics docs: [SLEEP_ANALYTICS_GUIDE.md](../SLEEP_ANALYTICS_GUIDE.md)
- Quickstart: [SLEEP_ANALYTICS_QUICKSTART.md](../SLEEP_ANALYTICS_QUICKSTART.md)
- Navigation update: [NAVIGATION_UPDATE.md](../NAVIGATION_UPDATE.md)

## Status

This project is deployed as a documentation site only. App runtime hosting is not provided by GitHub Pages.

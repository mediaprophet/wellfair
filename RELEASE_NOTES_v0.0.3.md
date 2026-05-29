# Release Notes — Episteme:WellFair v0.0.3

**Released:** 30 May 2026  
**Branch:** `release/v0.0.3`  
**Tag:** `v0.0.3`

---

## Summary

v0.0.3 completes the first full semantic pipeline sprint — the Rust/WASM core now
carries a real in-browser RDF store, SHACL validation, and HuBMAP anatomical linking.
The extension framework makes the Python-side pipeline composable. The philosophical
foundation of the project is now documented in full.

---

## What's new

### Rust / WASM Core (`wellfare-core`)
- **oxigraph RDF store** — health data loaded into an in-browser SPARQL triple store;
  no server required. Supports SELECT, ASK, and CONSTRUCT queries.
- **SHACL-via-SPARQL validation** — sleep efficiency range, HR physiological range,
  and trauma record shapes implemented as SPARQL ASK queries running in-browser.
- **HRA / CCF / UBERON namespaces** — sleep and heart rate Turtle output now includes
  anatomical identifiers linking to the HuBMAP Human Reference Atlas.
- **PROV-O provenance** — every generated triple records its Samsung Health CSV source.
- **Fixed:** GLB loading now uses `fetch()` → `createObjectURL()` — immune to static
  server path confusion across Docker, local, and WASM environments.
- **Fixed:** oxigraph 0.4 API compatibility (previous build used 0.3 call signatures).

### Python / Semantic pipeline
- **HuBMAP HRA SPARQL client** (`src/hra_client.py`) — queries `lod.humanatlas.io`
  for cell types and biomarkers by UBERON organ ID, with local Turtle cache.
- **Extension framework** (`extensions/`) — pluggable, opt-in architecture:
  - `shacl_validator` — pyshacl integration for extended shape validation
  - `n3_reasoner` — EYE binary + N3 rule files for causal/clinical reasoning
  - `local_llm` — Ollama PDF parsing stub (Phase 6)
- **RDF transformer fix** — `graph_for_data_type()` now uses correct Samsung Health
  data type keys (`com.samsung.shealth.sleep` etc.) and numeric column types.

### Developer Tools
- Built-in test suite (Dev Tools tab) covering all pipeline layers:
  WASM CSV parsing, Turtle RDF generation, oxigraph SPARQL, SHACL shapes,
  Python RDF transformer, HRA client, extensions, and static assets.
  All tests runnable from the UI without leaving the app.

### Documentation
- **README** fully rewritten: mobile-first PWA install instructions, architecture
  diagram, capability table, P3 / P3A / P3-SWA terminology introduced.
- **Philosophical foundation** — the *untransferable code* concept documented;
  language grounded in the semiotics of natural personhood, inalienable dignity,
  lived experience, and peace infrastructure. "Sovereign" replaced throughout with
  the more precise language of the natural person and their inalienable agency.
- **CONCEPTS.md** (new) — conceptual framework document for AI agents and contributors;
  defines key terms and maps each to a concrete design decision.

---

## Test results (v0.0.3 at tag)

| Suite | Result |
|---|---|
| WASM CSV parsing (browser) | ✅ Pass |
| WASM Turtle RDF generation | ✅ Pass |
| WASM SPARQL SELECT + ASK (oxigraph) | ✅ Pass |
| WASM SHACL-via-SPARQL (6 shapes) | ✅ Pass |
| Python RDF transformer (20 triples, 3.6ms) | ✅ Pass |
| Static assets (WASM 3.2MB, 7/7 GLBs, 11/11 HRA) | ✅ Pass |

---

## Known limitations / next sprint scope

- SWI-Prolog WASM (`swipl-wasm`) not yet integrated — Phase 5 evaluation pending
- Local LLM (Ollama) extension is a stub — Phase 6
- HRA SPARQL client requires network; offline fallback not yet implemented
- `use_container_width` deprecation warnings from Streamlit (cosmetic only)

---

## Upgrade notes

No breaking changes to data formats or export paths. The Samsung Health CSV pipeline
is backward-compatible. The extension framework is additive — no existing functionality
depends on extensions being installed.

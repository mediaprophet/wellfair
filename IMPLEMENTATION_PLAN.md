# WellFair v0.0.3-dev — Implementation Plan

> Started: 2026-05-29  
> Branch: master  
> Covers: 3D GLB fix, Rust/WASM RDF store, HuBMAP semantic integration, reasoning extensions

---

## Architecture Overview

```
Browser (WASM)                          Local Daemon / Python-side
────────────────────────────────        ──────────────────────────────────
wellfare-core (Rust → WASM)             extensions/ (Python, opt-in)
  ├── CSV → Turtle          (done)        ├── hra_client/   SPARQL → HuBMAP KG
  ├── RDF-Star privacy      (done)        ├── n3_reasoner/  EYE binary + .n3 rules
  ├── SHACL-via-SPARQL      (Phase 2)     ├── swi_prolog/   optional upgrade
  ├── oxigraph RDF store    (Phase 2)     └── local_llm/    Ollama PDF parsing
  └── HRA/CCF namespaces    (Phase 2)
```

**Key constraints:**
- PWA bundle must stay lean — no heavy binaries in WASM path
- Extensions download on first use, teardown() releases memory
- Nothing loads until triggered by user action or data pattern
- People described with SHACL/RDFS shapes, not OWL class membership
- N3Logic for causal/clinical reasoning (not OWL entailment)
- SWI-Prolog WASM (`swipl-wasm`) to be evaluated for in-browser N3

---

## Phase 1 — Fix 3D Viewer & Stabilise (immediate)

### 1.1 Fix GLB loading (`ui/tabs/anatomy_3d.py`)
**Problem:** `resolveAssetUrl()` hardcodes `/app/static/models/` — only valid in Docker.  
**Fix:** `fetch()` GLB as ArrayBuffer → `URL.createObjectURL(blob)` → pass blob URL to GLTFLoader. Immune to static server path confusion.  
**Also:** Improve error message to show actual URL attempted + HTTP status.  
**Files:** `ui/tabs/anatomy_3d.py` (~60 lines)

### 1.2 Holographic placeholder during load
Add a wireframe bounding-box mesh that renders immediately while GLB streams.  
**Files:** `ui/tabs/anatomy_3d.py` (~20 lines)

---

## Phase 2 — Rust Core: oxigraph + HRA namespaces

### 2.1 Add `oxigraph` to `wellfare-core`
```toml
oxigraph = { version = "0.4", default-features = false, features = ["js"] }
```
- Load Turtle output from existing `*_to_turtle()` functions into an in-memory store
- Expose `query_health_graph(sparql: &str) -> Result<String, JsValue>` via wasm-bindgen
- Returns JSON SPARQL results

### 2.2 SHACL-via-SPARQL shapes
Encode validation constraints as SPARQL ASK/SELECT queries (no OWL).  
**New files:**
```
wellfare-core/src/shapes/
  sleep.rq          -- efficiency 0-100, duration > 0
  cardiovascular.rq -- HR within physiological range
  trauma.rq         -- required fields for trauma assessment
```
Expose `validate_graph(shape_id: &str) -> Result<String, JsValue>`.

### 2.3 Add HRA/CCF/UBERON namespaces to `rdf.rs`
```rust
@prefix ccf:    <http://purl.org/ccf/> .
@prefix uberon: <http://purl.obolibrary.org/obo/UBERON_> .
@prefix cl:     <http://purl.obolibrary.org/obo/CL_> .
@prefix hra:    <https://purl.humanatlas.io/> .
```
Add `uberon_id` field to HeartRateRecord, SleepRecord etc. so RDF output links to HRA KG.

---

## Phase 3 — HuBMAP Semantic Client (`src/hra_client.py`)

**SPARQL endpoint:** `https://lod.humanatlas.io/sparql`  
**grlc REST gateway:** `https://apps.humanatlas.io/api/grlc/`  
**Python client:** `hra-api-client` (PyPI)

### 3.1 Core queries
- `asctb_for_uberon(uberon_id)` → cell types + biomarkers for an organ
- `cell_types_in_organ(organ_label)` → list of CL terms
- `biomarkers_for_cell_type(cl_id)` → gene/protein markers

### 3.2 TTL cache
Cache each query result as `data/hra_cache/{uberon_id}.ttl`.  
On cache hit: load from disk (no network). TTL: 30 days.

### 3.3 Mesh annotation bridge
Feed results into `anatomy_3d.py` organ hover labels:  
`Heart → Cardiomyocytes, Endothelial cells | Biomarkers: MYH7, TNNT2`

### 3.4 Extend `ontology_template.yaml`
Add `ccf:`, `uberon:`, `cl:`, `hra:` namespaces alongside existing FHIR/SNOMED/LOINC.

---

## Phase 4 — Extension Framework (`extensions/`)

### Directory structure
```
extensions/
  __init__.py          ExtensionRegistry: discover, download, activate, teardown
  base.py              ExtensionBase ABC: name, requires_daemon, download(), load(), health_check(), teardown()
  
  shacl_validator/     Pure pip (pyshacl), always available
    shapes/            .ttl SHACL shape files per health domain
  
  n3_reasoner/         Downloads EYE binary (~15MB) on first use
    rules/             .n3 rule files for clinical patterns
      adrenal_fatigue.n3
      sleep_debt.n3
      trauma_cascade.n3
      cardiovascular_risk.n3
  
  swi_prolog/          Optional: checks `swipl` on PATH, falls back to EYE
    rules/             .pl Prolog rules for complex constraint solving
  
  local_llm/           Requires Ollama daemon OR llama-cpp-python
    pdf_parser.py      pdfplumber + LLM structured extraction
    symptom_extractor.py
    models.yaml        name, size_gb, use_case, quantisation
  
  hra_client/          Thin wrapper around src/hra_client.py for extension API
```

### Memory contract
- Extensions never load until `registry.activate(name)` called
- Each has `teardown()` that releases process/memory
- `requires_daemon=True` extensions cannot run in Stlite/Pyodide PWA
- Size budget per extension documented in `models.yaml` / extension metadata

### N3 rule format (EYE)
```n3
# rules/adrenal_fatigue.n3
@prefix health: <https://health.example.org/ns#> .
@prefix : <#> .

{ ?person health:sleepHours ?h .
  ?person health:restingHR ?hr .
  ?h math:lessThan 5 .
  ?hr math:greaterThan 90 }
  => { ?person health:pattern health:AdrenalFatigueSuspected } .
```

---

## Phase 5 — SWI-Prolog WASM Evaluation

Evaluate `swipl-wasm` (~8MB WASM binary) for in-browser N3Logic:
- Test: can `swipl-wasm` load `library(n3)` pack?
- If yes: N3 rules run in browser with no daemon
- If no: EYE remains the N3 engine, SWI-Prolog is daemon-only

Decision gate: complete before committing to extension daemon architecture for N3.

---

## Phase 6 — Local LLM Integration

**Models (via Ollama):**
| Use case | Model | RAM |
|---|---|---|
| PDF / clinical note extraction | Phi-3.5-mini Q4 | ~2.2GB |
| Symptom pattern matching | Llama 3.2 3B Q4 | ~2.0GB |
| Lightweight triage/tagging | Qwen2.5 1.5B Q4 | ~1.0GB |

**Interface:** Ollama REST (`localhost:11434`) or `llama-cpp-python` direct  
**Use cases:**
- `document_ingestion.py` — extract structured health data from uploaded PDFs
- `symptom_extractor.py` — freetext → RDF triples via JSON schema output
- Future: explain N3 rule conclusions in plain language

---

## Progress Log

| Date | Phase | Status | Notes |
|---|---|---|---|
| 2026-05-29 | Setup | ✅ Done | v0.0.3-dev tagged, plan written |
| 2026-05-29 | 1.1 GLB fix | ✅ Done | fetch→blob pipeline, multi-path probe, detailed error UI |
| 2026-05-29 | 1.2 Placeholder mesh | ✅ Done | Wireframe human silhouette, swapped out on GLB load |
| 2026-05-29 | 2.1 oxigraph | ✅ Done | store.rs — HealthStore, SPARQL query, WasmHealthStore WASM binding |
| 2026-05-29 | 2.2 SHACL shapes | ✅ Done | shapes.rs — 6 SPARQL-ASK constraints + validate_health_turtle() WASM binding |
| 2026-05-29 | 2.3 HRA namespaces | ✅ Done | rdf.rs — ccf:, uberon:, cl:, hra:, rdfs:, sh: added to prefix set |
| 2026-05-29 | 3.1 hra_client.py | ✅ Done | SPARQL client, OrganAnnotation, ORGAN_UBERON_MAP, to_mesh_tooltip(), to_rdf_turtle() |
| 2026-05-29 | 3.2 TTL cache | ✅ Done | JSON cache in data/hra_cache/, 30-day TTL |
| 2026-05-29 | 3.3 Mesh annotations | 🔲 Todo | Wire hra_client into anatomy_3d.py bioData payload |
| 2026-05-29 | 4. Extension framework | ✅ Done | base.py, registry.py, shacl_validator/, n3_reasoner/ (EYE + 4 rule files), local_llm/ |
| — | 5. swipl-wasm eval | 🔲 Todo | |
| — | 6. Wire hra_client → 3D viewer | 🔲 Todo | Pass mesh tooltip JSON into anatomy_3d.py |
| ⚠️ | Rust native linker | 🔲 Blocked | MinGW + MSVC both broken on host. wasm-pack build may work. Needs mingw64 fix or VS BuildTools |

---

## Key References

- HuBMAP SPARQL: `https://lod.humanatlas.io/sparql`
- grlc REST: `https://apps.humanatlas.io/api/grlc/`
- HRA Python client: `hra-api-client` (PyPI)
- EYE reasoner: `https://github.com/eyereasoner/eye`
- swipl-wasm: `https://github.com/SWI-Prolog/swipl-wasm`
- oxigraph: `https://github.com/oxigraph/oxigraph`
- pyshacl: `https://github.com/RDFLib/pySHACL`
- CCF 3D models: `https://github.com/hubmapconsortium/ccf-3d-reference-object-library`

## Design Decisions

- **SHACL/RDFS over OWL**: people described as shapes/constraints, not class instances
- **N3Logic over OWL reasoning**: causal chains, not entailment hierarchies
- **Blob URL for GLB**: bypasses Streamlit static path confusion entirely
- **TTL disk cache for HRA**: avoids repeated queries to 125GB remote KG
- **Extension download-on-demand**: keeps PWA bundle lean, respects memory budget
- **EYE as default N3 engine**: ~15MB binary, no SWI-Prolog dep required
- **SWI-Prolog optional**: upgrade path for users needing proof traces or Prolog rules

# Differential Diagnostics Informatics Subsystem — Implementation Plan
# WellFair v0.1+

> This document captures the full scope of the informatics subsystem as
> designed across the architecture discussion. It is the authoritative staging
> reference. The `anatomy-mappings.ttl` in this directory is Stage A output.

---

## Design Intent

This is a **reasoning and evaluation engine** that applies the differential
diagnosis paradigm to health, welfare, and legal circumstances. The 3D
anatomical viewer is one accessibility layer for presenting results — it is
not the primary purpose.

The core capability is: given a user's private circumstances (health metrics,
social factors, legal status) and a set of publicly published expert rulesets
(compiled from peer-reviewed studies or legislation), reason locally and
privately to surface relevant implications, risks, or entitlements — and
explain why.

**Three reasoning principles govern the design:**

1. **Abductive reasoning** — infer the most parsimonious explanation from
   incomplete observations. Rules express necessary-and-sufficient conditions,
   not correlations.

2. **Occam's Razor** — prefer the simplest unified explanation. The engine
   should not multiply conditions without cause.

3. **Hickam's Dictum** — a subject can have as many simultaneous conditions
   as their circumstances warrant. The engine must not collapse overlapping
   condition threads. Multi-condition accumulation is a first-class requirement.

**Two hard constraints that override everything else:**

- All reasoning runs locally in the browser via SWI-Prolog WASM. No user
  data leaves the device. No query is sent to an external inference service.
- People are never modelled as OWL class members. Conditions are asserted as
  facts about a subject using SHACL/RDFS shapes. N3Logic for causal reasoning.

---

## The Two Primary Audiences

### Audience 1: Domain Experts (Biomedical, Legal, Welfare)
People who understand the science or legislation but do not program.
Their workflow: **ingest unstructured research → validate → publish signed rulesets**.
They need an authoring tool, not access to the user runtime.

### Audience 2: End Users (Welfare Subjects)
People evaluating their own circumstances against established knowledge.
Their workflow: **provide private data → select rulesets → receive explanation**.
They must not be required to understand RDF, Prolog, or ontologies.
The 3D body is an accessibility aid for this group.

**The separation is a hard architectural constraint.** Expert knowledge is
published independently of the user runtime. A new study can be added without
touching the user's application. These two systems share data formats but not
code paths.

---

## Ontologies in Use

| Ontology | Purpose | When Required |
|---|---|---|
| FMA (Foundational Model of Anatomy) | Spatial-anatomical structure, part relationships, hierarchy | All stages involving anatomy |
| SNOMED-CT (`http://snomed.info/id/`) | Clinical conditions, disorders, findings, procedures | Condition → anatomy implications |
| HPO (Human Phenotype Ontology) | Phenotypic abnormalities, especially for complex presentations (EDS, rare diseases) | Phenotypic profiling rulesets |
| LOINC | Laboratory tests and biomarker parameter codes (HbA1c, systolic BP, etc.) | Biomarker-triggered rules |
| UBERON | Cross-species anatomy bridge; already in HuBMAP asset manifest | HuBMAP GLB mesh alignment |
| SKOS | Concept labelling and notation for system layer identifiers | Schema glue |
| Custom `app:` / welfare ontology | Welfare eligibility, rights-based assessments, social determinants | Stage F |

**Ontology constraint:** The LLM extraction pipeline must be forced to look up
or infer standard URIs from the above list. It must not invent new terms.
Unconstrained term invention breaks interoperability between rulesets from
different experts.

---

## Stage A — Data Schema and Tooling Foundation
**Prerequisite for all other stages.**

### A1. Anatomy Mappings (DONE)
File: `shared-schemas/anatomy-mappings.ttl`

Maps Three.js scene node names (HuBMAP GLB internal names and procedural
geometry IDs) to FMA anatomical URIs, UBERON crossrefs, and condition →
anatomy implication sets with severity weights.

HuBMAP node names follow the pattern `<Institution>_<Sex>_<Organ>[_<Laterality>]`
(e.g., `VH_M_Kidney_L`, `Allen_M_Brain`). Procedural geometry uses the
`proc_` prefix convention (e.g., `proc_heart`, `proc_adrenal_l`).

### A2. Procedural Mesh Naming (CODE CHANGE REQUIRED)
File: `ui/tabs/anatomy_3d.py`

The procedural Three.js geometry objects (skull, heart, aorta, pancreas,
adrenals, brain, spinal cord, lungs, stomach, intestines, kidneys, lymph, eye)
do not currently have `.name` assigned. `scene.getObjectByName()` cannot
resolve them.

Each procedural mesh must have its `.name` set to match the `app:hasMeshId`
values in `anatomy-mappings.ttl` before being added to the scene:
```javascript
heart.name = "proc_heart";
brain.name = "proc_brain";
pancreas.name = "proc_pancreas";
adrenalL.name = "proc_adrenal_l";
// etc.
```

### A3. LOINC Biomarker Parameter Vocabulary
File: `shared-schemas/biomarker-vocabulary.ttl`

A lookup table mapping plain Prolog parameter names to LOINC codes and units:
```turtle
app:Param_HbA1c
    app:prologName "hba1c" ;
    app:loincCode  "4548-4" ;
    app:unit       "%" .

app:Param_SystolicBP
    app:prologName "systolic_bp" ;
    app:loincCode  "8480-6" ;
    app:unit       "mmHg" .
```
This enables interoperability when a user's data arrives from a FHIR source
using LOINC codes rather than local parameter names.

### A4. Mock User Profile Documents
Directory: `shared-schemas/test-profiles/`

Formal RDF (Turtle) documents representing test subjects for validation:
- `mock_profile_healthy.ttl` — no conditions, all metrics nominal
- `mock_profile_diabetic_severe.ttl` — Type 2 DM, HbA1c 9.2, systolic 145
- `mock_profile_hypertensive.ttl` — essential hypertension, systolic 162
- `mock_profile_eds.ttl` — EDS hypermobile type, joint hypermobility reported
- `mock_profile_comorbid.ttl` — DM + hypertension + early CKD (Hickam test case)
- `mock_profile_welfare_ndis.ttl` — NDIS eligibility test case (non-clinical)

Each profile uses `user_fact` and `user_metric` predicates matching the Prolog
rule interface, so profiles double as both SPARQL source data and Prolog test
input.

---

## Stage B — Expert Knowledge Authoring Suite
**Depends on: Stage A**

### B1. LLM Extraction Prompt Engineering
The lightweight local LLM receives a structured system prompt instructing it
to parse an input text (from a PDF, DOI-resolved paper, or pasted abstract)
and return a JSON payload conforming to this schema:

```json
{
  "study_metadata": {
    "doi": "string",
    "title": "string",
    "authors": ["string"],
    "publication_year": "integer",
    "journal": "string"
  },
  "logical_implications": [
    {
      "condition_indicated": "snomed:<id>",
      "biomarker_triggers": [
        {
          "loinc_code": "string",
          "prolog_param": "string",
          "operator": "greater_than | less_than | equals | between",
          "value": "number",
          "value_upper": "number | null"
        }
      ],
      "affected_anatomical_structures": [
        {
          "fma_uri": "fma:<term>",
          "severity_weight": "high | medium | low",
          "mechanism_summary": "string (1–2 sentences, plain English)"
        }
      ]
    }
  ]
}
```

The LLM must be instructed to use only URIs from the approved ontology list
(FMA, SNOMED, HPO, LOINC). If it cannot identify a standard URI, it must flag
the field as `"unresolved"` rather than inventing a term.

### B2. Rule Generation Compiler
A utility (Python script or Rust module) that takes the validated JSON from B1
and emits two files per study:

**Output 1: `<study_id>.ttl` — Provenance metadata**
```turtle
<https://wellfair.app/ruleset/study_diabetes_microvascular_2026>
    a app:Ruleset ;
    dcterms:source <https://doi.org/10.1016/j.jdiab...> ;
    dcterms:title "Microvascular Complications of Type 2 Diabetes..." ;
    dcterms:created "2026-05-29"^^xsd:date ;
    app:authoredBy <https://expert.example.org/profile#me> ;
    app:prologFile "study_diabetes_microvascular_2026.pl" .
```

**Output 2: `<study_id>.pl` — Pure Prolog logic**
```prolog
% study_diabetes_microvascular_2026.pl
% Source: doi:10.1016/j.jdiab...
% DO NOT EDIT — generated by WellFair Rule Compiler

implication_target(User, 'http://purl.org/sig/ont/fma/Left_renal_artery', medium) :-
    user_fact(User, 'http://snomed.info/id/44054006'),
    user_metric(User, hba1c, Value),
    Value > 7.0.

implication_target(User, 'http://purl.org/sig/ont/fma/Right_renal_artery', medium) :-
    user_fact(User, 'http://snomed.info/id/44054006'),
    user_metric(User, hba1c, Value),
    Value > 7.0.

implication_target(User, 'http://purl.org/sig/ont/fma/Retina', high) :-
    user_fact(User, 'http://snomed.info/id/44054006'),
    user_metric(User, hba1c, Value),
    Value > 8.0.
```

### B3. Expert Review UI
A form-based interface (not 3D) for the expert to:
1. Paste a DOI or PDF text
2. Review the LLM's proposed JSON extraction, field by field
3. Correct any unresolved URIs or incorrect severity weights
4. Trigger the rule compiler
5. Sign and publish the output

This UI does not need to be polished. Accuracy of the output matters more
than visual design at this stage.

### B4. Expert Spatial Preview
A read-only, restricted copy of the 3D viewer embedded in the authoring tool.
When the expert approves a set of implications, they can click "Preview 3D"
to see which mesh structures would highlight before publishing.

This is a sanity check: if an EDS rule lights up the entire body uniformly
rather than joints specifically, the expert can identify the ontology mapping
error before the ruleset is published.

### B5. Authoring Sandbox (Test Runner)
Before publishing, the expert runs their compiled ruleset against the mock
profiles from Stage A4. The sandbox shows:
- Which profiles triggered which implications
- Whether any rules loop infinitely (Prolog cycle detection)
- Whether threshold boundaries behave correctly (test at value, value-0.01,
  value+0.01)
- Whether multi-condition profiles (the comorbid mock) accumulate correctly

A ruleset that fails the sandbox cannot be published.

### B6. Cryptographic Signing
Each published ruleset pair (`.pl` + `.ttl`) must be signed with the expert's
key (WebID-linked keypair or similar). The user-side runtime verifies the
signature before loading any rules. This is the trust chain that prevents
malicious or tampered rulesets from being loaded.

Implementation: use a lightweight detached signature (e.g., Ed25519) stored
alongside the files. The user app verifies on download.

---

## Stage C — User-Facing Evaluation Runtime
**Depends on: Stage A, and at least one published ruleset from Stage B**

### C1. User Data → RDF Triple Store
The user's records (health metrics from the app, social factors, reported
conditions) are serialized as Turtle and loaded into the local oxigraph store
via `wellfare-core`'s existing `load_turtle()` / `query()` interface.

Facts use the predicate pattern the Prolog rules expect:
```turtle
<urn:wellfair:user:me>
    app:userFact snomed:44054006 ;          # has condition: T2 DM
    app:userMetric [
        app:paramName "hba1c" ;
        app:value 8.3
    ] .
```

### C2. SPARQL-to-Prolog Fact Bridge
Before invoking the WASM engine, run a SPARQL SELECT against the local store
to extract only the facts relevant to the current ruleset. Transform results
into Prolog `assert` calls:

```javascript
// SPARQL result row: { param: "hba1c", value: "8.3" }
// → asserted into WASM as:
prolog.assertz(`user_metric(me, hba1c, 8.3).`);
prolog.assertz(`user_fact(me, 'http://snomed.info/id/44054006').`);
```

Do not hand the user's entire RDF graph to Prolog. Only extract what the
currently loaded ruleset requires. This limits WASM memory pressure and
prevents inadvertent data leakage into the rule evaluation scope.

### C3. SWI-Prolog WASM Lifecycle Manager
Runs in a **Web Worker** (never on the main UI thread).

Responsibilities:
- Initialize the WASM module once; reuse the instance across evaluations
- Download and cache rule files (IndexedDB); verify cryptographic signature
  before loading (Stage B6)
- Load a ruleset via `consult()`, assert user facts, run the query, retract
  user facts, unload the ruleset
- Expose a clean async message interface to the main thread:
  ```
  { type: "evaluate", rulesetUrl: "...", userFacts: [...] }
  → { type: "result", implications: [...], proofTrace: [...] }
  ```
- Detect and time-limit evaluations to prevent infinite loops in malformed
  rulesets (even if B5 sandbox passed)

### C4. Multi-Condition Accumulation (Hickam Support)
When a user evaluates against multiple rulesets simultaneously (or a single
ruleset that covers comorbidities), the runtime must merge implication results
across condition threads.

Merge rules:
- Same anatomical URI appearing in multiple results: take the **highest**
  severity weight
- All unique anatomical URIs from all conditions are included (no suppression)
- Each result entry retains a list of which rulesets triggered it, for the
  Explainer (C5)

### C5. Explainer Module
Translates the Prolog proof trace and ruleset metadata into a plain-English
explanation for each triggered anatomical structure.

Inputs:
- The anatomical URI (e.g., `fma:Left_renal_artery`)
- The Prolog proof trace (which facts and rules fired)
- The `mechanism_summary` from the compiled `.ttl` (B2)
- The study citation (DOI, title, authors, year)

Output (displayed when user clicks a highlighted mesh):
```
Left Renal Artery — Medium Risk

Your HbA1c of 8.3% exceeds the 7.0% threshold identified in:
  "Microvascular Complications of Type 2 Diabetes" (doi:10.1016/...)
  Journal of Diabetes, 2024.

Mechanism: Sustained hyperglycaemia causes thickening of the glomerular
basement membrane and narrowing of renal arterioles, reducing filtration
capacity over time.

This is an automated evaluation, not a clinical diagnosis.
Discuss with a qualified health professional.
```

The mechanism summary comes from B1's `mechanism_summary` field in the JSON;
the local LLM may optionally rewrite it for readability, but the citation must
be verbatim from the signed `.ttl`.

### C6. Ephemeral Output
The evaluation result (list of `{ anatomyUri, meshId, severity, explanation,
citations }`) exists only in browser session memory. It is:
- Passed to the 3D viewer (Stage D) for visualization
- Displayable as a structured text report (for users who want to print and
  take to a clinician)
- Never written to disk, IndexedDB, or transmitted anywhere

If the user navigates away, the result is gone. A new evaluation is required
to see results again.

---

## Stage D — 3D Spatial Visualization Integration
**Depends on: Stage A (mesh naming), Stage C (evaluation output)**

### D1. Mesh Resolver SPARQL Query
After C4 produces the accumulated implication list, resolve each `anatomyUri`
to a `meshId` via SPARQL against the local `anatomy-mappings.ttl`:

```sparql
PREFIX app: <https://wellfair.app/ontology/>

SELECT ?meshId ?highlightColor WHERE {
  ?element app:mapsToAnatomy ?uri ;
           app:hasMeshId ?meshId .
  OPTIONAL { ?implication app:impliesPathologyIn ?uri ;
                          app:highlightColor ?highlightColor . }
  VALUES ?uri { <http://purl.org/sig/ont/fma/Left_renal_artery>
                <http://purl.org/sig/ont/fma/Retina> }
}
```

### D2. Ontology Hierarchy Traversal for Diffuse Conditions
Some conditions (EDS, atherosclerosis, systemic connective tissue disorders)
implicate a *class* of structures rather than specific named meshes. A direct
`VALUES` query will return nothing if the FMA URI is a parent class (e.g.,
`fma:Joint_structure`) rather than a specific instance.

For these, query the hierarchy:
```sparql
SELECT ?meshId WHERE {
  ?element app:mapsToAnatomy ?specificUri ;
           app:hasMeshId ?meshId .
  ?specificUri rdfs:subClassOf* <http://purl.org/sig/ont/fma/Joint_structure> .
}
```

This returns all meshes that are sub-concepts of the target class — e.g., all
major joints — rather than requiring exact URI match. This is the architectural
difference between direct-target conditions (diabetes → left renal artery) and
diffuse-target conditions (EDS → all joints).

### D3. AnatomyViewerController — Three Render Modes
The controller class must support three semantically distinct render modes,
not just color change:

**Mode 1: highlight** — direct causal target, high confidence
- Emissive color from `app:highlightColor` in `anatomy-mappings.ttl`
- Emissive intensity based on severity (high: 0.9, medium: 0.6, low: 0.3)
- Used for: specific organ/vessel targets

**Mode 2: pulse** — secondary or accumulating risk, draws attention over time
- Animated emissive intensity oscillation (0.3 → 0.7 → 0.3, ~1.5s period)
- Used for: structures at medium severity or implicated by multiple conditions

**Mode 3: stress-shader** — diffuse structural conditions (EDS, connective tissue)
- Geometry or shader-level change to communicate structural vulnerability
  rather than acute pathology (e.g., increased surface noise, reduced opacity,
  joint-area glow without solid fill)
- Used for: EDS joints, spinal instability, pelvic floor laxity

All other meshes not in the current implication set are dimmed (opacity
reduced to ~15% of baseline) to direct visual attention.

### D4. Click-to-Explain Sidebar
When the user clicks any highlighted mesh:
1. Retrieve the explanation from C5's output for that mesh's anatomy URI
2. Display in the existing CSS2D label or a sidebar panel:
   - Structure name
   - Severity level
   - Mechanism summary (plain English)
   - Study citation with DOI link
   - Disclaimer
3. GSAP camera zoom to the selected structure (existing behavior, already
   implemented in `anatomy_3d.py`)

The explanation text is sourced entirely from the evaluation result in session
memory (C6). No additional network calls are made on click.

### D5. System Isolation Mode
When implications are present, the viewer should optionally isolate the
implicated body system (dim all others). This is the "isolates the
Cardiovascular System and Endocrine System, dimming the rest" behavior
described in the Diabetes scenario.

Isolating by system uses the `app:inSystem` property in `anatomy-mappings.ttl`
to determine which layer group to keep visible.

---

## Stage E — Decentralized Distribution
**Depends on: Stage B (signed rulesets exist)**

### E1. IPFS / Solid Pod Publishing
The expert authoring tool (B3) can publish completed, signed rulesets to:
- IPFS (content-addressed; immutable once published)
- A Solid Pod (mutable; expert can update or retract)

The user runtime (C3) fetches by content hash (IPFS) or Pod URL. IPFS is
preferred for stability; Solid is preferred if experts need to issue corrections.

### E2. Rule Registry
A lightweight registry (JSON-LD document) listing available rulesets:
```json
{
  "@context": "https://wellfair.app/registry/context.jsonld",
  "rulesets": [
    {
      "id": "https://ipfs.io/ipfs/<hash>/study_diabetes_microvascular_2026",
      "title": "Microvascular Complications of Type 2 Diabetes",
      "conditions": ["http://snomed.info/id/44054006"],
      "domain": "biomedical",
      "author": "https://expert.example.org/profile#me",
      "published": "2026-05-29"
    }
  ]
}
```

The user app queries this registry to present a browseable list of available
rulesets. The user selects which studies to evaluate against.

### E3. Cryptographic Verification on Download
Before `consult()`-ing any downloaded `.pl` file (C3), the WASM lifecycle
manager verifies the Ed25519 detached signature against the expert's public
key (fetched from their WebID profile). A failed verification aborts the load
and alerts the user.

---

## Stage F — Non-Biomedical Welfare Rules
**Depends on: Stage B (authoring pipeline exists)**

### F1. Welfare / Rights Ontology
File: `shared-schemas/welfare-rights.ttl`

A custom vocabulary for conditions and entitlements not covered by SNOMED
or HPO:
```turtle
welfare:NDISEligibility
    a rdfs:Class ;
    rdfs:label "NDIS Eligibility Criterion" .

welfare:HousingInsecurity
    a rdfs:Class ;
    rdfs:label "Housing Insecurity" .

welfare:IncomeThreshold
    a rdfs:Class ;
    rdfs:label "Income-Based Eligibility Threshold" .
```

### F2. Legislative Text Ingestion
The LLM extraction prompt (B1) must be adapted for legislative and policy
documents, where the "conditions" are eligibility criteria (income, residency,
disability status) and the "implications" are entitlements or services, not
anatomical targets.

The JSON schema output is the same structure; `affected_anatomical_structures`
is replaced by `affected_entitlements` for welfare rules. The Prolog compiler
(B2) emits equivalent rules using welfare predicates instead of FMA URIs.

For welfare rules, the 3D visualization layer (Stage D) is not the primary
output — a structured text report or eligibility checklist is more appropriate.
The architecture must support result presentation without the 3D layer.

### F3. Example Welfare Rulesets
- NDIS eligibility (disability type, functional impact, age, residency)
- Centrelink income support thresholds (income, assets, family status)
- Housing priority assessment (chronic homelessness, domestic violence risk,
  medical vulnerability)

---

## Cross-Cutting Concerns (All Stages)

### Privacy by Design
- User data never leaves the device at any stage
- SPARQL queries run against local store only
- Prolog evaluation runs in WASM Web Worker
- Evaluation output is ephemeral session memory
- Rule files (expert-authored) are public; user facts are private

### Bundle Size Discipline
- SWI-Prolog WASM downloads on first use, not bundled
- Rule files fetch on demand, cached in IndexedDB after first download
- `anatomy-mappings.ttl` is bundled (it is static schema, not dynamic data)
- All heavy reasoning runs in Web Worker to keep UI thread responsive

### No OWL Class Membership for People
Users and subjects are never asserted as members of OWL classes
(`:User a snomed:DiabetesMellitusPatient`). Conditions are facts:
(`user_fact(me, snomed:44054006)`). SHACL/RDFS shapes describe structure;
N3Logic / Prolog Horn clauses handle causal reasoning.

### Disclaimer and Clinical Boundary
Every evaluation result, at every presentation layer, must carry a prominent
disclaimer: this is an automated evaluation against published research, not a
clinical diagnosis or legal advice. The system surfaces information; qualified
professionals interpret and act on it.

---

## File Structure (Target)

```
shared-schemas/
  anatomy-mappings.ttl          ← Stage A1 (done)
  biomarker-vocabulary.ttl      ← Stage A3
  welfare-rights.ttl            ← Stage F1
  test-profiles/
    mock_profile_healthy.ttl
    mock_profile_diabetic_severe.ttl
    mock_profile_hypertensive.ttl
    mock_profile_eds.ttl
    mock_profile_comorbid.ttl
    mock_profile_welfare_ndis.ttl

expert-authoring-tool/
  paper-parser-llm/
    extraction_prompt.txt       ← B1
    extraction_schema.json      ← B1
  rule-compiler/
    compile_ruleset.py          ← B2
  sandbox/
    run_tests.py                ← B5
  ui/                           ← B3, B4

user-runtime-lib/
  engine.js                     ← C2, C3 orchestration
  wasm-worker.js                ← C3 Web Worker
  accumulator.js                ← C4 multi-condition merge
  explainer.js                  ← C5
  visualizer-bridge.js          ← D1, D2, D3, D4

rulesets/                       ← published rulesets (or fetched to cache)
  study_diabetes_microvascular_2026.pl
  study_diabetes_microvascular_2026.ttl
  study_eds_hypermobile_2025.pl
  study_eds_hypermobile_2025.ttl
```

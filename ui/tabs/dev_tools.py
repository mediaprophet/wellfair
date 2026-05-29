# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Developer Tools & Test Suite tab.

Runs in-app tests covering:
  1. WASM Core (wellfare-core) — CSV parsing, RDF generation, SPARQL, SHACL
  2. HRA Client — SPARQL connectivity to lod.humanatlas.io, TTL cache
  3. Extension Framework — registry discovery, shacl_validator, n3_reasoner
  4. SWI-Prolog WASM — probe for swipl-wasm availability (Phase 5 evaluation)
  5. RDF Transformer — Python rdflib pipeline, ontology template
  6. Static Assets — GLB files present, WASM pkg built

Browser-side WASM tests run in an embedded HTML component.
Python-side tests run live in the Streamlit process.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
_STATIC_PKG = _ROOT / "ui" / "static" / "pkg"
_HRA_MODELS = _ROOT / "ui" / "static" / "models" / "hra"
_AVATAR_MODELS = _ROOT / "ui" / "static" / "models"


# ── Result helpers ─────────────────────────────────────────────────────────────
def _pass(label: str, detail: str = ""):
    st.markdown(f"✅ **{label}**" + (f" — {detail}" if detail else ""))

def _fail(label: str, detail: str = ""):
    st.markdown(f"❌ **{label}**" + (f" — {detail}" if detail else ""))

def _warn(label: str, detail: str = ""):
    st.markdown(f"⚠️ **{label}**" + (f" — {detail}" if detail else ""))

def _info(label: str, detail: str = ""):
    st.markdown(f"ℹ️ **{label}**" + (f" — {detail}" if detail else ""))


# ── Test suites ────────────────────────────────────────────────────────────────

def _test_static_assets():
    st.subheader("📦 Static Assets")

    # WASM package
    wasm = _STATIC_PKG / "wellfare_core_bg.wasm"
    js   = _STATIC_PKG / "wellfare_core.js"
    if wasm.exists() and js.exists():
        size_mb = round(wasm.stat().st_size / 1_048_576, 1)
        _pass("WASM package built", f"wellfare_core_bg.wasm ({size_mb} MB)")
    else:
        _fail("WASM package missing", "Run: cd wellfare-core && wasm-pack build --target web --out-dir ../ui/static/pkg")

    # Avatar GLBs
    avatars = ["baseline.glb", "elena.glb", "michael.glb", "rebecca.glb", "margaret.glb", "robert.glb", "jordan.glb"]
    present = [f for f in avatars if (_AVATAR_MODELS / f).exists()]
    missing = [f for f in avatars if f not in present]
    if missing:
        _warn(f"Avatar GLBs: {len(present)}/{len(avatars)}", f"Missing: {', '.join(missing)}")
    else:
        _pass(f"Avatar GLBs: {len(present)}/{len(avatars)} present")

    # HRA organ GLBs
    hra_manifest = _HRA_MODELS / "manifest.json"
    if hra_manifest.exists():
        manifest = json.loads(hra_manifest.read_text())
        organs = manifest if isinstance(manifest, list) else manifest.get("organs", [])
        hra_present = sum(1 for o in organs if (_HRA_MODELS / o.get("file","")).exists())
        _pass(f"HRA organ GLBs: {hra_present}/{len(organs)} present")
    else:
        _warn("HRA manifest not found", "Run: python scripts/download_hra_models.py")


def _test_rdf_transformer():
    st.subheader("🔗 RDF Transformer (Python)")
    try:
        from src.rdf_transformer import OntologyTemplate, graph_for_data_type, TransformOptions
        import pandas as pd
        tmpl_path = next((_ROOT / d / "ontology_template.yaml" for d in ["config", "."] if (_ROOT / d / "ontology_template.yaml").exists()), None)
        if not tmpl_path:
            _warn("ontology_template.yaml not found", "Some transform tests skipped")
            return
        tmpl = OntologyTemplate(str(tmpl_path))
        ns = tmpl.namespaces
        required = ["schema", "health", "prov", "qudt", "fhir", "snomed", "loinc"]
        missing_ns = [n for n in required if n not in ns]
        if missing_ns:
            _warn("Namespace gaps", f"Missing: {missing_ns}")
        else:
            _pass("All required namespaces present", f"{len(ns)} total")
        t0 = time.perf_counter()
        df = pd.DataFrame([{"uuid": "test-001", "start_time": "1777632000000",
                             "end_time": "1777718340000", "time_offset": "60",
                             "sleep_duration": "440", "efficiency": "78",
                             "deep_sleep": "90", "rem_sleep": "110",
                             "light_sleep": "240", "wake_up_count": "0"}])
        g = graph_for_data_type(tmpl, "sleep", df, TransformOptions())
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        if len(g) > 0:
            _pass(f"Sleep graph: {len(g)} triples", f"{elapsed}ms")
        else:
            _fail("Sleep graph empty")
    except Exception as e:
        _fail("RDF transformer error", str(e))


def _test_hra_client():
    st.subheader("🧬 HRA Client (HuBMAP SPARQL)")
    try:
        from src.hra_client import get_organ_annotation, ORGAN_UBERON_MAP, _cache_path
        _pass("hra_client imported", f"{len(ORGAN_UBERON_MAP)} organs mapped")

        # Cache check
        heart_cache = _cache_path("asctb_UBERON_0000948")
        if heart_cache.exists():
            age_days = round((time.time() - heart_cache.stat().st_mtime) / 86400, 1)
            _pass("Heart annotation cached", f"{age_days}d old")
        else:
            _info("Heart annotation not cached", "Will fetch on first use (requires network)")

        # Live network probe (non-blocking)
        if st.checkbox("🌐 Live SPARQL probe (requires internet)", key="hra_live"):
            with st.spinner("Querying lod.humanatlas.io…"):
                try:
                    t0 = time.perf_counter()
                    ann = get_organ_annotation("UBERON:0000948", "Heart")
                    elapsed = round(time.perf_counter() - t0, 2)
                    if ann.cell_types or ann.biomarkers:
                        _pass(f"HRA heart query: {len(ann.cell_types)} cell types, {len(ann.biomarkers)} biomarkers", f"{elapsed}s")
                        st.code(ann.to_mesh_tooltip())
                    else:
                        _warn("HRA returned empty result", "Endpoint may be slow or rate-limited")
                except Exception as e:
                    _fail("HRA SPARQL failed", str(e))
    except Exception as e:
        _fail("hra_client import failed", str(e))


def _test_extensions():
    st.subheader("🧩 Extension Framework")
    try:
        from extensions import registry
        available = registry.available()
        _pass(f"Registry: {len(available)} extensions discovered")

        for ext in available:
            name = ext["name"]
            installed = ext["installed"]
            active = ext["active"]
            daemon = "🔌 daemon" if ext["requires_daemon"] else "⚡ in-process"
            size = f"{ext['download_size_mb']:.0f}MB" if ext["download_size_mb"] > 0 else "no download"
            status = "✅ installed" if installed else "⬇️ not installed"
            st.markdown(f"  - **{name}** ({daemon}, {size}) — {status}")
    except Exception as e:
        _fail("Extension registry error", str(e))
        return

    # SHACL validator test
    st.markdown("**SHACL Validator:**")
    try:
        from extensions.shacl_validator import ShaclValidatorExtension
        shacl = ShaclValidatorExtension()
        if shacl.is_available():
            shacl.load()
            # Valid sleep record — should pass
            good_ttl = """
@prefix fhir:   <http://hl7.org/fhir/> .
@prefix health: <https://health.example.org/ns#> .
<urn:test:sleep:1> a fhir:Observation ;
    health:sleepEfficiency 78 ;
    health:deepSleepMinutes 90 .
"""
            result = shacl.validate(good_ttl, "sleep")
            if result["conforms"]:
                _pass("SHACL sleep shape: valid record passes")
            else:
                _fail("SHACL sleep shape: false positive", str(result))

            # Invalid efficiency (150%) — should fail
            bad_ttl = good_ttl.replace("78", "150")
            result2 = shacl.validate(bad_ttl, "sleep")
            if not result2["conforms"]:
                _pass("SHACL sleep shape: invalid efficiency (150%) caught")
            else:
                _fail("SHACL sleep shape: missed invalid efficiency")
            shacl.teardown()
        else:
            _warn("pyshacl not installed", "Run: pip install pyshacl")
    except Exception as e:
        _fail("SHACL validator error", str(e))

    # N3 reasoner probe
    st.markdown("**N3 Reasoner (EYE):**")
    try:
        from extensions.n3_reasoner import N3ReasonerExtension
        n3 = N3ReasonerExtension()
        if n3.is_available():
            n3.load()
            if n3.health_check():
                _pass("EYE reasoner available and healthy")
                # Quick rule test
                data = """
@prefix health: <https://health.example.org/ns#> .
<urn:test:person:1> health:sleepHours 4 ;
                    health:restingHR 95 .
"""
                try:
                    out = n3.reason(data, rule_names=["adrenal_fatigue"])
                    if "AdrenalFatigueSuspected" in out:
                        _pass("N3 adrenal fatigue rule fired correctly")
                    else:
                        _warn("N3 rule output unexpected", out[:200])
                except Exception as e:
                    _fail("N3 reasoning error", str(e))
                n3.teardown()
            else:
                _warn("EYE binary unhealthy")
        else:
            _info("EYE not installed", "Call registry.activate('n3_reasoner') to download (~15MB)")
    except Exception as e:
        _fail("N3 reasoner error", str(e))


def _test_swipl_wasm():
    st.subheader("🦉 SWI-Prolog WASM (Phase 5 — Evaluation)")

    st.info(
        "SWI-Prolog WASM (`swipl-wasm`) is **not yet integrated** — this is the evaluation probe. "
        "It would enable N3Logic rules to run in-browser with no daemon."
    )

    # Check for system swipl
    swipl_path = None
    for candidate in ["swipl", "swipl.exe"]:
        import shutil
        p = shutil.which(candidate)
        if p:
            swipl_path = p
            break

    if swipl_path:
        try:
            result = subprocess.run(
                [swipl_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            version_line = result.stdout.strip().splitlines()[0] if result.stdout else "unknown"
            _pass("System SWI-Prolog found", f"{swipl_path} — {version_line}")
            _info("Next step", "Test `library(n3)` pack: swipl -g 'pack_install(n3)' -t halt")
        except Exception as e:
            _warn("SWI-Prolog found but failed to run", str(e))
    else:
        _warn("System SWI-Prolog not found", "Install from https://www.swi-prolog.org/download/stable")

    # Check for swipl-wasm build
    swipl_wasm_candidates = [
        _ROOT / "ui" / "static" / "swipl" / "swipl-web.wasm",
        _ROOT / "extensions" / "swi_prolog" / "swipl-web.wasm",
    ]
    found_wasm = next((p for p in swipl_wasm_candidates if p.exists()), None)
    if found_wasm:
        size_mb = round(found_wasm.stat().st_size / 1_048_576, 1)
        _pass("swipl-wasm binary found", f"{found_wasm} ({size_mb}MB)")
    else:
        _info("swipl-wasm not downloaded", "Source: https://github.com/SWI-Prolog/swipl-wasm")

    st.markdown("""
**Integration plan** (once evaluated):
1. Download `swipl-web.wasm` + `swipl-web.js` from swipl-wasm releases
2. Serve from `ui/static/swipl/`
3. Load in Three.js component: `await SWIPrologSession.create()`
4. Load N3 pack: `session.call('use_module(library(n3))')`
5. Assert health data as Prolog facts, run N3 rules in-browser
6. If viable → N3 reasoner moves from EYE daemon to in-browser WASM
""")


def _test_wasm_core_browser():
    """Embed an HTML component that loads wellfare_core WASM and runs JS-side tests."""
    st.subheader("⚙️ WASM Core (Browser-side)")

    wasm_exists = (_STATIC_PKG / "wellfare_core_bg.wasm").exists()
    if not wasm_exists:
        _fail("WASM package not found", "Build first: wasm-pack build --target web --out-dir ui/static/pkg")
        return

    # CSV test data
    sleep_csv = "uuid,start_time,end_time,time_offset,sleep_duration,efficiency,deep_sleep,rem_sleep,light_sleep,wake_up_count\\nb2000001-0000-4000-8000-000000000001,1777681200000,1777707600000,60,440,78,90,110,240,0"
    hr_csv = "uuid,start_time,time_offset,heart_rate,min,max,heart_rate_zone,binning_data\\nc3000001-0000-4000-8000-000000000001,1777668000000,60,68,58,120,rest,hr_bin_0.json"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: monospace; font-size: 13px; background: #0f172a; color: #e2e8f0; padding: 16px; margin: 0; }}
.pass {{ color: #4ade80; }} .fail {{ color: #f87171; }} .warn {{ color: #fbbf24; }}
.info {{ color: #60a5fa; }} .section {{ color: #a78bfa; font-weight: bold; margin-top: 12px; }}
pre {{ background: #1e293b; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 11px; }}
</style>
</head>
<body>
<div id="log"><span class="info">⏳ Loading WASM core…</span></div>
<script type="module">
const log = document.getElementById('log');
function append(cls, msg) {{
  log.innerHTML += '<br><span class="' + cls + '">' + msg + '</span>';
}}
function section(title) {{
  log.innerHTML += '<br><span class="section">── ' + title + ' ──</span>';
}}

try {{
  const {{ default: init,
    sleep_turtle_from_csv, parse_sleep_csv_json,
    heart_rate_turtle_from_csv, parse_heart_rate_csv_json,
    steps_turtle_from_csv, parse_steps_csv_json,
    weight_turtle_from_csv, parse_weight_csv_json,
    WasmHealthStore, validate_health_turtle
  }} = await import('/app/static/pkg/wellfare_core.js');

  await init();
  append('pass', '✅ WASM core loaded');

  // ── CSV Parsing ──────────────────────────────────────────────
  section('CSV Parsing');
  const sleepCsv = `{sleep_csv}`;
  const hrCsv = `{hr_csv}`;

  try {{
    const sleepRecords = parse_sleep_csv_json(sleepCsv);
    append('pass', '✅ Sleep CSV parsed: ' + JSON.stringify(sleepRecords[0].sleep_duration) + 'min, efficiency=' + sleepRecords[0].efficiency + '%');
  }} catch(e) {{ append('fail', '❌ Sleep CSV parse failed: ' + e); }}

  try {{
    const hrRecords = parse_heart_rate_csv_json(hrCsv);
    append('pass', '✅ Heart rate CSV parsed: ' + hrRecords[0].heart_rate + ' BPM');
  }} catch(e) {{ append('fail', '❌ Heart rate CSV parse failed: ' + e); }}

  // ── Turtle RDF Generation ────────────────────────────────────
  section('RDF / Turtle Generation');
  let sleepTtl = '';
  try {{
    sleepTtl = sleep_turtle_from_csv(sleepCsv);
    const hasEfficiency = sleepTtl.includes('sleepEfficiency');
    const hasProv = sleepTtl.includes('prov:wasDerivedFrom');
    const hasHRA = sleepTtl.includes('fhir:') && sleepTtl.includes('health:');
    const hasCCF = sleepTtl.includes('@prefix ccf:') || sleepTtl.includes('@prefix uberon:');
    append(hasEfficiency ? 'pass' : 'fail', (hasEfficiency ? '✅' : '❌') + ' Sleep Turtle: sleepEfficiency triple');
    append(hasProv ? 'pass' : 'fail', (hasProv ? '✅' : '❌') + ' Sleep Turtle: PROV-O provenance');
    append(hasHRA ? 'pass' : 'fail', (hasHRA ? '✅' : '❌') + ' Sleep Turtle: FHIR + health namespaces');
    append(hasCCF ? 'pass' : 'fail', (hasCCF ? '✅' : '❌') + ' Sleep Turtle: HRA/CCF/UBERON namespaces');
  }} catch(e) {{ append('fail', '❌ Turtle generation failed: ' + e); }}

  let hrTtl = '';
  try {{
    hrTtl = heart_rate_turtle_from_csv(hrCsv);
    const hasHR = hrTtl.includes('364075005'); // SNOMED heart rate
    append(hasHR ? 'pass' : 'fail', (hasHR ? '✅' : '❌') + ' Heart rate Turtle: SNOMED concept');
  }} catch(e) {{ append('fail', '❌ HR Turtle failed: ' + e); }}

  // ── WASM Health Store (oxigraph SPARQL) ──────────────────────
  section('oxigraph SPARQL Store');
  try {{
    const store = new WasmHealthStore();
    store.load_turtle(sleepTtl);
    const result = store.query('SELECT ?s WHERE {{ ?s a <http://hl7.org/fhir/Observation> }}');
    const parsed = JSON.parse(result);
    const rows = parsed?.results?.bindings?.length ?? 0;
    append(rows > 0 ? 'pass' : 'fail', (rows > 0 ? '✅' : '❌') + ' SPARQL SELECT: ' + rows + ' observation(s) found');

    // ASK query
    const askResult = store.query('ASK {{ ?s <https://health.example.org/ns#sleepEfficiency> ?e }}');
    const isTrue = JSON.parse(askResult).boolean === true;
    append(isTrue ? 'pass' : 'fail', (isTrue ? '✅' : '❌') + ' SPARQL ASK: sleepEfficiency exists');
  }} catch(e) {{ append('fail', '❌ SPARQL store error: ' + e); }}

  // ── SHACL-via-SPARQL Validation ──────────────────────────────
  section('SHACL-via-SPARQL Shapes');
  try {{
    const validSleep = '@prefix fhir: <http://hl7.org/fhir/> . @prefix health: <https://health.example.org/ns#> . <urn:t:1> a fhir:Observation ; health:sleepEfficiency 78 .';
    const validResult = JSON.parse(validate_health_turtle(validSleep));
    append(validResult.valid ? 'pass' : 'fail', (validResult.valid ? '✅' : '❌') + ' Valid sleep record passes (' + validResult.checked + ' shapes checked)');

    const invalidSleep = '@prefix fhir: <http://hl7.org/fhir/> . @prefix health: <https://health.example.org/ns#> . <urn:t:2> a fhir:Observation ; health:sleepEfficiency 150 .';
    const invalidResult = JSON.parse(validate_health_turtle(invalidSleep));
    const caught = invalidResult.violations.some(v => v.shape === 'sleep:efficiency-range');
    append(caught ? 'pass' : 'fail', (caught ? '✅' : '❌') + ' Invalid efficiency (150%) caught by shape');

    const invalidHR = '@prefix fhir: <http://hl7.org/fhir/> . @prefix snomed: <http://snomed.info/id/> . <urn:t:3> a fhir:Observation ; fhir:Observation.valueQuantity 350 ; health:snomedConcept snomed:364075005 .';
    const hrResult = JSON.parse(validate_health_turtle(invalidHR));
    append('info', 'ℹ️ HR out-of-range (350 BPM): ' + hrResult.violations.length + ' violation(s)');

  }} catch(e) {{ append('fail', '❌ SHACL validation error: ' + e); }}

  // ── swipl-wasm probe ─────────────────────────────────────────
  section('SWI-Prolog WASM (evaluation probe)');
  try {{
    const resp = await fetch('/app/static/swipl/swipl-web.wasm', {{ method: 'HEAD' }});
    if (resp.ok) {{
      append('pass', '✅ swipl-wasm binary found at /app/static/swipl/');
    }} else {{
      append('warn', '⚠️ swipl-wasm not deployed (HTTP ' + resp.status + ') — not yet integrated');
    }}
  }} catch(e) {{
    append('warn', '⚠️ swipl-wasm not found — Phase 5 pending');
  }}

  append('info', '');
  append('pass', '✅ Browser-side test suite complete');

}} catch(e) {{
  append('fail', '❌ Fatal WASM load error: ' + e);
  log.innerHTML += '<pre>' + e.stack + '</pre>';
}}
</script>
</body>
</html>"""

    st.components.v1.html(html, height=520, scrolling=True)


# ── Main render ────────────────────────────────────────────────────────────────

def render_dev_tools(dark_mode: bool = False):
    st.title("🔧 Developer Tools & Test Suite")
    st.caption("v0.0.3-dev — internal test runner for WASM core, semantic pipeline, and extensions")

    st.info(
        "**SWI-Prolog WASM status:** Not yet integrated (Phase 5). "
        "The EYE reasoner extension handles N3Logic server-side. "
        "swipl-wasm evaluation probe is included below.",
        icon="🦉"
    )

    tabs = st.tabs([
        "⚙️ WASM Core",
        "🔗 RDF Pipeline",
        "🧬 HRA Client",
        "🧩 Extensions",
        "🦉 SWI-Prolog",
        "📦 Assets",
    ])

    with tabs[0]:
        _test_wasm_core_browser()

    with tabs[1]:
        _test_rdf_transformer()

    with tabs[2]:
        _test_hra_client()

    with tabs[3]:
        _test_extensions()

    with tabs[4]:
        _test_swipl_wasm()

    with tabs[5]:
        _test_static_assets()

    st.divider()
    st.markdown("""
**What's tested:**
| Suite | Method | Status |
|---|---|---|
| WASM CSV parsing | Browser JS | ✅ Implemented |
| WASM Turtle RDF | Browser JS | ✅ Implemented |
| WASM SPARQL (oxigraph) | Browser JS | ✅ Implemented |
| WASM SHACL-via-SPARQL | Browser JS | ✅ Implemented |
| Python RDF transformer | Streamlit process | ✅ Implemented |
| HRA SPARQL client | Streamlit process | ✅ Implemented |
| SHACL validator (pyshacl) | Extension | ✅ Implemented |
| N3 reasoner (EYE) | Extension daemon | ✅ Implemented |
| SWI-Prolog WASM | Browser JS | 🔲 Phase 5 — pending |
| Local LLM (Ollama) | Extension daemon | 🔲 Requires Ollama |
""")

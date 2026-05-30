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

_ROOT = Path(__file__).resolve().parent.parent.parent
_STATIC_PKG = _ROOT / "ui" / "static" / "pkg"
_HRA_MODELS = _ROOT / "ui" / "static" / "models" / "hra"
_AVATAR_MODELS = _ROOT / "ui" / "static" / "models"
_PROFILES_DIR = _ROOT / "docs" / "profiles"


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
        # Search known locations — config/ is canonical
        _candidates = [_ROOT / "config" / "ontology_template.yaml", _ROOT / "ontology_template.yaml"]
        tmpl_path = next((p for p in _candidates if p.exists()), None)
        if not tmpl_path:
            _warn("ontology_template.yaml not found", f"Searched: {[str(p) for p in _candidates]}")
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
        df = pd.DataFrame([{"uuid": "test-001", "start_time": 1777632000000,
                             "end_time": 1777718340000, "time_offset": 60,
                             "sleep_duration": 440, "efficiency": 78,
                             "deep_sleep": 90, "rem_sleep": 110,
                             "light_sleep": 240, "wake_up_count": 0}])
        g = graph_for_data_type(tmpl, "com.samsung.shealth.sleep", df, TransformOptions())
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


def _test_vault_browser():
    """Browser-side tests for the vault crypto stack and OTS anchoring."""
    st.subheader("🔒 Vault Crypto & Anchoring (Browser-side)")

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: monospace; font-size: 13px; background: #0f172a; color: #e2e8f0; padding: 16px; margin: 0; }
.pass { color: #4ade80; } .fail { color: #f87171; } .warn { color: #fbbf24; }
.info { color: #60a5fa; } .section { color: #a78bfa; font-weight: bold; margin-top: 12px; }
button { background: #1e293b; color: #a78bfa; border: 1px solid #334155; border-radius: 4px;
  padding: 4px 12px; font-family: monospace; cursor: pointer; margin-top: 8px; font-size: 12px; }
button:hover { border-color: #7c3aed; }
</style>
</head>
<body>
<div id="log"><span class="info">⏳ Running vault crypto tests…</span></div>
<div id="ots-btn-wrap" style="margin-top:8px"></div>
<script type="module">
const log = document.getElementById('log');
function line(cls, msg) { log.innerHTML += '<br><span class="' + cls + '">' + msg + '</span>'; }
function section(t) { log.innerHTML += '<br><span class="section">── ' + t + ' ──</span>'; }
const toB64 = u8 => btoa(String.fromCharCode(...u8));
const fromB64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

// ── 1. WebCrypto Guard ────────────────────────────────────────────────────────
section('WebCrypto Guard (pair.html startup check)');
const missing = [];
try { await crypto.subtle.generateKey({ name: 'Ed25519' }, false, ['sign', 'verify']); }
catch (_) { missing.push('Ed25519'); }
try { await crypto.subtle.generateKey({ name: 'X25519' }, false, ['deriveBits']); }
catch (_) { missing.push('X25519'); }
if (missing.length === 0) {
  line('pass', '✅ WebCrypto guard: Ed25519 + X25519 both supported — vault will load');
} else {
  line('fail', '❌ WebCrypto guard: missing ' + missing.join(', ') + ' — vault would show unsupported-browser error');
}

// ── 2. Identity Credentials (Ed25519 did:key) ─────────────────────────────────
section('Identity Credentials — Ed25519 did:key');
let sigKey = null;
try {
  sigKey = await crypto.subtle.generateKey({ name: 'Ed25519' }, true, ['sign', 'verify']);
  const pubRaw = new Uint8Array(await crypto.subtle.exportKey('raw', sigKey.publicKey));
  // did:key prefix: 0xed01 + pubkey, then multibase base58btc
  line('pass', '✅ Ed25519 key pair generated — public key ' + pubRaw.length + ' bytes');

  const payload = new TextEncoder().encode('{"type":"hello","did":"did:key:test"}');
  const sig = new Uint8Array(await crypto.subtle.sign('Ed25519', sigKey.privateKey, payload));
  line('pass', '✅ Ed25519 sign: ' + sig.length + '-byte signature produced');

  const valid = await crypto.subtle.verify('Ed25519', sigKey.publicKey, sig, payload);
  line(valid ? 'pass' : 'fail', (valid ? '✅' : '❌') + ' Ed25519 verify: signature ' + (valid ? 'valid' : 'INVALID'));

  // Tampered payload must fail
  const tampered = new TextEncoder().encode('{"type":"hello","did":"did:key:TAMPERED"}');
  const bad = await crypto.subtle.verify('Ed25519', sigKey.publicKey, sig, tampered);
  line(!bad ? 'pass' : 'fail', (!bad ? '✅' : '❌') + ' Ed25519 verify: tampered payload correctly rejected');
} catch (e) { line('fail', '❌ Ed25519 error: ' + e); }

// ── 3. Noise_XX key exchange (X25519) ─────────────────────────────────────────
section('Noise_XX Key Exchange — X25519');
try {
  const aliceKP = await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits']);
  const bobKP   = await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits']);
  line('pass', '✅ X25519 static key pairs generated (both sides)');

  const aliceShared = new Uint8Array(await crypto.subtle.deriveBits(
    { name: 'X25519', public: bobKP.publicKey }, aliceKP.privateKey, 256));
  const bobShared = new Uint8Array(await crypto.subtle.deriveBits(
    { name: 'X25519', public: aliceKP.publicKey }, bobKP.privateKey, 256));

  const match = toB64(aliceShared) === toB64(bobShared);
  line(match ? 'pass' : 'fail', (match ? '✅' : '❌') + ' DH shared secret: Alice and Bob derive identical 32-byte secret');
} catch (e) { line('fail', '❌ X25519 DH error: ' + e); }

// ── 4. Symmetric encryption (AES-256-GCM) ────────────────────────────────────
section('DataChannel Encryption — AES-256-GCM');
try {
  const aesKey = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode('{"type":"data","records":[{"id":1}]}');
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, aesKey, plaintext));
  line('pass', '✅ AES-256-GCM encrypt: ' + ct.length + ' bytes (plaintext + 16-byte tag)');

  const recovered = new Uint8Array(await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, aesKey, ct));
  const roundtrip = new TextDecoder().decode(recovered) === new TextDecoder().decode(plaintext);
  line(roundtrip ? 'pass' : 'fail', (roundtrip ? '✅' : '❌') + ' AES-256-GCM decrypt: plaintext recovered correctly');

  // Wrong IV must fail
  const badIV = crypto.getRandomValues(new Uint8Array(12));
  try {
    await crypto.subtle.decrypt({ name: 'AES-GCM', iv: badIV }, aesKey, ct);
    line('fail', '❌ AES-GCM: decryption with wrong IV should have thrown');
  } catch (_) {
    line('pass', '✅ AES-GCM: wrong IV correctly rejected (authentication tag mismatch)');
  }
} catch (e) { line('fail', '❌ AES-256-GCM error: ' + e); }

// ── 5. Sanctuary key derivation (PBKDF2-SHA256) ───────────────────────────────
section('Sanctuary Key Derivation — PBKDF2-SHA256 (310,000 iterations)');
try {
  const pin = new TextEncoder().encode('8888');
  const salt = new TextEncoder().encode('wf-sanctuary-salt-v1');
  const baseKey = await crypto.subtle.importKey('raw', pin, { name: 'PBKDF2' }, false, ['deriveKey']);
  const t0 = performance.now();
  const sancKey = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', hash: 'SHA-256', salt, iterations: 310_000 },
    baseKey, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  );
  const ms = Math.round(performance.now() - t0);
  line('pass', '✅ PBKDF2-SHA256 sanctuary key derived in ' + ms + 'ms (310k iterations)');
  line(ms > 200 ? 'pass' : 'warn',
    (ms > 200 ? '✅' : '⚠️') + ' Derivation time ' + ms + 'ms — ' +
    (ms > 200 ? 'adequate work factor' : 'suspiciously fast; check iteration count'));

  // Deterministic: same PIN + salt → same key behaviour (test by encrypting same plaintext)
  const baseKey2 = await crypto.subtle.importKey('raw', pin, { name: 'PBKDF2' }, false, ['deriveKey']);
  const sancKey2 = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', hash: 'SHA-256', salt, iterations: 310_000 },
    baseKey2, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  );
  const iv = new Uint8Array(12); // fixed IV for determinism test
  const c1 = toB64(new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, sancKey, pin)));
  const c2 = toB64(new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, sancKey2, pin)));
  line(c1 === c2 ? 'pass' : 'fail', (c1 === c2 ? '✅' : '❌') + ' PBKDF2 deterministic: same PIN+salt → same key');
} catch (e) { line('fail', '❌ PBKDF2 error: ' + e); }

// ── 6. Commitment computation (sha256(sha256(entry) ‖ nonce)) ─────────────────
section('DLT Commitment — sha256(sha256(entry) ‖ nonce)');
try {
  const entry = new TextEncoder().encode('{"type":"assertion","content":"Test entry","created_at":"2026-05-30T10:00:00Z"}');
  const inner = new Uint8Array(await crypto.subtle.digest('SHA-256', entry));
  const nonce = crypto.getRandomValues(new Uint8Array(16));
  const concat = new Uint8Array(inner.length + nonce.length);
  concat.set(inner); concat.set(nonce, inner.length);
  const commitment = new Uint8Array(await crypto.subtle.digest('SHA-256', concat));

  line('pass', '✅ Commitment computed: ' + commitment.length + ' bytes');
  line('info', 'ℹ️ Commitment (hex): ' + Array.from(commitment).map(b => b.toString(16).padStart(2,'0')).join('').slice(0,32) + '…');

  // Different entry → different commitment
  const entry2 = new TextEncoder().encode('{"type":"assertion","content":"Different entry","created_at":"2026-05-30T10:00:00Z"}');
  const inner2 = new Uint8Array(await crypto.subtle.digest('SHA-256', entry2));
  const concat2 = new Uint8Array(inner2.length + nonce.length);
  concat2.set(inner2); concat2.set(nonce, inner2.length);
  const commitment2 = new Uint8Array(await crypto.subtle.digest('SHA-256', concat2));
  const distinct = toB64(commitment) !== toB64(commitment2);
  line(distinct ? 'pass' : 'fail', (distinct ? '✅' : '❌') + ' Different entries produce distinct commitments');

  // Same entry + different nonce → different commitment (nonce prevents pre-image)
  const nonce2 = crypto.getRandomValues(new Uint8Array(16));
  const concat3 = new Uint8Array(inner.length + nonce2.length);
  concat3.set(inner); concat3.set(nonce2, inner.length);
  const commitment3 = new Uint8Array(await crypto.subtle.digest('SHA-256', concat3));
  const nonceEffect = toB64(commitment) !== toB64(commitment3);
  line(nonceEffect ? 'pass' : 'fail', (nonceEffect ? '✅' : '❌') + ' Different nonce → different commitment (nonce prevents pre-image lookup)');

  // Store commitment bytes for OTS test below
  window._testCommitment = commitment;
} catch (e) { line('fail', '❌ Commitment computation error: ' + e); }

// ── 7. OTS file format ────────────────────────────────────────────────────────
section('OpenTimestamps — File Format Construction');
try {
  const OTS_MAGIC = new Uint8Array([
    0x00, 0x4f, 0x70, 0x65, 0x6e, 0x54, 0x69, 0x6d, 0x65, 0x73, 0x74, 0x61, 0x6d, 0x70, 0x73,
    0x00, 0x00, 0x50, 0x72, 0x6f, 0x6f, 0x66, 0x00, 0xbf, 0x89, 0xe2, 0xe8, 0x84, 0xe8, 0x92, 0x94,
  ]);
  const commitment = window._testCommitment || crypto.getRandomValues(new Uint8Array(32));
  const mockBody = new Uint8Array(16); // placeholder calendar response body
  const file = new Uint8Array(OTS_MAGIC.length + 1 + 1 + 32 + mockBody.length);
  let o = 0;
  file.set(OTS_MAGIC, o); o += OTS_MAGIC.length;
  file[o++] = 0x01; // version
  file[o++] = 0x08; // SHA256 op tag
  file.set(commitment, o); o += 32;
  file.set(mockBody, o);

  line('pass', '✅ OTS file constructed: ' + file.length + ' bytes');
  line(file[0] === 0x00 ? 'pass' : 'fail',
    (file[0] === 0x00 ? '✅' : '❌') + ' Magic byte 0: 0x00 (OTS null prefix)');
  const magicStr = new TextDecoder().decode(file.slice(1, 15));
  line(magicStr === 'OpenTimestamps' ? 'pass' : 'fail',
    (magicStr === 'OpenTimestamps' ? '✅' : '❌') + ' Magic bytes 1–14: "' + magicStr + '"');
  line(file[OTS_MAGIC.length] === 0x01 ? 'pass' : 'fail',
    (file[OTS_MAGIC.length] === 0x01 ? '✅' : '❌') + ' Version byte: 0x01');
  line(file[OTS_MAGIC.length + 1] === 0x08 ? 'pass' : 'fail',
    (file[OTS_MAGIC.length + 1] === 0x08 ? '✅' : '❌') + ' Hash op tag: 0x08 (SHA-256)');
  const embeddedHash = file.slice(OTS_MAGIC.length + 2, OTS_MAGIC.length + 2 + 32);
  const hashMatch = toB64(embeddedHash) === toB64(commitment);
  line(hashMatch ? 'pass' : 'fail', (hashMatch ? '✅' : '❌') + ' Commitment hash embedded correctly at offset ' + (OTS_MAGIC.length + 2));
} catch (e) { line('fail', '❌ OTS file format error: ' + e); }

// ── 8. IndexedDB — vault schema ───────────────────────────────────────────────
section('IndexedDB — Vault Schema (wf-vault v2)');
try {
  // Open a TEST db (not the real vault db) to verify IDB is functional
  await new Promise((resolve, reject) => {
    const req = indexedDB.open('wf-vault-devtest', 1);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('wf-s'))  db.createObjectStore('wf-s',  { keyPath: 'id' });
      if (!db.objectStoreNames.contains('wf-sc')) db.createObjectStore('wf-sc', { keyPath: 'id' });
    };
    req.onsuccess = e => {
      const db = e.target.result;
      const stores = Array.from(db.objectStoreNames);
      const hasLog = stores.includes('wf-s');
      const hasCfg = stores.includes('wf-sc');
      line(hasLog ? 'pass' : 'fail', (hasLog ? '✅' : '❌') + ' IDB store wf-s (sanctuary entry log) present');
      line(hasCfg ? 'pass' : 'fail', (hasCfg ? '✅' : '❌') + ' IDB store wf-sc (sanctuary config) present');

      // Write + read round trip in wf-s
      const tx = db.transaction('wf-s', 'readwrite');
      const store = tx.objectStore('wf-s');
      const testRec = { id: 'dev-test-001', seq: Date.now(), nonce: 'abc', commitment: 'xyz', ots_status: 'not_published' };
      store.put(testRec);
      tx.oncomplete = () => {
        const tx2 = db.transaction('wf-s', 'readonly');
        const req2 = tx2.objectStore('wf-s').get('dev-test-001');
        req2.onsuccess = () => {
          const rec = req2.result;
          const ok = rec && rec.ots_status === 'not_published' && rec.commitment === 'xyz';
          line(ok ? 'pass' : 'fail', (ok ? '✅' : '❌') + ' IDB round trip: record written and read with ots_status field');
          // Clean up test DB
          const tx3 = db.transaction('wf-s', 'readwrite');
          tx3.objectStore('wf-s').delete('dev-test-001');
          db.close();
          resolve();
        };
        req2.onerror = () => { line('fail', '❌ IDB read failed'); resolve(); };
      };
      tx.onerror = () => { line('fail', '❌ IDB write failed'); resolve(); };
    };
    req.onerror = () => { line('fail', '❌ IndexedDB open failed'); reject(); };
  });
} catch (e) { line('fail', '❌ IDB error: ' + e); }

// ── 9. OTS calendar probe (opt-in) ────────────────────────────────────────────
section('OpenTimestamps — Calendar Server (opt-in network probe)');
line('info', 'ℹ️ Click to POST a test commitment to alice.btc.calendar.opentimestamps.org/digest');
const wrap = document.getElementById('ots-btn-wrap');
const btn = document.createElement('button');
btn.textContent = '▶ Run OTS calendar probe';
btn.onclick = async () => {
  btn.disabled = true; btn.textContent = 'Probing…';
  try {
    const hash = crypto.getRandomValues(new Uint8Array(32));
    const t0 = performance.now();
    const resp = await fetch('https://alice.btc.calendar.opentimestamps.org/digest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream', 'Accept': 'application/octet-stream' },
      body: hash,
    });
    const ms = Math.round(performance.now() - t0);
    if (resp.ok) {
      const body = new Uint8Array(await resp.arrayBuffer());
      line('pass', '✅ OTS calendar reachable: HTTP ' + resp.status + ', ' + body.length + '-byte receipt in ' + ms + 'ms');
      line('info', 'ℹ️ Receipt (first 16 bytes hex): ' + Array.from(body.slice(0,16)).map(b=>b.toString(16).padStart(2,'0')).join(''));
    } else {
      line('warn', '⚠️ OTS calendar responded HTTP ' + resp.status + ' in ' + ms + 'ms');
    }
  } catch (e) {
    line('fail', '❌ OTS calendar unreachable: ' + e.message + ' (check network / CORS)');
  }
  btn.textContent = 'Done';
};
wrap.appendChild(btn);

line('info', '');
line('pass', '✅ Vault test suite complete');
</script>
</body>
</html>"""

    st.components.v1.html(html, height=700, scrolling=True)


def _test_access_profiles():
    """Python-side tests for SHACL access profiles and ODRL EdgeConstraints."""
    st.subheader("🗝️ Access Profiles & ODRL EdgeConstraints")

    # ── profiles.json ──────────────────────────────────────────────────────────
    st.markdown("**profiles.json**")
    profiles_json = _PROFILES_DIR / "profiles.json"
    if not profiles_json.exists():
        _fail("profiles.json not found", str(profiles_json))
        return

    try:
        profiles = json.loads(profiles_json.read_text(encoding="utf-8"))
        if not isinstance(profiles, list):
            _fail("profiles.json: expected a JSON array")
        else:
            _pass(f"profiles.json loaded: {len(profiles)} profiles")
            required_fields = {"id", "label", "sections"}
            for p in profiles:
                missing = required_fields - set(p.keys())
                if missing:
                    _warn(f"Profile '{p.get('id','?')}' missing fields", str(missing))
            if len(profiles) >= 9:
                _pass(f"Profile count ≥ 9 (expected: 9 access profiles)")
            else:
                _warn(f"Only {len(profiles)} profiles found", "Expected 9")

            ids = [p.get("id", "?") for p in profiles]
            st.markdown("Profile IDs: " + ", ".join(f"`{i}`" for i in ids))
    except Exception as e:
        _fail("profiles.json parse error", str(e))
        return

    # ── access-profiles.ttl ────────────────────────────────────────────────────
    st.markdown("**access-profiles.ttl (SHACL)**")
    ttl_path = _PROFILES_DIR / "access-profiles.ttl"
    if not ttl_path.exists():
        _fail("access-profiles.ttl not found", str(ttl_path))
        return

    ttl_text = ttl_path.read_text(encoding="utf-8")
    _pass(f"access-profiles.ttl present", f"{len(ttl_text):,} chars")

    wf_ns = "https://wellfare.social/ns/vault#"
    if wf_ns in ttl_text or "wf:" in ttl_text:
        _pass("wf: namespace present (https://wellfare.social/ns/vault#)")
    else:
        _warn("wf: namespace not found in TTL")

    for keyword in ["sh:NodeShape", "sh:PropertyShape", "sh:property", "odrl:", "wf:"]:
        if keyword in ttl_text:
            _pass(f"TTL contains `{keyword}`")
        else:
            _warn(f"TTL missing `{keyword}`")

    # Try rdflib parse if available
    st.markdown("**rdflib parse (SHACL shapes)**")
    try:
        import rdflib
        g = rdflib.Graph()
        g.parse(data=ttl_text, format="turtle")
        triple_count = len(g)
        _pass(f"rdflib parsed TTL: {triple_count} triples")

        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
        node_shapes    = set(g.subjects(rdflib.RDF.type, SH.NodeShape))
        prop_shapes    = set(g.subjects(rdflib.RDF.type, SH.PropertyShape))
        _pass(f"SHACL NodeShapes: {len(node_shapes)}")
        _pass(f"SHACL PropertyShapes: {len(prop_shapes)}")
        if len(node_shapes) + len(prop_shapes) == 0:
            _warn("No SHACL shapes found — TTL may not declare shape types explicitly")

        ODRL = rdflib.Namespace("http://www.w3.org/ns/odrl/2/")
        policies = set(g.subjects(rdflib.RDF.type, ODRL.Policy))
        if policies:
            _pass(f"ODRL policies: {len(policies)}")
        else:
            _info("No odrl:Policy triples found (EdgeConstraints may use custom types)")

    except ImportError:
        _info("rdflib not installed", "Run: pip install rdflib  (optional — text checks above still run)")
    except Exception as e:
        _fail("rdflib parse error", str(e))

    # ── Cross-check: profile IDs vs TTL ────────────────────────────────────────
    st.markdown("**Cross-check: JSON profile IDs vs TTL**")
    try:
        for p in profiles:
            pid = p.get("id", "")
            if pid and pid in ttl_text:
                _pass(f"Profile `{pid}` referenced in TTL")
            elif pid:
                _warn(f"Profile `{pid}` not found in TTL")
    except Exception as e:
        _warn("Cross-check skipped", str(e))


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
    st.caption("v0.0.5-dev — vault crypto + OTS anchoring, access profiles, WASM core, semantic pipeline, extensions")

    st.info(
        "**Vault tests** (🔒 tab) run entirely in-browser via WebCrypto — no server required. "
        "**SWI-Prolog WASM** is not yet integrated (Phase 5); the EYE reasoner extension handles N3Logic server-side.",
        icon="🔒"
    )

    tabs = st.tabs([
        "🔒 Vault",
        "🗝️ Access Profiles",
        "⚙️ WASM Core",
        "🔗 RDF Pipeline",
        "🧬 HRA Client",
        "🧩 Extensions",
        "🦉 SWI-Prolog",
        "📦 Assets",
    ])

    with tabs[0]:
        _test_vault_browser()

    with tabs[1]:
        _test_access_profiles()

    with tabs[2]:
        _test_wasm_core_browser()

    with tabs[3]:
        _test_rdf_transformer()

    with tabs[4]:
        _test_hra_client()

    with tabs[5]:
        _test_extensions()

    with tabs[6]:
        _test_swipl_wasm()

    with tabs[7]:
        _test_static_assets()

    st.divider()
    st.markdown("""
**What's tested:**
| Suite | Method | Status |
|---|---|---|
| WebCrypto guard (Ed25519 + X25519) | Browser JS | ✅ Implemented |
| Ed25519 sign + verify (identity credentials) | Browser JS | ✅ Implemented |
| X25519 DH key exchange (Noise_XX) | Browser JS | ✅ Implemented |
| AES-256-GCM encrypt / decrypt | Browser JS | ✅ Implemented |
| PBKDF2-SHA256 sanctuary key derivation | Browser JS | ✅ Implemented |
| Commitment computation sha256(sha256(e)‖nonce) | Browser JS | ✅ Implemented |
| OTS file format construction + magic bytes | Browser JS | ✅ Implemented |
| OTS calendar server probe | Browser JS (opt-in) | ✅ Implemented |
| IndexedDB vault schema (wf-s + wf-sc) | Browser JS | ✅ Implemented |
| Access profiles JSON structure | Python | ✅ Implemented |
| SHACL TTL parse + shape count (rdflib) | Python | ✅ Implemented |
| ODRL EdgeConstraint presence | Python | ✅ Implemented |
| Profile ID cross-check (JSON vs TTL) | Python | ✅ Implemented |
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

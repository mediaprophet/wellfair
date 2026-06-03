# WellFair — New Session Handover (2026-05-30, session 3)

## What this project is

Privacy-first personal health vault. Phone is the authoritative vault; desktop is a
stateless terminal. All live data flows over an end-to-end-encrypted WebRTC DataChannel
(Noise_XX + AES-256-GCM). Nothing persists on the desktop — closing the tab destroys
everything.

**Mandatory terminology** — always use "identity credentials" (not DIDs, not VCs). Use
SHACL/RDFS shapes for data about people; OWL only for policy artefacts. Health namespace:
`wf:` → `https://wellfare.social/ns/vault#`.

Read `CLAUDE.md` and `instructions/VAULT_CONNECTOR_NEXT_STEPS.md` in full before writing
any code. Architecture decisions are locked.

---

## Current state: branch release/v0.0.5, fully committed and pushed

**Branch:** `release/v0.0.5` — pushed to origin, clean working tree  
**Version:** v0.0.5-dev  
**Untracked remaining:** `expert-authoring-tool/`, `user-runtime-lib/` (separate work stream, not yet assessed)

### All commits on this branch

1. **M6 code-complete + v0.0.5-dev bump** — Firefox WebCrypto guard, OTS Bitcoin anchoring,
   README rewrite, CLAUDE.md updated, vault files first-time committed (pair.html, connector,
   profiles, shared-schemas)

2. **Vault dev tools test suite** — `ui/tabs/dev_tools.py`: new 🔒 Vault tab (9 browser-side
   crypto tests) + 🗝️ Access Profiles tab (Python-side TTL/JSON validation); caption bumped
   to v0.0.5-dev

3. **Package manager + recompiled app.html** — browser-level optional package system for the
   Streamlit/WASM layer; `docs/app.html` fully recompiled (63.3 MB; all 30 critical modules
   + new packages_tab + dev_tools vault tests all bundled)

---

## Vault layer — what's complete, what remains

### Code-complete (no further code tasks)

- QR WebRTC pairing, Gun signalling, 9 SHACL access profiles + ODRL EdgeConstraints
- Noise_XX_25519_AESGCM_SHA256 encrypted DataChannel
- Ed25519 did:key identity credentials (both sides), response signing + verification
- Sanctuary Mode: PBKDF2-SHA256 key derivation (310k iter), encrypted IDB (wf-vault v2),
  duress decoy, Unvarnished Log, Contingency Protocols
- Tripwire Dashboard, Synthesis Engine, Evidentiary Export (VP + commitment manifest)
- Bitcoin anchoring via OpenTimestamps (feeless, anonymous, per-entry pending/confirmed)
- Browser compatibility guard (Ed25519 + X25519 WebCrypto feature detection)
- PWA manifest, Wake Lock API, relay unreachable timeout, Gun post-handshake cleanup
- Dead Man's Switch + anonymous Nym notifications (scaffolded, activation pending)

### Remaining — runtime/device only, no code tasks

| Task | What's needed |
|------|---------------|
| **Nym Sandbox validation** | Run `docs/nym-test.html` against `https://sandbox-nym-api1.nymtech.net/api`; confirm cold-start time; set `NYM_SDK_URL` constant in `pair.html` |
| **Real-device testing** | iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md` |
| **SURB stress test** | Airplane-mode toggle while Nym active; verify fragment reassembly + SURB replenishment |

---

## Streamlit/WASM layer — current state

`docs/app.html` is the compiled Stlite bundle (63.3 MB). It is rebuilt by running:

```bash
python scripts/build_stlite.py
```

GitHub warns about the file size (>50 MB recommended). If the bundle grows further, consider
Git LFS for `docs/app.html`.

### Package manager (new this session)

A browser-level optional package system was added. It gates advanced capabilities
(LLM inference, Prolog WASM reasoning) behind installable packages, so the base PWA
stays lean.

| File | Purpose |
|------|---------|
| `docs/packages/index.js` | Package system entry point |
| `docs/packages/package-manager.js` | Download + install orchestration |
| `docs/packages/capabilities.js` | Capability token registry |
| `docs/packages/registry.json` | Package metadata |
| `docs/packages/pkg-llm-mediapipe.js` | LLM/MediaPipe package descriptor |
| `docs/packages/pkg-prolog-wasm.js` | SWI-Prolog WASM package descriptor |
| `docs/package-download-ui.js` | Install overlay UI for the PWA |
| `ui/utils/package_bridge.py` | Pyodide/desktop bridge — reads `window.wellfairPackageState`; all caps available in desktop mode |
| `ui/tabs/packages_tab.py` | Packages tab UI |

Navigation sections whose capability requirements aren't met are shown locked/dimmed in the
sidebar (via `is_nav_section_available()` in `package_bridge.py`).

### Anatomy 3D mesh naming

All Three.js mesh objects in `ui/tabs/anatomy_3d.py` now have `.name` attributes
(`proc_heart`, `proc_brain`, `proc_lung_l/r`, `proc_retina_l/r`, etc.) for semantic
resolver lookup. Invisible retina meshes were added for diabetic retinopathy targeting.

---

## Key files

```
docs/
  pair.html              Phone vault — all vault logic
  connector/index.html   Desktop terminal — stateless
  nym-test.html          Nym SDK validation harness
  manifest.webmanifest   PWA manifest
  app.html               Compiled Stlite WASM bundle (63.3 MB — rebuild with build_stlite.py)
  packages/              Browser package manager
  package-download-ui.js Install overlay UI
  profiles/
    access-profiles.ttl  SHACL access profiles (canonical)
    profiles.json        JS-loadable registry

ui/
  app.py                 Streamlit entry point
  tabs/dev_tools.py      Dev Tools (8 tabs, 23 test suites incl. vault crypto + OTS)
  tabs/packages_tab.py   Packages tab
  utils/package_bridge.py Pyodide capability bridge
  tabs/anatomy_3d.py     3D anatomy (meshes now named for semantic resolver)

scripts/build_stlite.py  Stlite compiler (fixed Windows emoji crash on line 155)

instructions/
  VAULT_CONNECTOR_NEXT_STEPS.md   Full milestone checklist
  BROWSER_COMPAT.md               Real-device test matrix
  SESSION_HANDOVER_2026-05-30-v2.md  Prior handover (session 2)
```

## Dev server

```bash
# Vault (phone + desktop)
python -m http.server 3000 --directory docs

# Streamlit (legacy semantic health core)
streamlit run ui/app.py

# Recompile Stlite bundle after Python changes
python scripts/build_stlite.py
```

---

## IDB schema (pair.html — locked)

- DB: `wf-vault` v2
- Store `wf-s` — `{ id, seq, type?, enc, nonce, commitment, ots_status?, ots_receipt?, ots_calendar?, ots_submitted?, ots_confirmed? }`
- Store `wf-sc` — `{ id: 'wf-cfg', s_canary, d_canary, d_contacts, sentinel_rules? }`

## OTS anchoring (pair.html — locked)

Functions live just before `// ── QR scanner`:
`_OTS_CALENDARS`, `_OTS_MAGIC`, `otsAnchorEntry`, `_otsUpgradeOne`, `otsUpgradeAll`,
`otsDownload`, `_otsAnchorRow`. Called from `_enterSanctuaryMode` (silent, non-blocking).

Chain decision rationale: IOTA rejected (Rebased introduced fees, poor verifier tooling);
EVM/Polygon rejected (persistent smart account creates on-chain behavioral fingerprint of
sanctuary activity); OpenTimestamps chosen (feeless, each hash anonymous in Merkle tree,
Bitcoin provenance, no library dependency). Do not re-open this decision.

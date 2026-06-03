# WellFair — New Session Handover (2026-05-30, session 2)

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

## Where we are: M6 code-complete, v0.0.5-dev

**Branch:** `release/v0.0.5` (pushed to origin/mediaprophet/wellfair)  
**Version:** v0.0.5-dev

### Completed this session (on top of previous M6 work)

**Firefox WebCrypto compatibility guard** (`pair.html` + `connector/index.html`):
- Ed25519 + X25519 feature probe runs before any init
- Unsupported browsers (Firefox < 130, old Chrome) get a clear styled error
- Both files patched; changes committed

**Bitcoin commitment anchoring via OpenTimestamps** (`pair.html`):
- `otsAnchorEntry(id)` — POST commitment bytes to first reachable calendar (alice → bob → finney); stores binary receipt + marks `ots_status: 'pending'`
- `_otsUpgradeOne(rec)` / `otsUpgradeAll()` — GET from calendar; flips to `'confirmed'` on 200; called silently on sanctuary unlock
- `otsDownload(id)` — assembles `.ots` file (OTS magic 31 bytes + version + SHA256 op tag + 32-byte commitment + calendar body); triggers browser download
- `_otsAnchorRow(r)` — per-entry anchor status in Evidentiary Export list:
  - `not_published` → `[Anchor to Bitcoin]` button
  - `pending` → `⏳ Pending Bitcoin block · [Download receipt]`
  - `confirmed` → `✓ Confirmed on Bitcoin · [Download .ots proof]`
- DLT anchor section copy updated from "chain decision pending" to describe OTS
- All vanilla fetch; no library dependency

**Developer Tools & Test Suite** (`ui/tabs/dev_tools.py`):
- New `🔒 Vault` tab — 9 browser-side tests via WebCrypto:
  - WebCrypto guard (Ed25519 + X25519 availability)
  - Ed25519 keygen, sign, verify, tamper rejection
  - X25519 DH shared-secret equality
  - AES-256-GCM encrypt/decrypt + wrong-IV rejection
  - PBKDF2-SHA256 sanctuary key (310k iter), timing check, determinism
  - Commitment computation: distinctness + nonce effect
  - OTS file format: magic bytes, version, SHA256 op, embedded hash
  - OTS calendar probe (opt-in: POST to alice.btc.calendar.opentimestamps.org)
  - IDB: wf-s + wf-sc store creation, round trip with ots_status field
- New `🗝️ Access Profiles` tab — Python-side:
  - profiles.json: load, count ≥9, required fields, ID list
  - access-profiles.ttl: wf: namespace, SHACL/ODRL keywords, rdflib parse
  - Cross-check: JSON profile IDs vs TTL

**Docs / project files:**
- `README.md` — comprehensive rewrite for v0.0.5-dev (vault as primary layer, M1–M6 summaries, updated capabilities table, updated project layout)
- `CLAUDE.md` — M6 marked code-complete; remaining items are runtime/device

---

## What remains — all runtime/device, no code tasks

| Task | What's needed |
|------|---------------|
| **Real-device testing** | iOS Safari, Android Chrome, Firefox 130+ — matrix in `instructions/BROWSER_COMPAT.md` |
| **SURB stress test** | Run Nym client, toggle airplane mode, verify fragment reassembly + SURB replenishment |
| **Nym Sandbox validation** | Run `docs/nym-test.html` against `https://sandbox-nym-api1.nymtech.net/api` → confirm SDK + cold-start time → set `NYM_SDK_URL` constant in `pair.html` |

---

## Uncommitted changes on the branch

These Streamlit/WASM layer files have local modifications that were not staged (separate context, 55 lines):
- `docs/app.html`
- `scripts/build_stlite.py`
- `ui/app.py`
- `ui/tabs/anatomy_3d.py`
- `ui/utils/navigation.py`

And untracked files from a separate work stream:
- `docs/packages/`, `docs/package-download-ui.js`
- `expert-authoring-tool/`
- `ui/tabs/packages_tab.py`, `ui/utils/package_bridge.py`
- `user-runtime-lib/`

Ask the user before staging any of these — they may belong to a different sprint or PR.

---

## Key files

```
docs/
  pair.html              Phone vault — Noise responder, Ed25519 sign, Sanctuary Mode,
                         Tripwire / Synthesis / Evidentiary panels, OTS anchoring,
                         Nym DMS + anon notify
  connector/index.html   Desktop terminal — Noise initiator, Ed25519 verify
  nym-test.html          Nym SDK validation harness (run before activating NYM_SDK_URL)
  manifest.webmanifest   PWA manifest
  profiles/
    access-profiles.ttl  SHACL access profile shapes (canonical)
    profiles.json        JS-loadable registry

ui/tabs/dev_tools.py     Developer Tools & Test Suite (8 tabs, 23 test suites)

instructions/
  VAULT_CONNECTOR_NEXT_STEPS.md   Full milestone checklist
  BROWSER_COMPAT.md               Audit results + real-device test matrix
  SESSION_HANDOVER_2026-05-30.md  Prior session handover (session 1)
```

## Dev server

```
python -m http.server 3000 --directory docs
```
Phone vault: `http://localhost:3000/pair.html`  
Desktop terminal: `http://localhost:3000/connector/`

---

## IDB schema (pair.html — do not change without explicit instruction)

- DB: `wf-vault` v2
- Store `wf-s` — sanctuary entry log:
  `{ id, seq, type?, enc, nonce, commitment, ots_status?, ots_receipt?, ots_calendar?, ots_submitted?, ots_confirmed? }`
  - `type` absent or `'assertion'`/`'hypothesis'` → Unvarnished Log
  - `type: 'tripwire'` → Tripwire Dashboard
- Store `wf-sc` — config: `{ id: 'wf-cfg', s_canary, d_canary, d_contacts, sentinel_rules? }`

All `enc` values are `{ iv, ct }` blobs, AES-256-GCM under the sanctuary key.

---

## OTS implementation notes (for future work)

OTS functions live in `pair.html` just before `// ── QR scanner`:
- `_OTS_CALENDARS` — [alice, bob, finney]
- `_OTS_MAGIC` — 31-byte Uint8Array (hardcoded)
- `otsAnchorEntry(id)` — called from UI button
- `_otsUpgradeOne(rec)` — called by `otsUpgradeAll()`
- `otsUpgradeAll()` — called from `_enterSanctuaryMode()` (non-blocking)
- `otsDownload(id)` — builds and downloads `.ots` file
- `_otsAnchorRow(r)` — renders per-entry anchor status HTML

The `.ots` file format: `_OTS_MAGIC (31 bytes) + 0x01 (version) + 0x08 (SHA256 op) + commitment (32 bytes) + calendar body`. Compatible with standard OTS verifiers.

The chain decision discussion: IOTA was rejected (Rebased introduced fees, poor verifier ecosystem). EVM/Polygon was rejected (persistent smart account creates on-chain behavioral fingerprint). OpenTimestamps chosen: feeless, anonymous, Bitcoin provenance, no on-chain identity.

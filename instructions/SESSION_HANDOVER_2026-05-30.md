# WellFair — New Session Handover (2026-05-30)

## What this project is

Privacy-first personal health vault. Phone is the authoritative vault; desktop is a
stateless terminal. All live data flows over an end-to-end-encrypted WebRTC DataChannel
(Noise_XX + AES-256-GCM). Nothing persists on the desktop — closing the tab destroys
everything.

**Mandatory terminology** — always use "identity credentials" (not DIDs, not VCs). Use
SHACL/RDFS shapes for data about people; OWL only for policy artefacts. Health namespace:
`wf:` → `https://wellfare.social/ns/vault#`.

Read `CLAUDE.md` for the full orientation and locked architecture decisions before writing
any code.

---

## Where we are: Milestone 6 in progress

**Milestones 1–5 complete.** M4 (Nym) is scaffolded and needs one runtime validation step
(run `docs/nym-test.html` against Nym Sandbox testnet, then set `NYM_SDK_URL` in
`pair.html`) — that is a live-network test, not a code task.

**M6 completed last session:**
- Gun write audit → CLEAN; connector storage audit → CLEAN (documented in
  `instructions/BROWSER_COMPAT.md`)
- `manifest.webmanifest` updated for `pair.html`; PWA meta tags wired into `pair.html` head
- Wake Lock API — acquired on session approve across all three approve paths, released on
  `endSession()`, re-acquired on `visibilitychange`
- Relay unreachable handling — 12-second timeout in `connectToSession()` → cancel + scan error
- Gun signalling cleanup post-handshake on both phone and connector sides
- **Tripwire Dashboard** (Active Opaque Collisions + Resolution Engine) in Sanctuary workspace
- **Synthesis Engine** (Contradiction Audits + Incoherence Reports + Sentinel Ruleset) in
  Sanctuary workspace
- **Evidentiary Export** — VP generation (JSON-LD, Ed25519 signed, commitment hashes) +
  Commitment Manifest download for manual DLT anchoring

**M6 remaining (in priority order):**

### 1. DLT chain write for Sanctuary commitment anchors ← primary code task

Commitment hashes are already computed (`sha256(sha256(entry) ‖ nonce)`) and stored
locally in every `wf-s` IDB record. The "Export commitment manifest" button in the
Evidentiary Export panel already packages them for manual anchoring. What remains is the
actual on-chain write, triggered from the same panel.

**Chain decision to surface:** IOTA (feeless, `did:iota` alignment, IoT-focused) vs
Ethereum/Polygon (widest verifier ecosystem, gas cost). Recommend IOTA for a feeless
phone-based PWA, but this is a user decision — surface the tradeoffs and implement
whichever is chosen.

Implementation approach:
- Wire a "Publish to [chain]" button per commitment in the Evidentiary Export panel
- Use a lightweight browser-compatible SDK (IOTA: `@iota/sdk` WASM; Ethereum: `ethers.js`
  with a simple anchoring contract on Polygon)
- The published value is the commitment hash only — no entry content ever leaves the device
- Store the on-chain transaction ID / block reference alongside the commitment in IDB

### 2. Firefox WebCrypto compatibility check

Ed25519 `SubtleCrypto.generateKey` landed Firefox 111; X25519 landed Firefox 130. Add a
feature detection on startup in `pair.html` and `connector/index.html` — if either is
missing, show a clear "browser not supported" message rather than a cryptic error.

### 3. Real-device testing (not a code task — physical devices needed)

Matrix template is in `instructions/BROWSER_COMPAT.md`. Key risks documented there:
- iOS Safari: WebRTC DataChannel, camera QR, Wake Lock, PWA install, BFCache
- Firefox Desktop: Ed25519 + X25519 WebCrypto support
- Android Chrome: PWA "Add to Home Screen" with `start_url: /pair.html`

### 4. SURB stress test (not a code task — runtime validation)

Simulate airplane-mode toggle while Nym client is active; verify SURB replenishment and
fragment reassembly buffer expiry behave correctly.

---

## Key files

```
docs/
  pair.html              Phone vault — Noise responder, Ed25519 sign, Sanctuary Mode,
                         Tripwire / Synthesis / Evidentiary panels, Nym DMS + anon notify
  connector/index.html   Desktop terminal — Noise initiator, Ed25519 verify, owner workspace
  nym-test.html          Nym SDK validation harness (run before activating NYM_SDK_URL)
  manifest.webmanifest   PWA manifest — start_url: /pair.html
  profiles/
    access-profiles.ttl  SHACL access profile shapes (canonical)
    profiles.json        JS-loadable registry

instructions/
  VAULT_CONNECTOR_NEXT_STEPS.md   Full milestone checklist with all M6 checkboxes
  BROWSER_COMPAT.md               Audit results + real-device test matrix template
  sanctuaryMode.md                Sanctuary Mode specification (M5)
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
- Store `wf-s` — sanctuary entry log: `{ id, seq, type?, enc, nonce, commitment }`
  - `type` absent or `'assertion'`/`'hypothesis'` → Unvarnished Log entries
  - `type: 'tripwire'` → Tripwire Dashboard entries
- Store `wf-sc` — config: `{ id: 'wf-cfg', s_canary, d_canary, d_contacts, sentinel_rules? }`

All `enc` values are `{ iv, ct }` blobs, AES-256-GCM under the sanctuary key.

---

Read `CLAUDE.md` and `instructions/VAULT_CONNECTOR_NEXT_STEPS.md` in full before writing
any code. Architecture decisions in those files are locked and must not be revisited
without explicit instruction.

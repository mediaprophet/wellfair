# WellFair Vault Connector — Implementation Continuation

This file carries forward the architectural decisions and remaining work from the
initial connector build session. Read it fully before writing any new code.

---

## Terminology

- Use **"identity credentials"** — not "DIDs", not "Verifiable Credentials", not "VCs".
  This is the original W3C Credentials Community Group / Web Payments CG term.
  Technical spec names (did:key, did:peer, W3C VC Data Model) may appear in
  technical contexts but the *concept* is always "identity credentials".
- Use **SHACL/RDFS shapes** for data about people — never OWL class membership.
  OWL is used only for policy artefacts (EdgeConstraint, etc.), not for the
  natural person or their health data.
- Health data paths use the `wf:` namespace: `https://wellfare.social/ns/vault#`

---

## What Has Been Built

### Files created / modified

| File | Purpose |
|------|---------|
| `docs/connector/index.html` | Desktop connector — pairing, app shell, owner workspace, Noise initiator, Ed25519 verify |
| `docs/pair.html` | Phone vault — scan, profile, PIN, consent, serve, Noise responder, Ed25519 sign |
| `docs/profiles/access-profiles.ttl` | SHACL shapes for all 9 access profiles (canonical model) |
| `docs/profiles/profiles.json` | JS-loadable profile registry derived from the TTL |
| `CLAUDE.md` | Auto-loaded session orientation (project purpose, architecture, current state, dev server) |
| `.claude/launch.json` | Local dev server config (`python -m http.server 3000 --directory docs`) |

### What works end-to-end (mock data only)

1. Desktop opens `/connector/` → generates Ed25519 `did:key` + X25519 Noise key + session ID
   → writes Gun.eco relay → shows QR
2. Phone opens `/pair.html` → scans QR → Gun relay delivers SDP offer → WebRTC DataChannel established
3. **Noise_XX_25519_AESGCM_SHA256 handshake** runs in `dc.onopen` (3 messages) → both sides
   derive non-extractable AES-256-GCM send/recv keys. All subsequent DataChannel traffic is encrypted.
4. Phone shows profile selection (9 profiles) → user selects → consent step
5. Desktop sends encrypted `{type:"request", id, section}` → phone signs response with Ed25519
   → desktop verifies signature before rendering
6. Desktop renders data; no persistence anywhere on desktop
7. Owner mode: profile selection → 4-digit PIN (demo PIN: `1234`) → full R/W workspace
8. Owner workspace: Documents (drag-drop, text extraction, save to vault), Notes,
   Mental Health, Social Context; Text A+/A− accessibility controls; high-contrast toggle

### Access profiles defined (in TTL + JSON)

| Profile | Auth required | R/W | Emergency |
|---------|--------------|-----|-----------|
| Owner Workspace | Vault owner PIN | R/W | No |
| Emergency / First Responder | Emergency responder VC | R | Yes (2h) |
| Emergency Department | Clinical professional VC | R | Yes (4h) |
| General Practitioner | Clinical professional VC | R | No |
| Specialist | Clinical professional VC | R | No |
| Psychiatrist / Mental Health | MH practitioner VC | R | No |
| Social Worker | Social worker VC | R | No |
| Personal / Partner | None | R | No |
| Carer / Family | None | R | No |
| Legal Advocate | Shared PIN | R | No |

### Message protocol (DataChannel — all encrypted after Noise_XX handshake)

Handshake (plaintext JSON, before session keys are derived):
```
Desktop → Phone:  {type:"noise", msg:1, e:"<b64 X25519 pub>"}
Phone → Desktop:  {type:"noise", msg:2, e:"<b64>", s:"<b64 encrypted static pub>"}
Desktop → Phone:  {type:"noise", msg:3, s:"<b64 encrypted static pub>"}
```

Application messages (AES-256-GCM binary — 4-byte nonce prefix + ciphertext):
```
Desktop → Phone:
  {type:"hello", v:1}
  {type:"request", id, section}
  {type:"disconnect"}
  {type:"write_section", id, section, data}              (owner mode only)
  {type:"store_document", id, filename, size, pages, extracted_text, stored_at}

Phone → Desktop:
  {type:"session_info", vault_did:"did:key:z…", profile:{…}, sections:[]}
  {type:"response", id, section, data, sig:"<b64 Ed25519 sig over 'section:JSON(data)'>"}
  {type:"error", id, message}
  {type:"vault_write_ack", id, section|filename}
  {type:"disconnect"}
```

### Vault mock data sections (in `pair.html` VAULT object)

overview, heart_rate, blood_pressure, sleep, steps, weight, medications,
allergies, conditions, blood_type, dnr, emergency_contacts, surgical_history,
mental_health, sexual_health, social_context

---

## Remaining Work — Milestones

### Milestone 1 — Local-first PoC hardening  *(polish deferred to Milestone 6)*

Core flow works. Remaining polish items have been moved into Milestone 6 where they
belong alongside the broader hardening and browser-compat pass.

### Milestone 2 — Identity Credentials Layer  *(complete)*

- [x] Ed25519 `did:key` generated per session (both sides) via WebCrypto + base58btc encode
- [x] X25519 static keypairs for Noise_XX (vault: generated at startup; connector: per session)
- [x] Noise_XX_25519_AESGCM_SHA256 handshake over DataChannel — 3 messages, derives
      non-extractable AES-256-GCM send/recv keys via HKDF-SHA256
- [x] All application DataChannel traffic AES-256-GCM encrypted (4-byte nonce prefix)
- [x] Vault signs every `response` with Ed25519; desktop caches vault public key from
      `session_info` and verifies before rendering; rejected data never reaches the UI
- [x] Session keys + noise keys nulled in teardown (GC eligible)

Remaining from original M2 scope (deferred):
- [ ] `did:peer` per pairing stored in vault's IndexedDB (persistent contacts)
- [ ] Section data packaged as Verifiable Presentation with embedded ODRL policy
- [ ] `dct:references` wired to UDHR/GDPR anchors from `WebCivics/ontologies`

Reference: `docs/profiles/access-profiles.ttl` has the full ODRL/credential model.
Reference: `WebCivics/ontologies` (GitHub) has `ttl/un/udhr.ttl` and `ttl/w3c/odrl.ttl`.

### Milestone 3 — Ephemeral Sharing Flow polish  *(complete)*

- [x] Session TTL: vault overwrites `session/{sid}` Gun node after configurable timeout
      (`SESSION_TTL_MS = 30 * 60 * 1000` in `pair.html`; fires TTL timer in both
      `approveSession` and `approveOwnerSession`; `teardown()` also puts null on disconnect)
- [x] `beforeunload` / `pagehide` / `visibilitychange` cleanup on connector
      (`beforeunload` sends disconnect; `pagehide` calls teardown; `visibilitychange`
      starts 2-minute grace timer that disconnects if tab stays hidden)
- [x] BFCache eviction on connector tab (`event.persisted` check in `pagehide` handler
      calls `event.target.location.replace('about:blank')`)
- [x] `FinalizationRegistry` test: `_gcRegistry` registered in both files; session keys
      registered before nulling in `teardown()` — GC confirmation logged to console
- [x] Emergency profile: pre-authorisation setup UI on phone (`⚙ Emergency access settings`
      panel in owner serving step; `preAuthorizedProfiles` Set persists across sessions;
      pre-authorized profiles skip consent and auto-approve via `autoApproveEmergency()`)
- [x] Emergency profile: full ISO timestamp + accessor `did:key` shown in audit log
      for emergency profile sessions (`log-emergency` CSS class, `.log-did` display)
- [x] Legal Advocate profile: session-scoped section picker now shows only
      `profile.sections` (not all sections), all unchecked by default with explanatory hint

### Milestone 4 — Nym Mixnet Integration  *(scaffolded — one activation step remaining)*

Goal: route Sanctuary Mode / Dead Man's Switch traffic anonymously through Nym.

- [x] Add COOP/COEP headers via Service Worker so Nym Wasm can initialise:
  `withCrossOriginIsolation()` in `docs/sw.js` wraps every same-origin response.
  Both `pair.html` and `connector/index.html` register `/sw.js` at startup.
  CDN scripts have `crossorigin="anonymous"` for COEP compatibility.
- [x] Validation harness: `docs/nym-test.html` — standalone page that checks
  `crossOriginIsolated`, times SDK cold start, tests SURB send in isolation.
  Uses Nym Sandbox testnet (`https://sandbox-nym-api1.nymtech.net/api`).
  Test tokens available via Nym Discord #faucet channel.
- [x] Gun `nym/` namespace adapter built in `pair.html`:
  - `nymAdapter.send(recipient, payload)` routes vault outbound via Nym instead of Gun
  - Fragments payloads > 28 KB (Sphinx packet limit with overhead)
  - Reassembly buffer keyed on `(msg_id, fragment_idx)`, 30 s expiry, cleaned every 10 s
- [x] SURB pool: `surbBudget = 20` on init, 3 attached per outbound message,
  optimistic replenish when budget < 5 (real exhaustion surfaces as SDK send errors)
- [x] Dead Man's Switch wired in `pair.html` (owner mode panel ⚡):
  configurable interval, two trustee Nym addresses, check-in / test-fire buttons;
  on missed check-in, `dmsFire()` sends encrypted alert via `nymAdapter` to trustees
- [x] `pair.html`: "Anonymous notification" section added (owner mode only, panel ☁) —
  compose a message, send via `nymAdapter`, no WebRTC involved

**Remaining activation step** (not a code change — a runtime validation):
1. Serve locally: `python -m http.server 3000 --directory docs`
2. Open `http://localhost:3000/nym-test.html`, run checks, confirm:
   - `crossOriginIsolated = true`
   - SDK imports and cold-starts successfully
   - SURB send test passes
3. Note the confirmed `NYM_SDK_URL` CDN/local path and cold-start time
4. Set `NYM_SDK_URL` constant at the top of `pair.html`'s `<script>` block
5. Optionally update `NYM_API_URL` from mainnet to Sandbox for continued dev

### Milestone 5 — Sanctuary Mode & Duress  *(complete — core flow)*

Reference: `instructions/sanctuaryMode.md` has the full Sanctuary Mode specification.

- [x] Two-key KDF hierarchy:
  - `deriveVaultKey(pin, salt)` — PBKDF2-SHA256, 310 000 iterations (OWASP 2023 min)
  - Sanctuary key: derived from Sanctuary PIN + `_SANC_SALT`
  - Duress key: derived from Duress PIN + `_DURS_SALT`
  - Main vault key slot: `_MAIN_SALT` reserved for full vault encryption (future)
  - All three keys are cryptographically independent
- [x] Sanctuary namespace in IndexedDB:
  - DB: `wf-vault` v2; stores: `wf-s` (entry log), `wf-sc` (config/canaries)
  - No string `"sanctuary"` appears in any store name or IDB key
  - All entries AES-256-GCM encrypted under the sanctuary key before storage
- [x] Decoy vault: main PIN → normal owner workspace with zero signal of Sanctuary
  - `duressModeActive` flag suppresses the `⚫ Sanctuary Mode` panel entirely
  - Duress PIN entry at owner PIN step opens identical workspace + fires silent alert
- [x] DLT commitment anchor for Sanctuary entries:
  `commitment = sha256(sha256(entry_bytes) ‖ nonce)` computed before IDB write
  `nonce` and `commitment` stored with each entry record; commitment logged to
  console ready to publish to a public chain (actual DLT write deferred to M6)
- [x] Duress PIN: configures via `_checkAndFireDuress()`:
  - Duress canary verified with PBKDF2-derived key
  - Contacts (Nym addresses) stored encrypted under duress key in `wf-sc`
  - On trigger: `duressModeActive = true`, silent Nym alert fired to contacts,
    normal owner workspace opens with sanctuary panel absent
- [x] Sanctuary workspace UI (`step-sanctuary`):
  - Dark theme via `body.sanctuary-active` CSS variable override
  - First-use setup flow: sanctuary PIN → confirm → duress PIN → confirm → ready
  - Unvarnished Log: Veiled Assertions + Hypothesis Nodes, encrypted + DLT-anchored
  - Contingency Protocols: duress contact configuration (Nym addresses)
- [x] Dead Man's Switch configuration UI — already present from Milestone 4 (owner
  mode `⚡ Dead Man's Switch` panel)

Deferred to Milestone 6 (from sanctuaryMode.md):
- [ ] Tripwire Dashboard (Active Opaque Collisions / Resolution Engine)
- [ ] Synthesis Engine (Contradiction Audits, Incoherence Reports)
- [ ] Evidentiary Export — Verifiable Presentation package + ephemeral serving link
- [ ] Actual DLT write for commitment anchors (chain TBD)

### Milestone 6 — Hardening & Cross-Browser  *(in progress)*

From M1 polish:
- [ ] Test on real Android + desktop end-to-end (currently only tested in browser preview)
- [ ] Validate iOS Safari: WebRTC DataChannel, camera QR scan, backgrounding behaviour
- [x] Session TTL cleanup on vault side — TTL timer fires in `approveSession`, `approveOwnerSession`,
  `autoApproveEmergency`; also in dc.onopen fallback path
- [x] "Keep screen active" — Wake Lock API (`acquireWakeLock` / `releaseWakeLock`) acquired on
  session approve, released in `endSession`; re-acquired on `visibilitychange` when visible
- [x] Gun relay unreachable handling — 12-second timeout in `connectToSession`; on expiry calls
  `cancelSession()` and shows error on scan step
- [x] Gun signalling cleanup — phone nulls answer node after Noise handshake; connector nulls
  offer + answer nodes after Noise handshake (belt-and-suspenders with SDP cleanup on answer receipt)

From M6 proper:
- [x] Gun write audit — all writes are signalling-only under `wf-v1-signal/`; no `core/` namespace;
  no health data; documented in `instructions/BROWSER_COMPAT.md`
- [x] Connector storage audit — zero writes to `localStorage`, `IndexedDB`, or `sessionStorage`;
  documented in `instructions/BROWSER_COMPAT.md`
- [ ] Full flow test matrix: iOS 16.4+ PWA, iOS 17, Android Chrome, Chrome Desktop,
  Firefox Desktop — template started in `instructions/BROWSER_COMPAT.md`
- [ ] Stress test SURB pool under poor connectivity (airplane mode simulation)
- [ ] Validate iOS backgrounding / force-close DMS check-in interaction
- [x] `pair.html` PWA manifest — `docs/manifest.webmanifest` updated (name, start_url, orientation);
  `<link rel="manifest">` + Apple PWA meta tags added to `pair.html` head

From deferred M5 (Sanctuary sub-features):
- [x] Tripwire Dashboard — Active Opaque Collisions feed + Resolution Engine (Keep Hidden /
  Reveal Temporarily / Export to Doctor); entries encrypted + DLT-anchored in `wf-s` IDB store
- [x] Synthesis Engine — Contradiction Audits (keyword overlap against immutable record) →
  Incoherence Report; Sentinel Ruleset management (encrypted under sanctuary key)
- [x] Evidentiary Export — entry selector → Verifiable Presentation (JSON-LD, Ed25519 signed,
  commitment hashes embedded) → auto-download; Commitment Manifest export for manual DLT anchoring
- [ ] Actual DLT write for commitment anchors — chain decision pending (IOTA vs Ethereum/Polygon);
  commitment hashes are computed and ready; manual export available via "Export commitment manifest"

---

## Architecture Decisions Locked In

These must not be revisited without explicit user instruction:

1. **Phone is authoritative vault** — desktop is always a stateless terminal
2. **Gun.eco for signalling only** — health data never touches Gun relay nodes
   (relay sees only encrypted SDP blobs during handshake, then never again)
3. **SHACL for data shapes** — OWL only for policy artefacts, never for people
4. **Identity credentials per relationship** — `did:peer` per pairing, `did:key` for
   ephemeral sessions; no shared long-term identifier across relationships
5. **Nym for anonymous routing** — not for real-time calls; WebRTC for all live sessions
6. **ODRL EdgeConstraints** — `webizen:OnDeviceProcessingOnly`, `webizen:maxCacheDuration`
   etc. from `docs/profiles/access-profiles.ttl` govern what receivers may do with data
7. **"Identity credentials"** — canonical term for what specs call DIDs + VCs

---

## Key File Locations

```
docs/
  connector/index.html      Desktop connector app
  pair.html                 Phone vault pairing page
  profiles/
    access-profiles.ttl     SHACL access profile shapes (canonical)
    profiles.json           JS-loadable profile registry
  sw.js                     Service Worker (needs COOP/COEP headers for Nym)
  manifest.webmanifest      PWA manifest

instructions/
  sanctuaryMode.md          Sanctuary Mode full specification
  VAULT_CONNECTOR_NEXT_STEPS.md   This file
```

---

## Notes on Related Repositories

- **WebCivics/ontologies** (GitHub, `2023` branch): `ttl/un/udhr.ttl` (UDHR as RDF),
  `ttl/w3c/odrl.ttl`, `ttl/w3c/shacl.ttl`. Use these as the rights instrument source.
  Canonical versions will eventually be DLT-anchored (specific chain TBD) rather than
  HTTP URIs. Bundle core ontologies in the PWA Service Worker cache at install time.

- **mediaprophet/Episteme** (GitHub): `custom-addons/rights-ontology.ttl` defines
  `webizen:EdgeConstraint`, `webizen:OnDeviceProcessingOnly`, `webizen:maxCacheDuration`
  etc. These are already referenced in `docs/profiles/access-profiles.ttl`.

- **Solid / `did:web`**: preferred long-term vault identity method. A Solid Pod's
  profile card URL maps directly to a `did:web` identifier. Fallback: `did:key`.

- **Nym SDK**: `@nymproject/sdk-full-fat` for browser. Requires SharedArrayBuffer
  (hence COOP/COEP headers). Cold start 3–8s. Not usable in Service Workers directly —
  must run on main thread or a dedicated `Worker`. zk-nyms (Coconut scheme) are for
  Nym network access auth only — NOT the health identity credential layer.

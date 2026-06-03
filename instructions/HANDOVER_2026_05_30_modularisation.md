# WellFair — Session Handover 2026-05-30 (Modularisation)

## What this session did

Refactored `pair.html` (3634 lines / 159 KB monolith) into a clean module tree.
`pair.html` is **untouched** and continues to work as a legacy fallback.

---

## New file layout

```
docs/
  vault.html          Daily-use vault app (PIN → meds, sanctuary, DMS, anon notify)
  webconnect.html     WebRTC pairing bridge (QR scan → profile → consent → serving)

docs/js/              Shared modules — plain globals, no bundler, load-order matters
  vault-idb.js               IDB constants + _openDB/_dbPut/_dbGet/_dbGetAll
  vault-crypto.js            PBKDF2 key derivation, AES-GCM _sEnc/_sDec, computeCommitment, toB64/fromB64
  vault-did.js               generateDidKey() — Ed25519, encoded as did:key:z…
  vault-nym.js               initNym(), nymAdapter.send(), DMS, anonymous notification
  vault-mock.js              VAULT mock object (all sections) + SECTION_LABELS
  vault-sanctuary-pins.js    PIN state machine, _setupSanctuary, _checkAndFireDuress, wake lock
  vault-sanctuary-log.js     Unvarnished Log, Tripwire Dashboard, Synthesis Engine
  vault-sanctuary-evidence.js  Evidentiary Export, generateVP, exportCommitmentManifest, OTS
  vault-meds-reminders.js    MedNotifier, _buildTodaySchedule, logMedTaken/Skipped, today panel
  vault-meds-lod.js          SUBSTANCE_INTERACTIONS, RxNorm/Wikidata LOD, interaction engine
  vault-meds-manager.js      openMedManager, saveMedication, ceaseMedication, sheet UI
  noise-xx.js                Noise_XX_25519_AESGCM_SHA256 — webconnect.html only
  profiles.js                Profile loading/rendering, emergency pre-auth — webconnect.html only
```

### Script load order (matters — later scripts call functions from earlier ones)

**vault.html** loads:
```html
vault-idb.js → vault-crypto.js → vault-did.js → vault-nym.js → vault-mock.js →
vault-sanctuary-pins.js → vault-sanctuary-log.js → vault-sanctuary-evidence.js →
vault-meds-reminders.js → vault-meds-lod.js → vault-meds-manager.js
```

**webconnect.html** loads (after html5-qrcode and Gun CDN scripts):
```html
vault-crypto.js → vault-did.js → vault-nym.js → vault-mock.js →
noise-xx.js → profiles.js
```
Note: vault.html loads `vault-idb.js` but webconnect.html does **not** — the transport
bridge has no direct IDB access. All IDB operations live in vault.html/modules.

---

## Page responsibilities

### vault.html — standalone daily health vault
- PIN entry → owner workspace (no WebRTC required)
- Shows: drug interactions, medication reminder/management, DMS, anon notify, sanctuary mode
- Sanctuary: PIN → Unvarnished Log, Tripwire, Synthesis, Evidentiary Export, OTS
- Duress detection: entering duress PIN opens normal-looking workspace + fires silent Nym alert
- "Connect to desktop →" link opens webconnect.html in a new context
- Demo: `vault.html?demo` skips PIN → shows owner workspace with mock data

### webconnect.html — WebRTC pairing bridge
- QR scan / manual session ID → profile selection → consent → serving
- Owner PIN: **authentication only** — no vault health UI (no meds, no sanctuary)
  - Owner serving shows activity log + emergency pre-auth panel + "Open Vault app" link
- Serves vault sections to desktop via Noise_XX encrypted DataChannel
- Demo: `webconnect.html?demo` skips pairing → owner serving mode with mock data
- Duress detection: **removed** — duress is a vault.html concern

### connector/index.html — desktop side
- Unchanged from M6. Nothing was touched.

---

## Key differences from pair.html

| Concern | pair.html | vault.html | webconnect.html |
|---------|-----------|------------|-----------------|
| Meds UI | ✓ inline | ✓ via modules | — |
| Sanctuary | ✓ inline | ✓ via modules | — |
| DMS / Anon notify | ✓ inline | ✓ via vault-nym.js | — |
| Duress detection | ✓ in pinKey | ✓ in pinKey | — removed |
| Emergency pre-auth | ✓ in serving | — | ✓ in serving |
| IDB | ✓ inline | ✓ via vault-idb.js | — |
| Noise_XX | ✓ inline | — | ✓ via noise-xx.js |
| Gun signalling | ✓ inline | — | ✓ inline script |
| VAULT mock | ✓ inline | ✓ via vault-mock.js | ✓ via vault-mock.js |

---

## State variables — where they live now

These are globals set by modules and used by the page's inline script:

| Variable | Defined in | Used by |
|----------|-----------|---------|
| `sanctuaryKey` | vault-sanctuary-pins.js | vault-sanctuary-log.js, vault-sanctuary-evidence.js |
| `sanctuaryActive` | vault-sanctuary-pins.js | vault-sanctuary-log.js |
| `duressModeActive` | vault-sanctuary-pins.js | vault.html inline (controls sanctuary panel visibility) |
| `_wakeLock` | vault-sanctuary-pins.js | acquireWakeLock / releaseWakeLock |
| `_medCheckInterval` | vault-meds-reminders.js | vault.html `lockVault()` |
| `dmsTimer` | vault-nym.js | vault.html `lockVault()` / `pagehide` |
| `nymClient` | vault-nym.js | vault-sanctuary-pins.js (`_checkAndFireDuress`) |
| `nymAdapter` | vault-nym.js | vault-sanctuary-pins.js, vault-nym.js (DMS/anon) |
| `vaultDidKey` | vault.html inline | vault-sanctuary-evidence.js (`generateVP`) |
| `allowedSections` | profiles.js | webconnect.html inline |
| `activeProfile` | profiles.js | webconnect.html inline |
| `profiles` | profiles.js | webconnect.html inline |
| `_sessionSend/_sessionRecv` | noise-xx.js | webconnect.html inline (teardown) |

---

## NYM_SDK_URL — new location

The constant has **moved** from `pair.html` to `js/vault-nym.js` (line 7):
```js
const NYM_SDK_URL = null; // TODO: set after validating with docs/nym-test.html
```
When activating Nym, edit `vault-nym.js` — this makes DMS/anon notify work in **both**
vault.html and webconnect.html (which both load vault-nym.js).

---

## Stale files to clean up

These files exist on disk but are **not referenced** by any page:
- `docs/js/vault-sanctuary.js` — superseded by the three `vault-sanctuary-*.js` files
- `docs/js/vault-meds.js` — superseded by the three `vault-meds-*.js` files

Safe to delete. They were the intermediate monolithic versions created before the
second round of splitting.

---

## Demo mode

Both pages support `?demo`:
- `vault.html?demo` — skips PIN, opens owner workspace with mock meds data
- `webconnect.html?demo` — skips pairing, goes straight to owner serving mode

**Known issue (inherited from pair.html):** Session TTL timer (`SESSION_TTL_MS = 30 min`)
still fires in demo mode on webconnect.html and calls `endSession()`. Consider suppressing
when `DEMO_MODE` is true.

---

## IDB schema

Unchanged from M6. vault.html and webconnect.html share the **same** IDB
(`wf-vault` v3) since they're same-origin. webconnect.html doesn't read IDB directly —
it serves data from the VAULT mock object (falling back to IDB only for medications via
the vault-meds modules which are loaded by vault.html, not webconnect.html).

If a user adds a medication in vault.html, it's stored in IDB. webconnect.html's
`handleDesktopMessage` serves the VAULT mock's medications section — **it does not
read IDB meds**. The desktop connector will see mock medications, not IDB-added ones,
until the serving layer is connected to IDB (a future task).

---

## Testing

Chrome (with Claude in Chrome extension) is required — Claude app preview lacks WebCrypto.

```
# Server
python -m http.server 3000 --directory docs

# Pages
http://localhost:3000/vault.html?demo          ← daily vault
http://localhost:3000/webconnect.html?demo     ← pairing bridge (demo)
http://localhost:3000/connector/?demo          ← desktop side (demo)
http://localhost:3000/pair.html?demo           ← legacy (still works)
```

Real pairing test:
1. Open `http://localhost:3000/webconnect.html` on phone/tab
2. Open `http://localhost:3000/connector/` on desktop
3. Scan QR or paste session ID

---

## What's next

### Immediate (next session)
1. **Test vault.html and webconnect.html in Chrome** — verify PIN unlock, meds panel,
   sanctuary mode, QR pairing flow. Use Chrome extension tools (`mcp__Claude_in_Chrome__*`).
2. **Fix webconnect.html serving meds from IDB** — `handleDesktopMessage` currently
   reads from VAULT mock for the `medications` section. It should fall through to IDB-stored
   meds when available. This requires loading vault-idb.js in webconnect.html and
   calling `_getActiveMeds()` instead of `VAULT.medications()`.
3. **Delete stale files** — `docs/js/vault-sanctuary.js` and `docs/js/vault-meds.js`.

### Pending from previous sessions
4. **Medication Sprint 6** — Diet/food log with substance tagging and temporal
   interaction checks. Belongs in vault-meds-lod.js (substance tagging) +
   new vault-meds-diet.js.
5. **Demo account connection** — `connector/?demo` should auto-connect to a Gun session
   published by the vault app's demo account rather than using local DEMO_VAULT mock.
   Requires agreeing on the session ID / Gun namespace with the vault team.
6. **Nym activation** — Run `docs/nym-test.html` against Sandbox testnet, confirm SDK
   loads, set `NYM_SDK_URL` in `docs/js/vault-nym.js`.
7. **Real-device testing** — iOS Safari, Android Chrome, Firefox 130+.
   Matrix in `instructions/BROWSER_COMPAT.md`.

### Architecture horizon
8. **WASM vault integration** — vault.html's VAULT mock is a placeholder for data that
   ultimately lives in the WASM vault app (`expert-authoring-tool/`, `user-runtime-lib/`).
   When the WASM vault exposes a JS bridge, vault.html should call it instead of the mock.
9. **demo/index.html** — Demo landing page linking to both pages, or auto-connecting to
   the vault app's demo Gun session.

---

## Git state

Branch `release/v0.0.5` — this session's work is uncommitted (all new/modified files
are working-tree only). Commit when the next session validates in Chrome.

Files changed/created this session:
- `docs/vault.html` (new)
- `docs/webconnect.html` (new)
- `docs/js/` (new directory — 13 files)
- `CLAUDE.md` (key files section updated)

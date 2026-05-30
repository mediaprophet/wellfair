# WellFair — Session Handover VC-7b (2026-05-30)

## Milestone covered
VC-7b: vault.html Directory panel — script wiring, key derivation, Contacts button, bottom sheet UI

## Completed in this session

- Added `<script src="js/vault-directory.js"></script>` to vault.html after vault-mock.js
- Wired `initDirectory(key)` in `pinKey()`: `deriveVaultKey(entered, _MAIN_SALT).then(k => initDirectory(k))` called on both normal PIN and duress PIN paths
- Nulled directory key in `lockVault()`: `initDirectory(null)`
- Added `dir-panel` show/hide to `openOwnerWorkspace()` (shown unless duress mode) and `lockVault()` (hidden)
- Added `dir-sheet` bottom sheet close in `lockVault()`
- Added directory CSS block: `.dir-sheet`, `.dir-body`, `.dir-header`, `.dir-scroll`, `.dir-search`, `.dir-contact-card`, `.dir-contact-info`, `.dir-contact-name`, `.dir-contact-did`, `.dir-rel-badge`, `.dir-detail-field`, `.dir-detail-label`, `.dir-detail-value`, `.dir-detail-mono`, `.dir-form-label`, `.dir-input`, `.dir-empty`
- Added "👥 Contacts" button in owner workspace (`id="dir-panel"`) above Sanctuary
- Added `#dir-sheet` bottom sheet HTML with three sub-views: list (`dir-list-view`), add form (`dir-add-view`), detail (`dir-detail-view`)
- Added all directory JS functions in inline script:
  - `openDirectory()` / `closeDirectory()`
  - `_dirShowListView()` / `_dirShowAddForm()` / `_dirShowDetail()`
  - `_dirLoadContacts()` — calls `getAllContacts()` and renders
  - `_dirRenderList(contacts)` — renders cards; async post-render badge update for relationship status
  - `_dirFilterList(query)` — search filter (name + DID)
  - `_dirOpenDetail(id)` — decrypts and renders contact detail with agreement status
  - `_dirSaveNewContact()` — validates, calls `addContact()`, refreshes list
  - `_dirDeleteContact(id)` — confirm + `deleteContact()` + refresh
  - `_dirEsc(s)` — HTML escape helper
- `_dirAllContacts` module-level cache for the contact list

## Files modified

| File | Change summary | Key functions added |
|------|----------------|---------------------|
| `docs/vault.html` | Script tag + CSS + dir-panel button + dir-sheet HTML + initDirectory wiring + lockVault wiring + JS functions | `openDirectory`, `closeDirectory`, `_dirShowListView`, `_dirShowAddForm`, `_dirShowDetail`, `_dirLoadContacts`, `_dirRenderList`, `_dirFilterList`, `_dirOpenDetail`, `_dirSaveNewContact`, `_dirDeleteContact`, `_dirEsc` |

## IDB state

IDB version: **v4**  
Stores: `wf-s`, `wf-sc`, `wf-meds`, `wf-ml`, `wf-pc`, `wf-dl`, `wf-contacts`, `wf-relationships`, `wf-agreements`

## Script load order (vault.html) — current as of this session

```
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-directory →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager
```

## Verification results

Tested in Chrome against `http://localhost:3000/vault.html`:
- PIN unlock → owner workspace → "Contacts" button visible ✓
- Open Contacts sheet → empty state shown ✓
- Add contact (Dr Sarah Jones, did:key:z6MkTestAbc123) → card appears ✓
- Page reload → re-enter PIN → contact still present (IDB persistence) ✓
- Raw IDB record has keys `{ id, iv, ct }` — plaintext never stored ✓
- `lookupByDid('did:key:z6MkTestAbc123')` → returns correct contact ✓
- `lookupByDid('did:key:zzz_unknown')` → returns null ✓
- Zero console errors throughout ✓

## What to do next (immediate — first thing next session)

**Session 3 is VC-8 — Semantic Handshake (`vault-handshake.js`).**

1. Read `docs/js/vault-directory.js` (`saveRelationship`, `getRelationship`) — these are what VC-8 calls after handshake completion.
2. Read `docs/js/vault-did.js` — understand `generateDidKey()` and the key material available.
3. Create `docs/js/vault-handshake.js` with the four public functions:
   - `initiateHandshake(contactId)` — generates our did:key, constructs ODRL JSON-LD proposal, encodes as QR payload (and optionally sends via nymAdapter if contact has Nym address)
   - `receiveHandshake(payload)` — parses proposal, returns `{ contactName, did, agreement }` for user review
   - `acceptHandshake(payload, approved)` — signs agreement with our Ed25519 key, calls `saveRelationship()`, returns signed blob
   - `finaliseHandshake(signedBlob)` — verifies counterparty sig, calls `saveRelationship()` on initiator side
4. Add "Initiate handshake" button wiring in `_dirOpenDetail()` (currently `disabled` placeholder — enable it when vault-handshake.js is loaded)
5. Add `<script src="js/vault-handshake.js"></script>` after `vault-directory.js` in vault.html

The "Initiate handshake" button in the contact detail sheet is already rendered but disabled. In VC-8, change it to call `initiateHandshake(contactId)` and remove the `disabled` attribute.

## Decisions made this session

- Used a **bottom sheet overlay** (same pattern as `med-manager-sheet`) rather than a new `step-directory` full-page step. Rationale: the owner workspace uses a stacked panel layout without a nav bar; a sheet is more consistent and doesn't require changes to `showStep()`.
- The "Initiate handshake" button is rendered `disabled` with a tooltip explaining it's available in VC-8. This is intentional — wiring it now with a no-op would be confusing.
- Service worker cached the old vault-idb.js during verification — cleared manually. Future sessions: if scripts seem stale, unregister SW and clear caches before testing.
- `_dirEsc()` local HTML-escape helper added to inline script (not a conflict with any other global).

## Blocked / deferred

- Nothing blocked. All VC-7 acceptance criteria met.
- Relationship type is hardcoded to `'personal'` in `saveRelationship()` — VC-8 will call `updateContact()` with the negotiated type after handshake completes.

## Acceptance criteria met

- [x] IDB v4 opens without error; all 3 new stores created on upgrade
- [x] Add contact → appears in list → survives page reload
- [x] Contact data encrypted at rest (raw IDB value is `{ id, iv, ct }` — not plaintext)
- [x] `lookupByDid(did)` returns correct contact or null
- [x] Directory panel renders in vault.html owner workspace

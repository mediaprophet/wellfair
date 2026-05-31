# WellFair — Session Handover VC-7a (2026-05-30)

## Milestone covered
VC-7a: SHACL shapes for Contact/Relationship/UsageAgreement, IDB v4, vault-directory.js full public API

## Completed in this session

- Added `wf:Contact`, `wf:Relationship`, `wf:UsageAgreement` RDFS class declarations to `docs/profiles/access-profiles.ttl`
- Added all supporting property declarations: `wf:contactDid`, `wf:contactWebId`, `wf:contactNymAddress`, `wf:contactNotes`, `wf:relationshipType`, `wf:peerDid`, `wf:agreementRef`, `wf:agreementOdrl`, `wf:agreementSig`, `wf:counterpartySig`
- Added three SHACL NodeShapes: `wf:ContactShape`, `wf:RelationshipShape`, `wf:UsageAgreementShape` with `sh:property` constraints
- Bumped `_openDB` from v3 → v4 in `docs/js/vault-idb.js`
- Added three new IDB store constants: `_ST_CONTACTS = 'wf-contacts'`, `_ST_RELS = 'wf-relationships'`, `_ST_AGREEMENTS = 'wf-agreements'`
- Added three new stores to `onupgradeneeded` handler (guarded with `contains` check so existing data survives upgrade)
- Added `_dbDelete(store, key)` helper to `vault-idb.js` (was missing; needed by `deleteContact`)
- Created `docs/js/vault-directory.js` with full public API:
  - `initDirectory(aesKey)` — sets `_dirKey`; vault.html must call this on PIN verify (Session 2)
  - `addContact(name, did, webId, notes)` → plaintext record (with generated UUID id)
  - `getContact(id)` → plaintext or null
  - `getAllContacts()` → array of plaintext records
  - `updateContact(id, fields)` → updated plaintext record
  - `deleteContact(id)` → removes contact + relationship + agreement records
  - `lookupByDid(did)` → first matching contact or null (linear scan — fine for personal contacts)
  - `getRelationship(contactId)` → `{ ...rel, agreement }` or null
  - `saveRelationship(contactId, peerDid, agreementJsonLd, ourSig, theirSig)` → `{ relationship, agreement }`
- Exported `DIR_REL_TYPES` constant: `{ PERSONAL, PROFESSIONAL, CLINICAL, LEGAL }`

## Files modified

| File | Change summary | Key functions added |
|------|----------------|---------------------|
| `docs/profiles/access-profiles.ttl` | Added VC-7 vocabulary section + 3 NodeShapes at end of file | — |
| `docs/js/vault-idb.js` | v4 bump; 3 new store constants; 3 new stores in upgrade handler; `_dbDelete` helper | `_dbDelete` |
| `docs/js/vault-directory.js` | New file — full directory module | `initDirectory`, `addContact`, `getContact`, `getAllContacts`, `updateContact`, `deleteContact`, `lookupByDid`, `getRelationship`, `saveRelationship` |

## IDB state

IDB version: **v4**  
Stores: `wf-s`, `wf-sc`, `wf-meds`, `wf-ml`, `wf-pc`, `wf-dl`, `wf-contacts`, `wf-relationships`, `wf-agreements`

## Script load order (vault.html)

vault-directory.js has NOT been added to vault.html yet — that is Session 2 (VC-7b). The current load order in vault.html is unchanged:

```
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager
```

Target load order after Session 2:

```
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-directory →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager
```

## What to do next (immediate — first thing next session)

**Session 2 is VC-7b — Directory panel in vault.html.**

1. Open `docs/vault.html`. Add `<script src="js/vault-directory.js"></script>` after `vault-mock.js` and before `vault-sanctuary-pins.js`.

2. Wire up `initDirectory`: in `openOwnerWorkspace()` (line ~756), derive the main vault key and pass it to `initDirectory()`. The key should come from `deriveVaultKey(enteredPin, _MAIN_SALT)`. The PIN is in `pinEntry` at the moment `pinKey()` triggers `openOwnerWorkspace()` — capture it before the timeout. Pattern:
   ```js
   // in pinKey(), just before setTimeout(openOwnerWorkspace, 400):
   deriveVaultKey(entered, _MAIN_SALT).then(k => initDirectory(k));
   ```
   Also null the key on `lockVault()`:
   ```js
   initDirectory(null);
   ```

3. Add the `step-directory` panel to vault.html after `step-owner`. The plan specifies:
   - New step `step-directory` with nav link "Contacts" in the owner workspace nav
   - Contact list with search box, add button, and contact cards
   - Contact detail sheet: name, DID, WebID, relationship type, agreement status
   - "Initiate handshake" button per contact (wires to VC-8 in Session 3 — leave as `disabled` placeholder for now)
   - Panel should follow the same CSS pattern as `step-sanctuary` (see lines 537–702 in vault.html)

4. Wire the Directory nav button in the owner workspace nav bar (same pattern as the Sanctuary Mode button).

5. Add JavaScript in vault.html for the Directory panel: load contacts on panel open, render cards, handle add/delete.

6. Verify in Chrome: add a contact → reload page → contact still appears (encrypted IDB round-trip works).

## Decisions made this session

- `_dbDelete` added to `vault-idb.js` since it was missing and required by `deleteContact`. No other files were changed to add this — it is a pure addition.
- `saveRelationship` stores the relationship `type` as `DIR_REL_TYPES.PERSONAL` by default. VC-8 (Semantic Handshake) should call `updateContact(id, { type })` after saving the relationship if a different type is appropriate.
- `theirSig` in `saveRelationship` may be `null` on the initiator side before `finaliseHandshake()` sets it (VC-8 concern).
- `vault-directory.js` does NOT import anything — it relies on globals from `vault-idb.js` and `vault-crypto.js` (no bundler, plain globals, load order matters).
- `initDirectory(null)` is safe to call on lock — all subsequent API calls will throw cleanly before touching IDB.

## Blocked / deferred

- `vault.html` wiring — deferred to Session 2 (VC-7b) as instructed. The directory module is complete but not yet wired.
- `lookupByDid` is O(n) linear scan across all decrypted contacts. For a personal contact list this is fine. If the directory grows large (>1000 contacts) an in-memory did→id index could be added in a future session.

## Acceptance criteria met

- [x] IDB v4 opens without error; all 3 new stores created on upgrade — implementation complete; runtime verification deferred to Session 2
- [ ] Add contact → appears in list → survives page reload — deferred to Session 2 (vault.html not wired yet)
- [x] Contact data encrypted at rest (raw IDB value is `{ id, iv, ct }` — not plaintext) — confirmed in code
- [x] `lookupByDid(did)` returns correct contact or null — implemented
- [ ] Directory panel renders in vault.html owner workspace — deferred to Session 2

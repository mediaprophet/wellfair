# WellFair — Grok Collaboration Guide
> **Purpose**: Define tasks Grok can implement in parallel with Claude Code sessions,
> the context Grok needs, and the exact reporting format so Claude can integrate
> Grok's output cleanly.
>
> Last updated: 2026-06-04

---

## Overview

WellFair is a privacy-first health vault. The primary codebase lives at:
`https://github.com/mediaprophet/wellfair` — branch `feature/qualia-db-integration`

Grok is best used for tasks that are:
- **Self-contained** — one or two files, clear input/output contract
- **Well-specified** — data models, Rust structs, SHACL shapes, IDB patterns
- **Not browser-testable** — Grok cannot run a browser; Claude handles integration/verification

Claude integrates Grok's output, runs the dev server, and verifies in Chrome. Grok does not
need to test. Grok **must not** invent architecture — follow the patterns below exactly.

---

## Mandatory context — read before any task

### 1. Terminology (non-negotiable)
- User-facing: "identity credentials" (never DIDs or VCs), "Verified Directory" (never "sovereign")
- `wf:` namespace = `https://wellfare.social/ns/vault#`
- `qp:` namespace = `https://qualia.id/ns/` (cooperative projects ontology)
- SHACL/RDFS for shapes about people; OWL only for policy artefacts (EdgeConstraint, etc.)

### 2. Encryption pattern (all JS IDB writes)
Every record stored in IndexedDB is AES-256-GCM encrypted using `_sEnc`/`_sDec` from `vault-crypto.js`.
The stored form is always `{ id: record.id, iv: base64, ct: base64 }`.
The plaintext JS object is never written to IDB unencrypted.

```javascript
// Encrypt before write
async function _encRecord(plain) {
  const { iv, ct } = await _sEnc(_moduleKey, plain);
  return { id: plain.id, iv, ct };
}
// Decrypt on read
async function _decRecord(stored) {
  return _sDec(_moduleKey, { iv: stored.iv, ct: stored.ct });
}
```

All `_dbGet`, `_dbPut`, `_dbGetAll` calls from `vault-idb.js` use the raw encrypted form.
Decryption is done in the module. Use `Promise.allSettled` for batch decrypts — never `Promise.all`
(stale ciphertext from demo mode would abort the entire list).

### 3. IDB versioning
Current version: **v13**. The next upgrade must be **v14**.
IDB store creation always uses the idempotent pattern:
```javascript
if (!db.objectStoreNames.contains('wf-newstore'))
  db.createObjectStore('wf-newstore', { keyPath: 'id' });
```

### 4. CBOR-LD pattern
All QualiaStore writes go through `window.vaultCborLd.insertRecordToQualiaStore(storeName, plainRecord)`.
This is called with the **plaintext** record (before encryption). The CBOR-LD Lexicon maps IRI strings
to u64 IDs. Never write JSON, Turtle, or RDF-XML to QualiaStore — it is rejected by the binary gatekeeper.

### 5. Module public API pattern
Every JS module exposes a `window.vault<Module>` object:
```javascript
window.vaultProjects = {
  initProjects,
  addProject, getProject, getAllProjects, ...
};
```
All functions are declared in module scope (`function foo() {...}`), not as properties.

### 6. Rust / wellfare-core
- Crate: `wellfare-core/` at repo root
- WASM target: `wasm-pack build --release --target web --out-dir ../docs/pkg`
- All WASM exports are in `wellfare-core/src/wasm.rs` using `#[wasm_bindgen]`
- Rust edition 2024; oxigraph 0.4 is a default dependency
- `ed25519-dalek` and `sha2` are acceptable additions for signing/hashing tasks
- `serde` + `serde_json` already in `Cargo.toml`
- No `wgpu` dependency for WASM targets — it is behind `--features qualia` only

### 7. What Grok must NOT do
- Invent new architecture — follow patterns from existing modules
- Change IDB version without specifying the exact bump (current v13 → next v14)
- Use `async/await` with `Promise.all` for bulk decrypts — must use `Promise.allSettled`
- Add user-facing text using "DID", "VC", "sovereign", "OWL class"
- Write tests that require a browser — Grok produces source code; Claude tests it

---

## Available tasks

Each task below is self-contained. Grok should pick **one task at a time** and produce
a complete artefact. Tasks can be run in parallel by different Grok instances.

---

### G1 — Rust: ObligationLedger (R-CP1)

**What**: Implement `ObligationLedger` Rust struct — µ-unit calculation and CRDT merge algorithm.
Works in both WASM and native Tauri (no browser APIs).

**File to create**: `wellfare-core/src/obligation.rs`

**Existing reference** (JS equivalent in `docs/js/vault-projects.js`):
- µ-units = `totalHours × ratePerHour × 1000` (integer)
- CRDT merge: max(muUnits) wins per projectId — the higher count is always the most recent correct state
- Author-scoped: each contributor's balance is keyed by their did:key + projectId

**Required struct**:
```rust
pub struct ObligationLedger {
    pub project_id: String,
    pub author_did: String,
    pub total_hours: f64,
    pub mu_units: u64,
    pub rate_per_hour: f64,
    pub updated_at: String,  // ISO 8601
}
```

**Required methods**:
- `ObligationLedger::new(project_id, author_did, rate_per_hour) -> Self`
- `ledger.add_hours(hours: f64)` — adds hours, recomputes mu_units
- `ObligationLedger::merge(a: &Self, b: &Self) -> Self` — CRDT: return the one with higher mu_units; both must have the same project_id

**WASM export** (add to `wellfare-core/src/wasm.rs`):
```rust
#[wasm_bindgen]
pub fn create_obligation(project_id: &str, author_did: &str, rate: f64) -> JsValue {...}
#[wasm_bindgen]
pub fn merge_obligations(a_json: &str, b_json: &str) -> JsValue {...}
```

**Report format**: See "Reporting format" section below.

---

### G2 — Rust: Author-Scoped Merkle Signature (R-CP2)

**What**: `merkle_sign` function matching the JS implementation in `docs/js/vault-projects.js`.

**File to create**: `wellfare-core/src/merkle.rs`

**JS reference** (must produce identical hash output):
```javascript
async function _merkleHash(prevHash, hours, description, timestamp) {
  const prevBytes = prevHash ? fromB64(prevHash) : new Uint8Array(32); // genesis: 32 zero bytes
  const payload   = new TextEncoder().encode(JSON.stringify({ hours, description, timestamp }));
  const combined  = new Uint8Array(prevBytes.length + payload.length);
  combined.set(prevBytes);
  combined.set(payload, prevBytes.length);
  const digest = await crypto.subtle.digest('SHA-256', combined);
  return toB64(new Uint8Array(digest));
}
```

**Required function**:
```rust
// Returns base64url-encoded SHA-256(prevHashBytes ‖ UTF-8(JSON{hours,description,timestamp}))
// prev_hash_b64: base64url of previous hash, or None for genesis (uses 32 zero bytes)
pub fn merkle_hash(prev_hash_b64: Option<&str>, hours: f64, description: &str, timestamp: &str) -> String
```

**Dependencies to add** (Cargo.toml):
- `sha2 = "0.10"` (SHA-256)
- `base64 = "0.22"` (base64url encoding — use `engine::general_purpose::URL_SAFE_NO_PAD`)

**WASM export** (add to `wasm.rs`):
```rust
#[wasm_bindgen]
pub fn compute_merkle_hash(prev_hash_b64: Option<String>, hours: f64, description: &str, timestamp: &str) -> String
```

The JSON payload encoding must use `serde_json::json!` to produce exactly `{"hours":N,"description":"...","timestamp":"..."}` — key order matters for hash compatibility with the JS implementation.

**Report format**: See "Reporting format" section below.

---

### G3 — SHACL shapes for DIR4

**What**: Write SHACL node shapes for the cooperative and protocol vocabulary to append to
`docs/profiles/access-profiles.ttl`.

**Read first** (clone the repo and read):
- `docs/profiles/access-profiles.ttl` — existing shape patterns to follow
  - The file already has `qp:` prefix declared as `https://qualia.id/ns/`
  - The file already has shapes for `wf:ContributionRecord`, `wf:ObligationBalance`, `wf:CooperativeProject`,
    `qp:Contract`, `qp:EffortObligation`, `qp:Slice`, `qp:TokenizedShare`, `qp:hasConsentRelation`

**Shapes to add** (if not already present — check the file first):
1. `wf:VerifiableCredentialShape` — for records in `wf-credentials`: must have `wf:credentialType`, `wf:issuedAt` (xsd:dateTime), `wf:issuerDid` (string)
2. `wf:GuardianRelationshipShape` — for guardian/ward records in `wf-relationships`: must have `wf:role` = `"guardian"`, `wf:guardianDid`, `wf:wardDid`, `wf:scope` (string — ODRL EdgeConstraint IRI)
3. `qp:ProjectGovernanceShape` — for governance records: must have `qp:allowsCashOut` (xsd:boolean), `qp:tokenized` (xsd:boolean); optional `qp:cashOutCondition` (string)
4. `qp:DynamicEquitySliceShape` — for `wf-shares` records: `qp:contributorDid`, `qp:equityPercent` (xsd:decimal 0–100), `qp:allocationTimestamp` (xsd:dateTime)

**Output**: Turtle blocks to append to the existing `access-profiles.ttl`, each prefixed with a comment `# DIR4: <ShapeName>`.

**Report format**: See "Reporting format" section below.

---

### G4 — Rust: PFM data models (R-CP3)

**What**: Rust structs for the Personal Finance Management module.

**File to create**: `wellfare-core/src/pfm.rs`

**Required structs**:

```rust
pub struct LedgerEntry {
    pub id: String,
    pub entry_type: String,      // "income" | "expense" | "transfer"
    pub amount_sats: i64,        // amount in satoshis (Lightning denomination)
    pub amount_local: f64,       // local currency equivalent at time of entry
    pub currency: String,        // ISO 4217 currency code
    pub category: String,
    pub description: String,
    pub account_id: String,
    pub counterpart_account: Option<String>,   // double-entry counterpart
    pub cooperative_project_id: Option<String>, // links to wf-projects if cooperative expenditure
    pub tax_jurisdiction: Option<String>,       // ISO 3166-1 alpha-2
    pub timestamp: String,                      // ISO 8601
    pub receipt_hash: Option<String>,           // SHA-256 of receipt image if attached
}

pub struct TaxJurisdictionNym {
    pub jurisdiction: String,    // ISO 3166-1 alpha-2
    pub display_name: String,    // "Australia", "United Kingdom", etc.
    pub gst_vat_rate: f64,       // e.g. 0.10 for 10% GST
    pub cooperative_deductible: bool,
    pub expense_categories: Vec<String>,
}

pub struct ObligationMatrix {
    pub project_id: String,
    pub total_hours: f64,
    pub mu_units: u64,
    pub financial_outflow_sats: i64,
    pub fulfillment_pct: f64,    // 0.0–100.0
    pub as_of: String,           // ISO 8601
}
```

**Required WASM exports** (in `wasm.rs`):
```rust
#[wasm_bindgen]
pub fn validate_ledger_entry(entry_json: &str) -> bool
// Returns true if entry_type, amount_sats, currency, timestamp are all valid

#[wasm_bindgen]
pub fn compute_obligation_matrix(entries_json: &str, project_id: &str, rate: f64) -> JsValue
// entries_json = JSON array of LedgerEntry; returns ObligationMatrix as JsValue
```

Add `#[derive(Serialize, Deserialize, Debug, Clone)]` to all structs.

**Report format**: See "Reporting format" section below.

---

### G5 — JS: vault-pfm.js skeleton (PFM1)

**What**: Create `docs/js/vault-pfm.js` — the Personal Finance Management module.
Follow the exact same pattern as `docs/js/vault-projects.js` (encryption, IDB helpers, public API).

**Read first** (clone repo):
- `docs/js/vault-projects.js` — the pattern to copy exactly
- `docs/js/vault-idb.js` lines 1–87 — IDB constants and store opening (to understand the naming convention)

**Task**:
1. Implement double-entry ledger CRUD in `docs/js/vault-pfm.js`:
   - `initPfm(aesKey)` — set module key
   - `addLedgerEntry(entry)` → writes to `wf-ledger`
   - `getLedgerEntry(id)` → read + decrypt
   - `getAllEntries(options)` → all entries; `options.type` filter optional
   - `getEntriesByProject(projectId)` → cooperative expenditure entries
   - `getBalance()` → `{ totalIncomeSats, totalExpenseSats, netSats }`
   - `exportToOFX()` → string (basic OFX 2.0 format)
   - `exportToCSV()` → string

2. Add IDB v14 store to `docs/js/vault-idb.js`:
   - `const _ST_LEDGER = 'wf-ledger';`
   - `const _ST_PFM_CFG = 'wf-pfm-config';`
   - Bump version from 13 to 14
   - Add stores in `onupgradeneeded`

3. Expose `window.vaultPfm` with all public functions.

**Encryption**: Same `_encRecord`/`_decRecord` pattern. Use `_sEnc`/`_sDec` from `vault-crypto.js`.

**Report format**: See "Reporting format" section below.

---

### G6 — JS: vault-credentials.js skeleton (CV1–CV2)

**What**: Create `docs/js/vault-credentials.js` — the Credential Vault module.
Follow the exact same pattern as `docs/js/vault-projects.js`.

**Read first** (clone repo):
- `docs/js/vault-projects.js` — the pattern to follow

**Task**:
1. Credential CRUD in `docs/js/vault-credentials.js`:
   - `initCredentials(aesKey)` — set module key
   - `addCredential(vc)` → parse, encrypt, store in `wf-credentials`
     - `vc` is a W3C VC JSON-LD object (or simplified: `{id, type, issuer, issuanceDate, credentialSubject}`)
   - `getCredential(id)` → read + decrypt
   - `getAllCredentials()` → all credentials (Promise.allSettled for batch decrypt)
   - `deleteCredential(id)` → removes from IDB
   - `parseCredential(json)` → validates and normalises a VC JSON string into the internal format
   - `createVerifiablePresentation(credentialIds, holderDid)` → returns a W3C VP JSON object
     (unsigned placeholder — Ed25519 signing is handled by `vault-sanctuary-evidence.js`)
   - `deriveClaim(credential, attribute)` → returns `{ claim: attribute, value, issuer, issuanceDate }`

2. IDB (add to `vault-idb.js` if G5 hasn't already done v14):
   - `const _ST_CREDENTIALS = 'wf-credentials';`
   - Bump IDB to v14 (coordinate with G5; include all of G5's stores too)

3. Expose `window.vaultCredentials` with all public functions.

**Report format**: See "Reporting format" section below.

---

### G7 — PIA8: Consent gate in vault-p2p-sync.js

**What**: Add a `qp:hasConsentRelation` consent check before any GUN push in `vault-p2p-sync.js`.

**Read first** (clone repo):
- `docs/js/vault-p2p-sync.js` — the module to modify (focus on `pushProject` and `pushEquityShares`)
- `docs/js/vault-handshake.js` lines 1–50 — existing ODRL agreement handling pattern
- `docs/profiles/access-profiles.ttl` — `qp:hasConsentRelation` property definition

**Task**:
Add `checkProjectConsent(projectId)` to `vault-p2p-sync.js`:
- Reads `wf-agreements` IDB store for a record matching `{ projectId, type: 'sync_consent' }`
- Consent record format: `{ id, projectId, purpose, timeLimit (ISO8601), whatIsShared, grantedAt, revokedAt }`
- If `revokedAt` is set: return false (sync blocked)
- If no record or expired: return false (requires user to grant consent via UI)
- Returns boolean

Call `checkProjectConsent(projectId)` at the top of `pushProject()` and `pushEquityShares()`.
If false: `console.warn('[P2P] Sync blocked — no active consent for project:', projectId)` and return without pushing.

Add `grantSyncConsent(projectId, purpose, timeLimitIso, whatIsShared)` and `revokeSyncConsent(projectId)`:
- These write/update the consent record in `wf-agreements`
- `grantSyncConsent` writes `{ id: projectId + ':sync', projectId, type: 'sync_consent', purpose, timeLimit, whatIsShared, grantedAt: new Date().toISOString(), revokedAt: null }`
- `revokeSyncConsent` updates `revokedAt` on the existing record

**Important**: `wf-agreements` uses the same AES-GCM encryption as other stores, with the vault key.
The key is not accessible from `vault-p2p-sync.js` directly. Instead, expose:
- `window.vaultP2pSync.grantSyncConsent(...)` — delegates to `window.vaultHandshake.writeSyncConsent(...)` or directly to a new helper in `vault-idb.js`

**Simplest approach**: write the consent record as a plain JSON IDB entry (not encrypted) since consent records are not sensitive — they describe what data is shared, not the data itself. Use `_dbPut('wf-agreements', consentRecord)` without encryption.

**Report format**: See "Reporting format" section below.

---

### G8 — Research: Lightning + Nym integration spec

**What**: Produce a concise implementation spec (not code) for the Lightning + Nym payment rail.

**Context**:
- WellFair uses Lightning via LDK (Lightning Dev Kit) routed via Nym SOCKS5 proxy
- Three use cases: welfare payments to a vulnerable person (HCW), cooperative obligation micropayments (µ-units), and research bounties (DA)
- The vault's LDK node is initialised in `docs/js/vault-wallet.js` (currently a stub — `HCW-1/2 complete` means the init framework exists but Lightning node is not actually running)
- Nym SOCKS5: the Nym mixnet provides anonymous TCP transport; LDK connects to its Lightning peer via this proxy

**Produce**:
1. A list of the 5–8 Rust LDK types/traits needed in `wellfare-core/src/` for a minimal Tauri Nym-routed Lightning node (channel open, send payment, receive payment)
2. How the JS vault (`vault-wallet.js`) should invoke Tauri commands for each operation — method names, parameter types, return types
3. Any security considerations specific to the HCW founding use case (trafficking survivor — transaction-to-location linkage is a survival risk)
4. Recommended LDK version and any Nym Rust SDK version constraints

Output as a structured markdown document — no code, just spec. Max 600 words.

**Report format**: Paste the markdown doc directly (no code fences needed for spec text).

---

## Reporting format

When Grok completes a task, provide output in **exactly** this format so Claude can
integrate it without ambiguity:

```
## GROK OUTPUT — <Task ID> — <Task name>

### Files created
- `path/to/new_file.rs` — full file contents below

### Files modified
- `path/to/existing_file.js` — patch below

### New file: path/to/new_file.rs
```rust
[COMPLETE FILE CONTENTS — no omissions, no "// rest of file" shortcuts]
```

### Patch: path/to/existing_file.js
Add after line containing `// <some anchor text>`:
```javascript
[EXACT CODE TO INSERT]
```

### Cargo.toml additions (if any)
Under [dependencies]:
```
sha2 = "0.10"
base64 = "0.22"
```

### TODO.md tasks completed
- [x] R-CP1 ...
- [x] R-CP2 ...

### Notes for Claude
[Any integration warnings, things to watch out for, or decisions made]
```

**Rules for Grok output**:
1. **No pseudo-code** — every function must be complete and runnable
2. **No omissions** — never write `// ... existing code ...` or `// rest unchanged`
3. **Exact anchor text** — when modifying an existing file, quote a unique string from the file so Claude can locate the insertion point
4. **Rust**: include `use` statements; add `pub` appropriately; derive `Serialize, Deserialize` on all structs
5. **JS**: match the coding style of `vault-projects.js` exactly — `'use strict'` at top, function declarations (not arrow functions), JSDoc optional
6. **IDB version**: if bumping the IDB version, state the old version → new version explicitly

---

## Coordination notes

- **G5 and G6 both touch `vault-idb.js`** — coordinate which task goes first, or have Grok produce both IDB modifications in one combined patch for G5+G6 together
- **G1 and G2 both create new Rust files** — they can run fully in parallel, no conflicts
- **G3 modifies `access-profiles.ttl`** — run after confirming G3's shapes are not already present in the file (check the actual file first: it is 200+ lines of Turtle)
- **G7 modifies `vault-p2p-sync.js`** — do not run G7 at the same time as any session that is also modifying that file
- Claude will verify all Grok output in the browser before committing

---

## How to hand off a task to Grok

1. Pick a task from the list above (G1–G8)
2. Provide Grok with:
   - This entire file (`GROK_COLLABORATION.md`)
   - The specific source files listed under "Read first" for that task (paste their contents)
   - The relevant TODO.md entry for that task
3. Ask Grok to produce output in the "Reporting format" above
4. Paste Grok's output back to Claude Code to integrate and verify

---

## Tasks NOT suitable for Grok

- Browser verification (requires Chrome extension — only Claude can do this)
- Anything touching the vault PIN, AES key derivation, or Sanctuary Mode state machine
- WebRTC / Noise_XX / Nym SDK integration (too many moving parts, needs live browser)
- Tauri v2 mobile platform work (blocked; no app crate exists yet)
- Changes to `vault.html` HTML structure (complex inline JS/CSS interactions)
- Anything requiring access to the live IDB (only accessible in a real browser session)

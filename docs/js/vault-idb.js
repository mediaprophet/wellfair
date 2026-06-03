'use strict';

// ── IndexedDB — store names + helpers ────────────────────────────────────────

const _DB_NAME     = 'wf-vault';
const _ST_LOG      = 'wf-s';    // sanctuary entry log (obfuscated)
const _ST_CFG      = 'wf-sc';   // sanctuary config / canaries (obfuscated)
const _S_CANARY_OK = 'wf-sanctuary-ok';
const _D_CANARY_OK = 'wf-duress-ok';
const _ST_MEDS     = 'wf-meds'; // medication records
const _ST_MED_LOG  = 'wf-ml';   // adherence log
const _ST_PHARMA   = 'wf-pc';   // pharmacological LOD cache (7-day TTL)
const _ST_DIET_LOG = 'wf-dl';   // diet / substance log (Sprint 6)
// VC-7 — Verified Directory (added in v4)
const _ST_CONTACTS   = 'wf-contacts';      // encrypted contact records
const _ST_RELS       = 'wf-relationships'; // encrypted relationship edges
const _ST_AGREEMENTS = 'wf-agreements';    // encrypted signed usage agreements
// VC-12 — Background Job Scheduler (added in v5)
const _ST_JOBS       = 'wf-jobs';          // background job queue
// VC-13 — Event Log & Transcript (added in v6)
const _ST_EVENTS     = 'wf-events';        // call event log with hash chain
// WA-1 — Webizen Agent telemetry (added in v7)
const _ST_TELEMETRY  = 'wf-telemetry';     // session telemetry samples
// HCW-1 — Human-Centric Wallet (added in v8)
const _ST_WALLET     = 'wf-wallet';        // wallet provider metadata
const _ST_TXLOG      = 'wf-txlog';         // local transaction log (never transmitted)
// WASM bridge — biometric sensor data from Samsung Health CSV imports (added in v9)
const _ST_BIOMETRICS = 'wf-biometrics';    // weight, sleep, heart-rate, steps records
// QualiaDB — Persistent Lexicon dictionary (added in v10)
const _ST_LEXICON    = 'wf-lexicon';       // string <-> u64 mappings
// CP — Cooperative Projects (added in v11)
const _ST_PROJECTS      = 'wf-projects';      // cooperative project records
const _ST_CONTRIBUTIONS = 'wf-contributions'; // contribution log (Merkle chain)
const _ST_OBLIGATIONS   = 'wf-obligations';   // per-project µ-unit balances
// PIA6 — Personal Boundary Protection (added in v12)
const _ST_CALENDAR      = 'wf-calendar';      // personal calendar events (personalPriority flag)
// CP7 / PIA5 — Dynamic Equity Shares (added in v13)
const _ST_SHARES        = 'wf-shares';         // per-project qp:Slice equity allocations

function _openDB() {
  return new Promise((res, rej) => {
    const rq = indexedDB.open(_DB_NAME, 13);
    rq.onupgradeneeded = ev => {
      const db = ev.target.result;
      if (!db.objectStoreNames.contains(_ST_LOG))        db.createObjectStore(_ST_LOG,        { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_CFG))        db.createObjectStore(_ST_CFG,        { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_MEDS))       db.createObjectStore(_ST_MEDS,       { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_MED_LOG))    db.createObjectStore(_ST_MED_LOG,    { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_PHARMA))     db.createObjectStore(_ST_PHARMA,     { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_DIET_LOG))   db.createObjectStore(_ST_DIET_LOG,   { keyPath: 'id' });
      // v4 — VC-7 Verified Directory
      if (!db.objectStoreNames.contains(_ST_CONTACTS))   db.createObjectStore(_ST_CONTACTS,   { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_RELS))       db.createObjectStore(_ST_RELS,       { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_AGREEMENTS)) db.createObjectStore(_ST_AGREEMENTS, { keyPath: 'id' });
      // v5 — VC-12 Background Job Scheduler
      if (!db.objectStoreNames.contains(_ST_JOBS))       db.createObjectStore(_ST_JOBS,       { keyPath: 'id' });
      // v6 — VC-13 Event Log & Transcript
      if (!db.objectStoreNames.contains(_ST_EVENTS))     db.createObjectStore(_ST_EVENTS,     { keyPath: 'id' });
      // v7 — WA-1 Webizen Agent telemetry
      if (!db.objectStoreNames.contains(_ST_TELEMETRY))  db.createObjectStore(_ST_TELEMETRY,  { keyPath: 'id' });
      // v8 — HCW-1 Human-Centric Wallet
      if (!db.objectStoreNames.contains(_ST_WALLET))     db.createObjectStore(_ST_WALLET,     { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_TXLOG))      db.createObjectStore(_ST_TXLOG,      { keyPath: 'id' });
      // v9 — WASM bridge biometrics
      if (!db.objectStoreNames.contains(_ST_BIOMETRICS)) {
        const bs = db.createObjectStore(_ST_BIOMETRICS, { keyPath: 'id' });
        bs.createIndex('by_type', 'type', { unique: false });
        bs.createIndex('by_date', 'date', { unique: false });
      }
      // v10 — QualiaDB Lexicon
      if (!db.objectStoreNames.contains(_ST_LEXICON)) {
        const ls = db.createObjectStore(_ST_LEXICON, { keyPath: 'id' }); // id is the string
        ls.createIndex('by_uid', 'uid', { unique: true }); // uid is the u64 string representation
      }
      // v11 — Cooperative Projects
      if (!db.objectStoreNames.contains(_ST_PROJECTS))      db.createObjectStore(_ST_PROJECTS,      { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_CONTRIBUTIONS)) db.createObjectStore(_ST_CONTRIBUTIONS, { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_OBLIGATIONS))   db.createObjectStore(_ST_OBLIGATIONS,   { keyPath: 'id' });
      // v12 — PIA6 Personal Boundary Protection
      if (!db.objectStoreNames.contains(_ST_CALENDAR)) {
        const cal = db.createObjectStore(_ST_CALENDAR, { keyPath: 'id' });
        cal.createIndex('by_start', 'startIso', { unique: false });
      }
      // v13 — CP7/PIA5 Dynamic Equity Shares
      if (!db.objectStoreNames.contains(_ST_SHARES))
        db.createObjectStore(_ST_SHARES, { keyPath: 'id' });
    };
    rq.onsuccess = ev => res(ev.target.result);
    rq.onerror   = ev => rej(ev.target.error);
  });
}

async function _dbPut(store, record) {
  // CBOR-LD dual-write to QualiaStore.
  // Records an existence triple for this record. Full semantic content is
  // encoded separately per-module (e.g. exportProjectsToCborLdQuins) because
  // _dbPut receives the AES-GCM encrypted form {id,iv,ct} — plaintext is gone.
  // vault-cborld.js and QualiaStore must both be ready; failure is non-fatal.
  if (window.vaultCborLd && window.vaultWasm?.getQualiaStore()) {
    const qStore = window.vaultWasm.getQualiaStore();
    window.vaultCborLd.encodeIrisToCbor(
      `urn:wf:${store}:${record.id}`,
      'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
      `https://wellfare.social/ns/vault#StoredRecord`,
      `https://wellfare.social/ns/vault#store/${store}`,
    ).then(bytes => qStore.insert_from_cbor_ld(bytes))
     .catch(() => {});
  }
  const db = await _openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).put(record);
    tx.oncomplete = () => { db.close(); res(); };
    tx.onerror    = ev => { db.close(); rej(ev.target.error); };
  });
}

async function _dbGet(store, key) {
  const db = await _openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(store, 'readonly');
    const rq = tx.objectStore(store).get(key);
    rq.onsuccess = ev => { db.close(); res(ev.target.result); };
    rq.onerror   = ev => { db.close(); rej(ev.target.error); };
  });
}

async function _dbGetAll(store) {
  const db = await _openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(store, 'readonly');
    const rq = tx.objectStore(store).getAll();
    rq.onsuccess = ev => { db.close(); res(ev.target.result); };
    rq.onerror   = ev => { db.close(); rej(ev.target.error); };
  });
}

async function _dbDelete(store, key) {
  const db = await _openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).delete(key);
    tx.oncomplete = () => { db.close(); res(); };
    tx.onerror    = ev => { db.close(); rej(ev.target.error); };
  });
}

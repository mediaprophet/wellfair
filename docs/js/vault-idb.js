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

function _openDB() {
  return new Promise((res, rej) => {
    const rq = indexedDB.open(_DB_NAME, 3);
    rq.onupgradeneeded = ev => {
      const db = ev.target.result;
      if (!db.objectStoreNames.contains(_ST_LOG))      db.createObjectStore(_ST_LOG,      { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_CFG))      db.createObjectStore(_ST_CFG,      { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_MEDS))     db.createObjectStore(_ST_MEDS,     { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_MED_LOG))  db.createObjectStore(_ST_MED_LOG,  { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_PHARMA))   db.createObjectStore(_ST_PHARMA,   { keyPath: 'id' });
      if (!db.objectStoreNames.contains(_ST_DIET_LOG)) db.createObjectStore(_ST_DIET_LOG, { keyPath: 'id' });
    };
    rq.onsuccess = ev => res(ev.target.result);
    rq.onerror   = ev => rej(ev.target.error);
  });
}

async function _dbPut(store, record) {
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

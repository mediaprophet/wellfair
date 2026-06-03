'use strict';

// ── WASM bridge — wellfare-core ↔ vault.html ──────────────────────────────────
//
// Lazy-loads docs/pkg/wellfare_core.js (built by CI from wellfare-core/ Rust).
// Exposes CSV import, Turtle export, SPARQL query, and SHACL validation to the
// vault's JS layer.  All functions are no-ops (return null) if the WASM pkg is
// absent — the vault remains fully functional without it.

let _wasm = null;
let _loadPromise = null;
let _qualiaStore = null;

async function _load() {
    if (_wasm) return _wasm;
    if (_loadPromise) return _loadPromise;
    _loadPromise = (async () => {
        try {
            // Dynamic import — works with the ES module output of wasm-pack --target web
            const mod = await import('../pkg/wellfare_core.js');
            await mod.default();   // initialise WASM memory
            _wasm = mod;
            if (mod.QualiaStore) {
                _qualiaStore = new mod.QualiaStore();
                console.info('[vault-wasm] QualiaDB OPFS store initialized');
            }
            console.info('[vault-wasm] wellfare-core loaded');
        } catch (e) {
            console.warn('[vault-wasm] WASM pkg not available (run wasm-pack build to enable):', e.message);
            _wasm = null;
        }
        return _wasm;
    })();
    return _loadPromise;
}

// ── CSV import ────────────────────────────────────────────────────────────────

const _CSV_PARSE_FN = {
    weight:     w => w.parse_weight_csv_json,
    sleep:      w => w.parse_sleep_csv_json,
    heart_rate: w => w.parse_heart_rate_csv_json,
    steps:      w => w.parse_steps_csv_json,
};

const _CSV_TURTLE_FN = {
    weight:     w => w.weight_turtle_from_csv,
    sleep:      w => w.sleep_turtle_from_csv,
    heart_rate: w => w.heart_rate_turtle_from_csv,
    steps:      w => w.steps_turtle_from_csv,
};

/**
 * Parse a Samsung Health CSV export.
 * @param {'weight'|'sleep'|'heart_rate'|'steps'} type
 * @param {string} csvContent
 * @returns {Promise<object[]|null>}
 */
async function parseHealthCSV(type, csvContent) {
    const wasm = await _load();
    if (!wasm) return null;
    const fn = _CSV_PARSE_FN[type]?.(wasm);
    if (!fn) { console.warn('[vault-wasm] unknown CSV type:', type); return null; }
    return fn(csvContent);
}

/**
 * Parse a Samsung Health CSV and return Turtle RDF string directly.
 * @param {'weight'|'sleep'|'heart_rate'|'steps'} type
 * @param {string} csvContent
 * @returns {Promise<string|null>}
 */
async function csvToTurtle(type, csvContent) {
    const wasm = await _load();
    if (!wasm) return null;
    const fn = _CSV_TURTLE_FN[type]?.(wasm);
    if (!fn) return null;
    return fn(csvContent);
}

/**
 * Import a Samsung Health CSV into the vault's wf-biometrics IDB store.
 * Returns the number of records imported.
 * @param {'weight'|'sleep'|'heart_rate'|'steps'} type
 * @param {string} csvContent
 * @returns {Promise<number>}
 */
async function importCSVToVault(type, csvContent) {
    const records = await parseHealthCSV(type, csvContent);
    if (!records || !records.length) return 0;
    const mapped = records.map(r => ({
        id:    r.uuid || crypto.randomUUID(),
        type,
        date:  r.start_datetime || r.startDatetime || '',
        value: r.weight ?? r.heart_rate ?? r.count ?? r.sleep_duration ?? null,
        unit:  type === 'weight'     ? 'lb'
             : type === 'heart_rate' ? 'bpm'
             : type === 'steps'      ? 'steps'
             : 'min',
        raw: r,
    }));
    for (const rec of mapped) {
        await _dbPut(_ST_BIOMETRICS, rec);
    }
    return mapped.length;
}

// ── Vault data → Turtle export ────────────────────────────────────────────────

/**
 * Export all vault medication records as Turtle RDF.
 * @returns {Promise<string|null>}
 */
async function exportMedsToTurtle() {
    const wasm = await _load();
    if (!wasm) return null;
    const meds = await _dbGetAll(_ST_MEDS);
    return wasm.vault_meds_to_turtle(JSON.stringify(meds));
}

/**
 * Export all vault diet log entries as Turtle RDF.
 * @returns {Promise<string|null>}
 */
async function exportDietToTurtle() {
    const wasm = await _load();
    if (!wasm) return null;
    const entries = await _dbGetAll(_ST_DIET_LOG);
    return wasm.vault_diet_to_turtle(JSON.stringify(entries));
}

/**
 * Export all biometric records as Turtle RDF.
 * @returns {Promise<string|null>}
 */
async function exportBiometricsToTurtle() {
    const wasm = await _load();
    if (!wasm) return null;
    const records = await _dbGetAll(_ST_BIOMETRICS);
    return wasm.vault_biometrics_to_turtle(JSON.stringify(records));
}

/**
 * Export all vault health data (meds + diet + biometrics + cooperative projects) as a single Turtle document.
 * @returns {Promise<string|null>}
 */
async function exportVaultToTurtle() {
    const projectsTurtle = window.vaultProjects
        ? await window.vaultProjects.exportProjectsToTurtle().catch(() => null)
        : null;
    const [meds, diet, bio] = await Promise.all([
        exportMedsToTurtle(),
        exportDietToTurtle(),
        exportBiometricsToTurtle(),
    ]);
    if (!meds && !diet && !bio && !projectsTurtle) return null;
    // Merge: strip duplicate prefix blocks, concatenate bodies
    const stripPrefixes = s => s ? s.replace(/^@prefix[^\n]*\n/gm, '') : '';
    const first = meds || diet || bio || projectsTurtle || '';
    const prefixLines = first.match(/^@prefix[^\n]*\n/gm)?.join('') ?? '';
    return prefixLines + '\n' +
        stripPrefixes(meds) + stripPrefixes(diet) + stripPrefixes(bio) + stripPrefixes(projectsTurtle);
}

// ── SPARQL ────────────────────────────────────────────────────────────────────

/**
 * Run a SPARQL SELECT/ASK/CONSTRUCT query over a Turtle document.
 * @param {string} turtle
 * @param {string} sparql
 * @returns {Promise<object|null>}
 */
async function sparqlQuery(turtle, sparql) {
    const wasm = await _load();
    if (!wasm) return null;
    const store = new wasm.WasmHealthStore();
    store.load_turtle(turtle);
    const result = store.query(sparql);
    try { return JSON.parse(result); } catch { return result; }
}

/**
 * Run a SPARQL query over all exported vault data.
 * @param {string} sparql
 * @returns {Promise<object|null>}
 */
async function sparqlOverVault(sparql) {
    const turtle = await exportVaultToTurtle();
    if (!turtle) return null;
    return sparqlQuery(turtle, sparql);
}

// ── SHACL validation ──────────────────────────────────────────────────────────

/**
 * Validate a Turtle document against the built-in health shapes.
 * @param {string} turtle
 * @returns {Promise<{valid:boolean,checked:number,violations:object[]}|null>}
 */
async function validateHealthTurtle(turtle) {
    const wasm = await _load();
    if (!wasm) return null;
    try { return JSON.parse(wasm.validate_health_turtle(turtle)); } catch { return null; }
}

/**
 * Validate all exported vault data against health shapes.
 * @returns {Promise<{valid:boolean,checked:number,violations:object[]}|null>}
 */
async function validateVault() {
    const turtle = await exportVaultToTurtle();
    if (!turtle) return null;
    return validateHealthTurtle(turtle);
}

// ── Persistent Lexicon & JSON ↔ Quin Serialization ─────────────────────────────

/**
 * Basic string hashing as fallback. In a real environment, this uses FarmHash/xxHash64.
 * Generates a pseudo-60-bit integer (leaving top 4 bits free for datatypes).
 */
function _hashStringToBigInt(str) {
    let h = 0n;
    for (let i = 0; i < str.length; i++) {
        h = (h * 31n + BigInt(str.charCodeAt(i))) % 1152921504606846975n; // 2^60 - 1
    }
    return h || 1n;
}

class Lexicon {
    static async getId(str) {
        if (!str) return 0n;
        if (typeof str !== 'string') str = JSON.stringify(str);
        
        let record = await _dbGet(_ST_LEXICON, str);
        if (record) {
            return BigInt(record.uid);
        }
        
        const uid = _hashStringToBigInt(str);
        await _dbPut(_ST_LEXICON, { id: str, uid: uid.toString() });
        return uid;
    }

    static async getString(uidBigInt) {
        if (uidBigInt === 0n) return "";
        const uidStr = uidBigInt.toString();
        const db = await _openDB();
        return new Promise((res, rej) => {
            const tx = db.transaction(_ST_LEXICON, 'readonly');
            const idx = tx.objectStore(_ST_LEXICON).index('by_uid');
            const rq = idx.get(uidStr);
            rq.onsuccess = ev => { db.close(); res(ev.target.result ? ev.target.result.id : null); };
            rq.onerror   = ev => { db.close(); rej(ev.target.error); };
        });
    }
}

class JSONtoQuinSerializer {
    // Top 4 bits prefixes for the 64-bit Object vector
    static PREFIX_LEXICON = 0n << 60n; // 0x0
    static PREFIX_INT     = 1n << 60n; // 0x1
    static PREFIX_FLOAT   = 2n << 60n; // 0x2
    static PREFIX_BOOL    = 3n << 60n; // 0x3
    
    // Mask to extract the 60-bit payload
    static PAYLOAD_MASK   = 0x0FFFFFFFFFFFFFFFn;

    static async serialize(storeName, record) {
        const quins = [];
        const subjectId = record.id ? String(record.id) : crypto.randomUUID();
        const s = await Lexicon.getId(subjectId);
        const c = await Lexicon.getId(storeName); // Context is the store name
        const m = BigInt(Date.now()); // Metadata is the timestamp

        for (const [key, value] of Object.entries(record)) {
            if (key === 'id') continue;
            
            const p = await Lexicon.getId(key);
            let o = 0n;
            
            if (typeof value === 'boolean') {
                o = this.PREFIX_BOOL | (value ? 1n : 0n);
            } else if (typeof value === 'number') {
                if (Number.isInteger(value)) {
                    // Truncate to 60 bits and apply Int prefix
                    const v = BigInt(value) & this.PAYLOAD_MASK;
                    o = this.PREFIX_INT | v;
                } else {
                    // Simple deterministic representation of float (x1000) for POC
                    const v = BigInt(Math.floor(value * 1000)) & this.PAYLOAD_MASK;
                    o = this.PREFIX_FLOAT | v;
                }
            } else {
                const strVal = typeof value === 'string' ? value : JSON.stringify(value);
                const uid = await Lexicon.getId(strVal);
                o = this.PREFIX_LEXICON | uid;
            }

            quins.push({ s, p, o, c, m });
        }
        
        return quins;
    }
    
    static async deserialize(quins) {
        if (!quins || quins.length === 0) return null;
        
        const subjectStr = await Lexicon.getString(quins[0].s);
        const record = { id: subjectStr || quins[0].s.toString() };
        
        for (const q of quins) {
            const propStr = await Lexicon.getString(q.p);
            const key = propStr || q.p.toString();
            
            const prefix = q.o >> 60n;
            const payload = q.o & this.PAYLOAD_MASK;
            
            if (prefix === 0n) {
                // Lexicon string
                record[key] = (await Lexicon.getString(payload)) || payload.toString();
            } else if (prefix === 1n) {
                // Integer
                record[key] = Number(payload);
            } else if (prefix === 2n) {
                // Float (divided by 1000 from our POC packing)
                record[key] = Number(payload) / 1000.0;
            } else if (prefix === 3n) {
                // Boolean
                record[key] = payload === 1n;
            } else {
                // Fallback
                record[key] = payload.toString();
            }
        }
        return record;
    }
}

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultWasm = {
    load:                    _load,
    isAvailable:             () => !!_wasm,
    getQualiaStore:          () => _qualiaStore,
    // CSV import
    parseHealthCSV,
    csvToTurtle,
    importCSVToVault,
    // Turtle export
    exportMedsToTurtle,
    exportDietToTurtle,
    exportBiometricsToTurtle,
    exportVaultToTurtle,
    // SPARQL
    sparqlQuery,
    sparqlOverVault,
    // SHACL
    validateHealthTurtle,
    validateVault,
    // Serialization
    JSONtoQuinSerializer,
};

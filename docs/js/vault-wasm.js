'use strict';

// ── WASM bridge — wellfare-core ↔ vault.html ──────────────────────────────────
//
// Lazy-loads docs/pkg/wellfare_core.js (built by CI from wellfare-core/ Rust).
// Exposes CSV import, Turtle export, SPARQL query, and SHACL validation to the
// vault's JS layer.  All functions are no-ops (return null) if the WASM pkg is
// absent — the vault remains fully functional without it.

let _wasm = null;
let _loadPromise = null;

async function _load() {
    if (_wasm) return _wasm;
    if (_loadPromise) return _loadPromise;
    _loadPromise = (async () => {
        try {
            // Dynamic import — works with the ES module output of wasm-pack --target web
            const mod = await import('../pkg/wellfare_core.js');
            await mod.default();   // initialise WASM memory
            _wasm = mod;
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
 * Export all vault health data (meds + diet + biometrics) as a single Turtle document.
 * @returns {Promise<string|null>}
 */
async function exportVaultToTurtle() {
    const [meds, diet, bio] = await Promise.all([
        exportMedsToTurtle(),
        exportDietToTurtle(),
        exportBiometricsToTurtle(),
    ]);
    if (!meds && !diet && !bio) return null;
    // Merge: strip duplicate prefix blocks, concatenate bodies
    const stripPrefixes = s => s ? s.replace(/^@prefix[^\n]*\n/gm, '') : '';
    const wasm = await _load();
    const prefixBlock = meds || diet || bio || '';
    const prefixLines = prefixBlock.match(/^@prefix[^\n]*\n/gm)?.join('') ?? '';
    return prefixLines + '\n' + stripPrefixes(meds) + stripPrefixes(diet) + stripPrefixes(bio);
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

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultWasm = {
    load:                    _load,
    isAvailable:             () => !!_wasm,
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
};

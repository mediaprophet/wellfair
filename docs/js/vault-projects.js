'use strict';

// ── Cooperative Projects panel ─────────────────────────────────────────────────
// Depends on: vault-idb.js (_ST_PROJECTS, _ST_CONTRIBUTIONS, _ST_OBLIGATIONS,
//             _dbPut, _dbGet, _dbGetAll), vault-crypto.js (_sEnc, _sDec,
//             toB64, fromB64)
//
// All project, contribution, and obligation records are AES-256-GCM encrypted
// before IDB. The _dbPut calls also dual-write quints to QualiaStore (qualiaDB)
// via the existing dual-write hook in vault-idb.js.
//
// Module init: call initProjects(aesKey, didKey) when vault unlocks.

let _projKey = null;
let _projDid = null; // vault did:key string (for contribution authorship)

// ── Init ──────────────────────────────────────────────────────────────────────

function initProjects(aesKey, did) {
  _projKey = aesKey;
  _projDid = did || null;
}

function _requireKey() {
  if (!_projKey) throw new Error('[Projects] Key not set — call initProjects() after vault unlocks');
}

// ── Encryption helpers (same pattern as vault-directory.js) ───────────────────

async function _encRecord(plain) {
  const { iv, ct } = await _sEnc(_projKey, plain);
  return { id: plain.id, iv, ct };
}

async function _decRecord(stored) {
  return _sDec(_projKey, { iv: stored.iv, ct: stored.ct });
}

// ── Project CRUD ──────────────────────────────────────────────────────────────

async function addProject(name, description, ratePerHour, nodeId) {
  _requireKey();
  const record = {
    id:           crypto.randomUUID(),
    name:         name || 'Unnamed project',
    description:  description || '',
    ratePerHour:  typeof ratePerHour === 'number' ? ratePerHour : 1.0,
    nodeId:       nodeId || null,
    joined:       true, // adding a project implies you're in it
    joinedAt:     new Date().toISOString(),
    createdAt:    new Date().toISOString(),
  };
  await _dbPut(_ST_PROJECTS, await _encRecord(record));
  return record;
}

async function getProject(id) {
  _requireKey();
  const stored = await _dbGet(_ST_PROJECTS, id);
  return stored ? _decRecord(stored) : null;
}

async function getAllProjects() {
  _requireKey();
  const all = await _dbGetAll(_ST_PROJECTS);
  return Promise.all(all.map(r => _decRecord(r)));
}

async function updateProject(id, patch) {
  _requireKey();
  const proj = await getProject(id);
  if (!proj) throw new Error('[Projects] Not found: ' + id);
  Object.assign(proj, patch);
  await _dbPut(_ST_PROJECTS, await _encRecord(proj));
  return proj;
}

// ── Contribution log (Author-Scoped Merkle chain) ─────────────────────────────

// Hash = sha256( prevHashBytes ‖ UTF-8(JSON{hours,description,timestamp}) )
async function _merkleHash(prevHash, hours, description, timestamp) {
  const prevBytes = prevHash ? fromB64(prevHash) : new Uint8Array(32); // genesis: 32 zero bytes
  const payload   = new TextEncoder().encode(JSON.stringify({ hours, description, timestamp }));
  const combined  = new Uint8Array(prevBytes.length + payload.length);
  combined.set(prevBytes);
  combined.set(payload, prevBytes.length);
  const digest = await crypto.subtle.digest('SHA-256', combined);
  return toB64(new Uint8Array(digest));
}

// options.force = true skips the boundary-conflict gate (user has already confirmed)
async function logContribution(projectId, hours, description, options) {
  _requireKey();
  if (!projectId) throw new Error('[Projects] projectId required');
  if (!(hours > 0)) throw new Error('[Projects] hours must be a positive number');
  const timestamp  = new Date().toISOString();

  // PIA6 — boundary conflict check (skip when vault-calendar not yet loaded)
  if (!options?.force && window.vaultCalendar) {
    const now      = new Date(timestamp);
    const windowEnd = new Date(now.getTime() + hours * 3600000).toISOString();
    const conflicts = await window.vaultCalendar.checkBoundaryConflict(timestamp, windowEnd);
    if (conflicts.length > 0) {
      const err = new Error('[Projects] Boundary conflict: project work overlaps personal-priority calendar events');
      err.boundaryConflicts = conflicts;
      await window.vaultCalendar.logBoundaryConflict(
        `${timestamp}/${windowEnd}`, projectId, false,
      ).catch(() => {});
      throw err;
    }
  }
  // Get tail of the Merkle chain for this project
  const existing   = await getContributions(projectId);
  const prevHash   = existing.length > 0 ? existing[existing.length - 1].merkleHash : null;
  const merkleHash = await _merkleHash(prevHash, hours, description, timestamp);
  const record = {
    id:          crypto.randomUUID(),
    projectId,
    hours:       Number(hours),
    description: description || '',
    timestamp,
    prevHash:    prevHash || null,
    merkleHash,
    authorDid:   _projDid || null,
  };
  await _dbPut(_ST_CONTRIBUTIONS, await _encRecord(record));
  await _updateObligationBalance(projectId, Number(hours));
  return record;
}

async function getContributions(projectId) {
  _requireKey();
  const all       = await _dbGetAll(_ST_CONTRIBUTIONS);
  const decrypted = await Promise.all(all.map(r => _decRecord(r)));
  return decrypted
    .filter(r => r.projectId === projectId)
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

// ── Obligation (µ-unit) balance ───────────────────────────────────────────────

async function _updateObligationBalance(projectId, additionalHours) {
  const stored = await _dbGet(_ST_OBLIGATIONS, projectId);
  let bal;
  if (stored) {
    bal = await _decRecord(stored);
  } else {
    bal = { id: projectId, projectId, totalHours: 0, muUnits: 0, updatedAt: new Date().toISOString() };
  }
  const proj  = await getProject(projectId).catch(() => null);
  const rate  = proj?.ratePerHour ?? 1.0;
  bal.totalHours = Number((bal.totalHours + additionalHours).toFixed(2));
  bal.muUnits    = Math.round(bal.totalHours * rate * 1000); // µ-units = hours × rate × 1000
  bal.updatedAt  = new Date().toISOString();
  await _dbPut(_ST_OBLIGATIONS, await _encRecord(bal));
  return bal;
}

async function getObligationBalance(projectId) {
  _requireKey();
  const stored = await _dbGet(_ST_OBLIGATIONS, projectId);
  if (!stored) return { projectId, totalHours: 0, muUnits: 0 };
  return _decRecord(stored);
}

async function getAllObligations() {
  _requireKey();
  const all = await _dbGetAll(_ST_OBLIGATIONS);
  return Promise.all(all.map(r => _decRecord(r)));
}

// ── CBOR-LD export (feeds QualiaStore quint engine via vault-cborld.js) ──────
// Encodes all plaintext project/contribution/obligation records as CBOR-LD
// quints and inserts them into the in-memory QualiaStore.
// Call after vault unlock (alongside exportProjectsToTurtle → WasmHealthStore).
// Returns { projects, contributions, obligations } counts inserted.

async function exportProjectsToCborLdQuins() {
  _requireKey();
  if (!window.vaultCborLd || !window.vaultWasm?.getQualiaStore()) {
    return { projects: 0, contributions: 0, obligations: 0 };
  }
  const [projects, contribsRaw, obligations] = await Promise.all([
    getAllProjects(),
    _dbGetAll(_ST_CONTRIBUTIONS).then(all => Promise.all(all.map(r => _decRecord(r)))),
    getAllObligations(),
  ]);
  const counts = { projects: 0, contributions: 0, obligations: 0 };
  for (const p of projects) {
    counts.projects += await window.vaultCborLd.insertRecordToQualiaStore(_ST_PROJECTS, p);
  }
  for (const c of contribsRaw) {
    counts.contributions += await window.vaultCborLd.insertRecordToQualiaStore(_ST_CONTRIBUTIONS, c);
  }
  for (const o of obligations) {
    counts.obligations += await window.vaultCborLd.insertRecordToQualiaStore(_ST_OBLIGATIONS, o);
  }
  return counts;
}

// ── Turtle RDF export (feeds WasmHealthStore SPARQL via vault-wasm.js) ────────

async function exportProjectsToTurtle() {
  _requireKey();
  const [projects, contribsRaw, obligations] = await Promise.all([
    getAllProjects(),
    _dbGetAll(_ST_CONTRIBUTIONS).then(all => Promise.all(all.map(r => _decRecord(r)))),
    getAllObligations(),
  ]);

  const lines = [
    '@prefix wf:      <https://wellfare.social/ns/vault#> .',
    '@prefix qp:      <https://qualia.id/ns/> .',
    '@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .',
    '@prefix dcterms: <http://purl.org/dc/terms/> .',
    '',
  ];

  const _esc  = s => JSON.stringify(String(s ?? ''));
  const _uri  = id => `<urn:wf:project:${id}>`;
  const _curi = id => `<urn:wf:contribution:${id}>`;

  for (const p of projects) {
    lines.push(`${_uri(p.id)} a wf:CooperativeProject, qp:Workspace ;`);
    lines.push(`  wf:name ${_esc(p.name)} ;`);
    lines.push(`  wf:description ${_esc(p.description)} ;`);
    lines.push(`  wf:ratePerHour "${p.ratePerHour}"^^xsd:decimal ;`);
    lines.push(`  wf:joined "${p.joined}"^^xsd:boolean ;`);
    if (p.joinedAt)  lines.push(`  wf:joinedAt "${p.joinedAt}"^^xsd:dateTime ;`);
    lines.push(`  dcterms:created "${p.createdAt}"^^xsd:dateTime .`);
    lines.push('');
  }

  for (const c of contribsRaw) {
    lines.push(`${_curi(c.id)} a wf:ContributionRecord, qp:ProvenanceCommit ;`);
    lines.push(`  wf:project ${_uri(c.projectId)} ;`);
    lines.push(`  wf:hours "${c.hours}"^^xsd:decimal ;`);
    lines.push(`  wf:description ${_esc(c.description)} ;`);
    lines.push(`  wf:merkleHash "${c.merkleHash}" ;`);
    if (c.prevHash)  lines.push(`  wf:prevHash "${c.prevHash}" ;`);
    if (c.prevHash)  lines.push(`  qp:antecedent "${c.prevHash}" ;`);
    if (c.authorDid) lines.push(`  wf:authorDid "${c.authorDid}" ;`);
    if (c.authorDid) lines.push(`  qp:authorNym "${c.authorDid}" ;`);
    lines.push(`  dcterms:created "${c.timestamp}"^^xsd:dateTime .`);
    lines.push('');
  }

  for (const o of obligations) {
    lines.push(`<urn:wf:obligation:${o.projectId}> a wf:ObligationBalance, qp:EffortObligation ;`);
    lines.push(`  wf:project ${_uri(o.projectId)} ;`);
    lines.push(`  wf:totalHours "${o.totalHours}"^^xsd:decimal ;`);
    lines.push(`  wf:muUnits "${o.muUnits}"^^xsd:integer ;`);
    lines.push(`  qp:amount "${o.muUnits}"^^xsd:decimal ;`);
    lines.push(`  dcterms:modified "${o.updatedAt}"^^xsd:dateTime .`);
    lines.push('');
  }

  return lines.join('\n');
}

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultProjects = {
  initProjects,
  addProject, getProject, getAllProjects, updateProject,
  logContribution, getContributions,
  getObligationBalance, getAllObligations,
  exportProjectsToTurtle,       // → WasmHealthStore (oxigraph/SPARQL)
  exportProjectsToCborLdQuins,  // → QualiaStore (quint engine / Sentinel)
  // PIA6: force a contribution past a boundary conflict (call only after user opt-in)
  logContributionForced: (projectId, hours, description) =>
    logContribution(projectId, hours, description, { force: true }),
};

'use strict';

// ── Four-tier P2P sync layer (CP4 + CBOR7) ────────────────────────────────────
//
// Tier 1 — Nym (nymAdapter):        obligation commits in Sanctuary Mode
// Tier 2 — Gun+WebRTC:              project/obligation state (CBOR-LD wire, CBOR7)
// Tier 3 — N-Quads (.nq) download:  git-compatible offline ledger (Tier 3)
// Tier 4 — WebTorrent:              large artifact distribution (stub; PIA7)
//
// CRDT merge rules:
//   Obligations (µ-units): max per project (Merkle chain is append-only so the
//     highest seen µ-unit count wins; applied via vaultProjects.mergeObligationBalance)
//   Project metadata:      last-write-wins by updatedAt/ts timestamp
//   qp:Slice equity shares: last-write-wins per contributor slot (PIA5 stub)
//
// Wire format (CBOR7 — GUN Tier 2):
//   GUN stores a JSON record with:
//     v:           sync version string "1"
//     ts:          ISO timestamp
//     did:         sender did:key
//     projectId:   target project UUID
//     lex:         JSON-stringified {iri: number} mini-lexicon for this payload
//     obligations: base64 blob of concatenated CBOR-LD quint arrays
//     projects:    base64 blob of concatenated CBOR-LD quint arrays
//   The receiver merges the mini-lexicon into the local Lexicon before decoding.
//
// Depends on (loaded before this module in vault.html):
//   vault-crypto.js    — toB64, fromB64
//   vault-nym.js       — nymAdapter
//   vault-cborld.js    — window.vaultCborLd
//   vault-projects.js  — window.vaultProjects
//   gun.js CDN         — Gun global (already loaded in vault.html)
//
// Init:   vaultP2pSync.init(config)
// Push:   vaultP2pSync.pushProject(projectId)
// Pull:   vaultP2pSync.pullProject(projectId)
// Tier 3: vaultP2pSync.downloadNQuads()

const _GUN_NS    = 'wf-v1-project';
const _GUN_RELAYS_DEFAULT = [
  'https://gun.eco/gun',
  'https://relay.peer.ooo/gun',
];
const _SYNC_VER = '1';

let _gun    = null;
let _cfg    = null; // set by init()

// ── Init ─────────────────────────────────────────────────────────────────────

function init(config = {}) {
  _cfg = {
    gunRelays:    config.gunRelays    ?? _GUN_RELAYS_DEFAULT,
    nymAddress:   config.nymAddress   ?? null,
    projectIds:   config.projectIds   ?? [],
    did:          config.did          ?? null,
    sanctuaryMode: config.sanctuaryMode ?? false,
  };
  if (!_cfg.sanctuaryMode && typeof Gun !== 'undefined') {
    _gun = Gun(_cfg.gunRelays);
  }
}

// ── CBOR-LD wire format helpers ───────────────────────────────────────────────

// Build a {iri: number} mini-lexicon covering all IDs used in the given quints.
// Sent alongside the quints so the receiver can seed its local Lexicon.
function _buildMiniLex(quints) {
  const cbl = window.vaultCborLd;
  if (!cbl) return {};
  const lex = {};
  for (const bytes of quints) {
    try {
      for (const uid of cbl.decodeCborToIds(bytes)) {
        const iri = cbl.idToIri(uid);
        if (iri) lex[iri] = Number(uid);
      }
    } catch (_) {}
  }
  return lex;
}

// Merge a received mini-lexicon: ensure every IRI has a local Lexicon entry.
async function _mergeMiniLex(lexObj) {
  const cbl = window.vaultCborLd;
  if (!cbl || !lexObj) return;
  for (const iri of Object.keys(lexObj)) await cbl.iriToId(iri).catch(() => {});
}

// Pack an array of Uint8Array quints into a single base64 blob.
function _quintsToB64(quints) {
  let total = 0;
  for (const q of quints) total += q.length;
  const buf = new Uint8Array(total);
  let off = 0;
  for (const q of quints) { buf.set(q, off); off += q.length; }
  return toB64(buf);
}

// Unpack a base64 blob into individual CBOR quints.
// Each quint starts with a CBOR array header byte: 0x84 (4-el) or 0x85 (5-el).
function _b64ToQuints(b64) {
  const buf = fromB64(b64);
  const quints = [];
  let i = 0;
  while (i < buf.length) {
    const h = buf[i];
    if ((h & 0xE0) !== 0x80) break;
    const count = h & 0x1F;
    let j = i + 1;
    for (let k = 0; k < count; k++) {
      const add = buf[j] & 0x1F;
      if      (add <= 23) j += 1;
      else if (add === 24) j += 2;
      else if (add === 25) j += 3;
      else if (add === 26) j += 5;
      else if (add === 27) j += 9;
      else break;
    }
    quints.push(buf.slice(i, j));
    i = j;
  }
  return quints;
}

// Encode an obligation balance as CBOR-LD quints.
async function _obligToQuints(ob) {
  const cbl = window.vaultCborLd;
  if (!cbl) return [];
  return cbl.recordToCborLdQuins('wf-obligations', {
    id:         ob.projectId,
    projectId:  ob.projectId,
    totalHours: ob.totalHours,
    muUnits:    ob.muUnits,
    updatedAt:  ob.updatedAt ?? new Date().toISOString(),
    authorDid:  _cfg?.did ?? '',
  });
}

// Encode a project metadata record as CBOR-LD quints.
async function _projToQuints(p) {
  const cbl = window.vaultCborLd;
  if (!cbl) return [];
  return cbl.recordToCborLdQuins('wf-projects', {
    id:          p.id,
    name:        p.name,
    description: p.description,
    ratePerHour: p.ratePerHour,
    updatedAt:   p.updatedAt ?? p.createdAt ?? new Date().toISOString(),
  });
}

// ── Tier 1: Nym ───────────────────────────────────────────────────────────────

async function _pushViaNym(projectId, obligQuints, projQuints) {
  if (!nymAdapter.isActive() || !_cfg?.nymAddress) return false;
  await nymAdapter.send(_cfg.nymAddress, {
    type:        'wf-sync-v1',
    v:           _SYNC_VER,
    ts:          new Date().toISOString(),
    did:         _cfg.did,
    projectId,
    lex:         _buildMiniLex([...obligQuints, ...projQuints]),
    obligations: _quintsToB64(obligQuints),
    projects:    _quintsToB64(projQuints),
  });
  return true;
}

// ── Tier 2: GUN (CBOR7 wire format) ──────────────────────────────────────────

async function _pushViaGun(projectId, obligQuints, projQuints) {
  if (!_gun) return false;
  _gun.get(_GUN_NS).get(projectId).put({
    v:           _SYNC_VER,
    ts:          new Date().toISOString(),
    did:         _cfg?.did ?? '',
    projectId,
    lex:         JSON.stringify(_buildMiniLex([...obligQuints, ...projQuints])),
    obligations: _quintsToB64(obligQuints),
    projects:    _quintsToB64(projQuints),
  });
  return true;
}

function _gunRead(projectId) {
  if (!_gun) return Promise.resolve(null);
  return new Promise(resolve => {
    const t = setTimeout(() => resolve(null), 5000);
    _gun.get(_GUN_NS).get(projectId).once(data => {
      clearTimeout(t);
      resolve(data?.v === _SYNC_VER ? data : null);
    });
  });
}

// ── CRDT merge ────────────────────────────────────────────────────────────────

// Obligations: accept remote if its µ-unit count is higher (append-only Merkle).
async function _mergeObligation(projectId, remoteMuUnits) {
  const projects = window.vaultProjects;
  if (!projects) return;
  const local = await projects.getObligationBalance(projectId);
  if (remoteMuUnits > (local.muUnits ?? 0)) {
    await projects.mergeObligationBalance(projectId, remoteMuUnits);
  }
}

// Project metadata: last-write-wins by updatedAt timestamp.
async function _mergeProjMeta(projectId, meta) {
  const projects = window.vaultProjects;
  if (!projects) return;
  const local    = await projects.getProject(projectId).catch(() => null);
  const remoteTs = meta.updatedAt ?? meta.ts ?? '';
  const localTs  = local?.updatedAt ?? local?.createdAt ?? '';
  if (!local) {
    await projects.addProject(meta.name ?? '', meta.description ?? '',
      parseFloat(meta.ratePerHour) || 1.0).catch(() => {});
    return;
  }
  if (remoteTs > localTs) {
    const patch = {};
    if (meta.name        !== undefined) patch.name        = meta.name;
    if (meta.description !== undefined) patch.description = meta.description;
    if (meta.ratePerHour !== undefined) patch.ratePerHour = parseFloat(meta.ratePerHour) || 1.0;
    if (Object.keys(patch).length) {
      await projects.updateProject(projectId, { ...patch, updatedAt: remoteTs }).catch(() => {});
    }
  }
}

// ── Tier 3: N-Quads download ─────────────────────────────────────────────────

async function exportNQuads() {
  const projects = window.vaultProjects;
  if (!projects) return '';
  const [projs, obs] = await Promise.all([
    projects.getAllProjects(),
    projects.getAllObligations(),
  ]);
  const WF  = 'https://wellfare.social/ns/vault#';
  const QP  = 'https://qualia.id/ns/';
  const XSD = 'http://www.w3.org/2001/XMLSchema#';
  const CTX = '<urn:wf:sync:nquads>';
  const _u  = id  => `<urn:wf:project:${id}>`;
  const _ob = id  => `<urn:wf:obligation:${id}>`;
  const _s  = str => `"${String(str ?? '').replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\n/g,'\\n')}"`;
  const lines = [];
  for (const p of projs) {
    lines.push(`${_u(p.id)} <${WF}name> ${_s(p.name)} ${CTX} .`);
    lines.push(`${_u(p.id)} <${WF}description> ${_s(p.description)} ${CTX} .`);
    lines.push(`${_u(p.id)} <${WF}ratePerHour> "${p.ratePerHour}"^^<${XSD}decimal> ${CTX} .`);
    lines.push(`${_u(p.id)} <${WF}joined> "${p.joined}"^^<${XSD}boolean> ${CTX} .`);
    if (p.joinedAt)  lines.push(`${_u(p.id)} <${WF}joinedAt> "${p.joinedAt}"^^<${XSD}dateTime> ${CTX} .`);
    if (p.createdAt) lines.push(`${_u(p.id)} <${WF}createdAt> "${p.createdAt}"^^<${XSD}dateTime> ${CTX} .`);
  }
  for (const o of obs) {
    lines.push(`${_ob(o.projectId)} <${WF}muUnits> "${o.muUnits}"^^<${XSD}integer> ${CTX} .`);
    lines.push(`${_ob(o.projectId)} <${WF}totalHours> "${o.totalHours}"^^<${XSD}decimal> ${CTX} .`);
    lines.push(`${_ob(o.projectId)} <${QP}amount> "${o.muUnits}"^^<${XSD}decimal> ${CTX} .`);
    lines.push(`${_ob(o.projectId)} <${WF}updatedAt> "${o.updatedAt}"^^<${XSD}dateTime> ${CTX} .`);
  }
  return lines.join('\n') + '\n';
}

async function downloadNQuads() {
  const nq   = await exportNQuads();
  const blob = new Blob([nq], { type: 'application/n-quads' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `wf-ledger-${new Date().toISOString().slice(0, 10)}.nq`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── Tier 4: WebTorrent stub ───────────────────────────────────────────────────

function seedWebTorrent() {
  // Implemented by vault-webtorrent.js (PIA7); that module registers as Tier 4.
  console.warn('[P2P] WebTorrent Tier 4 not yet available — see PIA7');
  return Promise.resolve(null);
}

// ── Push / pull ───────────────────────────────────────────────────────────────

// Push a single project's obligation + metadata to peers.
//   Sanctuary Mode → Tier 1 (Nym) only.
//   Nym active + nymAddress set → Tier 1 first, Tier 2 as fallback.
//   Default → Tier 2 (GUN).
async function pushProject(projectId) {
  if (!_cfg) throw new Error('[P2P] Call init() first');
  const projects = window.vaultProjects;
  if (!projects) return;
  const [proj, ob] = await Promise.all([
    projects.getProject(projectId),
    projects.getObligationBalance(projectId),
  ]);
  if (!proj) throw new Error('[P2P] Unknown project: ' + projectId);
  const [obligQ, projQ] = await Promise.all([_obligToQuints(ob), _projToQuints(proj)]);
  if (_cfg.sanctuaryMode) { await _pushViaNym(projectId, obligQ, projQ); return; }
  const sentNym = await _pushViaNym(projectId, obligQ, projQ);
  if (!sentNym) await _pushViaGun(projectId, obligQ, projQ);
}

// Pull and merge a single project from GUN Tier 2.
// No-op in Sanctuary Mode.
async function pullProject(projectId) {
  if (!_cfg || _cfg.sanctuaryMode) return;
  const remote = await _gunRead(projectId);
  if (!remote) return;
  const cbl = window.vaultCborLd;
  if (!cbl) return;
  await _mergeMiniLex(JSON.parse(remote.lex || '{}'));
  // Merge obligations
  if (remote.obligations) {
    for (const q of _b64ToQuints(remote.obligations)) {
      try {
        const iris = cbl.decodeCborToIris(q);
        // iris[1] is predicate; iris[2] is object (urn:wf:lit:<value>)
        if (iris[1]?.endsWith('muUnits')) {
          const v = Number(iris[2]?.replace('urn:wf:lit:', ''));
          if (!isNaN(v)) await _mergeObligation(projectId, v);
        }
      } catch (_) {}
    }
  }
  // Merge project metadata
  if (remote.projects) {
    const meta = {};
    for (const q of _b64ToQuints(remote.projects)) {
      try {
        const iris = cbl.decodeCborToIris(q);
        const key  = iris[1]?.replace('https://wellfare.social/ns/vault#', '');
        const val  = iris[2]?.replace('urn:wf:lit:', '');
        if (key && val) meta[key] = val;
      } catch (_) {}
    }
    if (Object.keys(meta).length) await _mergeProjMeta(projectId, meta);
  }
}

async function pushAll() {
  if (!_cfg) return;
  for (const id of _cfg.projectIds) {
    await pushProject(id).catch(e => console.warn('[P2P] Push failed:', id, e));
  }
}

async function pullAll() {
  if (!_cfg) return;
  for (const id of _cfg.projectIds) await pullProject(id);
}

// ── PIA5 — qp:Slice equity shares (stub, extended by CP7) ────────────────────

async function pushEquityShares(projectId, shares) {
  if (!_gun || _cfg?.sanctuaryMode) return;
  _gun.get(_GUN_NS).get(projectId + ':equity').put({
    v: _SYNC_VER, ts: new Date().toISOString(),
    did: _cfg?.did ?? '', projectId,
    shares: JSON.stringify(shares ?? {}),
  });
}

async function pullEquityShares(projectId) {
  if (!_gun || _cfg?.sanctuaryMode) return null;
  return new Promise(resolve => {
    const t = setTimeout(() => resolve(null), 5000);
    _gun.get(_GUN_NS).get(projectId + ':equity').once(data => {
      clearTimeout(t);
      if (!data || data.v !== _SYNC_VER) return resolve(null);
      try { resolve(JSON.parse(data.shares)); } catch (_) { resolve(null); }
    });
  });
}

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultP2pSync = {
  init,
  pushProject, pullProject,
  pushAll,     pullAll,
  exportNQuads, downloadNQuads,
  seedWebTorrent,
  pushEquityShares, pullEquityShares, // PIA5 hooks (extended by CP7)
};

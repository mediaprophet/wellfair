'use strict';

// ── Evidentiary Export, Verifiable Presentations, OpenTimestamps anchoring ────
// Depends on: vault-idb.js, vault-crypto.js, vault-did.js, vault-sanctuary-pins.js

let _evEntries = [];

// ── Evidentiary Export ────────────────────────────────────────────────────────

async function refreshEvidentiary() {
  if (!sanctuaryKey) return;
  const container = document.getElementById('ev-entry-list');
  _evEntries = []; container.innerHTML = '';
  try {
    const all  = await _dbGetAll(_ST_LOG);
    const rows = all.filter(r => !r.type || r.type === 'assertion' || r.type === 'hypothesis');
    rows.sort((a, b) => b.seq - a.seq);
    if (!rows.length) {
      container.innerHTML = '<div style="color:var(--dim);font-size:.78rem">No sanctuary entries to export.</div>';
      return;
    }
    for (const r of rows) {
      try {
        const plain = await _sDec(sanctuaryKey, r.enc);
        _evEntries.push({ plain, r });
        const row = document.createElement('div');
        row.className = 'ev-row';
        const ts   = plain.created_at ? new Date(plain.created_at).toLocaleString() : '';
        const type = plain.type === 'assertion' ? '◉ Assertion' : '◎ Hypothesis';
        row.innerHTML =
          `<input type="checkbox" id="ev-${r.id}" value="${r.id}" />` +
          `<div><div class="ev-row-text">${plain.content.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>` +
          `<div class="ev-row-meta">${type} · ${ts} · <span style="font-family:monospace">${r.commitment.slice(0,12)}…</span></div>` +
          _otsAnchorRow(r) + `</div>`;
        container.appendChild(row);
      } catch (_) {}
    }
  } catch (e) {
    container.innerHTML = `<div style="color:var(--red);font-size:.78rem">Error: ${e.message}</div>`;
  }
}

async function generateVP() {
  if (!sanctuaryKey || typeof vaultDidKey === 'undefined' || !vaultDidKey) return;
  const status = document.getElementById('ev-status');
  const output = document.getElementById('ev-vp-output');
  status.textContent = 'Generating…'; status.style.color = 'var(--dim)'; output.innerHTML = '';

  const selected = _evEntries.filter(({ r }) => document.getElementById('ev-' + r.id)?.checked);
  if (!selected.length) { status.textContent = 'Select at least one entry.'; status.style.color = 'var(--red)'; return; }

  try {
    const now = new Date().toISOString();
    const vpPayload = JSON.stringify({
      '@context': ['https://www.w3.org/2018/credentials/v1'],
      type:       ['VerifiablePresentation'],
      id:         'urn:uuid:' + crypto.randomUUID(),
      holder:     vaultDidKey.did, issued: now,
      verifiableCredential: selected.map(({ plain, r }) => ({
        '@context':  ['https://www.w3.org/2018/credentials/v1', 'https://wellfare.social/ns/vault#'],
        type:        ['VerifiableCredential', 'SanctuaryEntry'],
        id:          'urn:uuid:' + crypto.randomUUID(),
        issuer:      vaultDidKey.did, issuanceDate: plain.created_at,
        credentialSubject: { type: plain.type, content: plain.content,
          commitment: r.commitment, nonce: r.nonce },
      })),
    });

    const sigRaw = new Uint8Array(await crypto.subtle.sign(
      { name: 'Ed25519' }, vaultDidKey.privateKey, new TextEncoder().encode(vpPayload)
    ));
    const vp = { presentation: JSON.parse(vpPayload),
      proof: { type: 'Ed25519Signature2020', created: now,
        verificationMethod: vaultDidKey.did + '#key-1',
        proofPurpose: 'authentication', proofValue: toB64(sigRaw) } };
    const vpJson = JSON.stringify(vp, null, 2);
    output.innerHTML = `<div class="vp-json">${vpJson.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>`;
    status.textContent = `✓ VP generated · ${selected.length} entr${selected.length===1?'y':'ies'} · signed by vault`;
    status.style.color = 'var(--green)';
    const blob = new Blob([vpJson], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'),
      { href: url, download: 'wellfair-vp-' + now.slice(0,10) + '.json', style: 'display:none' });
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 3000);
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

async function exportCommitmentManifest() {
  if (!sanctuaryKey) return;
  const status = document.getElementById('dlt-status');
  status.textContent = 'Exporting…'; status.style.color = 'var(--dim)';
  try {
    const all = await _dbGetAll(_ST_LOG);
    const manifest = {
      version: 1, exported_at: new Date().toISOString(),
      vault_did: typeof vaultDidKey !== 'undefined' && vaultDidKey ? vaultDidKey.did : null,
      commitments: all.filter(r => r.commitment).map(r =>
        ({ id: r.id, type: r.type || 'entry', seq: r.seq, nonce: r.nonce, commitment: r.commitment })),
      note: 'Publish each commitment hash to a public DLT to establish asymmetric provenance anchors.',
    };
    const json = JSON.stringify(manifest, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
      href: url, download: 'wellfair-commitments-' + new Date().toISOString().slice(0,10) + '.json',
      style: 'display:none' });
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 3000);
    status.textContent = `✓ Exported ${manifest.commitments.length} commitment${manifest.commitments.length===1?'':'s'}`;
    status.style.color = 'var(--green)';
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

// ── OpenTimestamps — Bitcoin commitment anchoring ─────────────────────────────

const _OTS_CALENDARS = [
  'https://alice.btc.calendar.opentimestamps.org',
  'https://bob.btc.calendar.opentimestamps.org',
  'https://finney.calendar.opentimestamps.org',
];
const _OTS_MAGIC = new Uint8Array([
  0x00,0x4f,0x70,0x65,0x6e,0x54,0x69,0x6d,0x65,0x73,0x74,0x61,0x6d,0x70,0x73,
  0x00,0x00,0x50,0x72,0x6f,0x6f,0x66,0x00,0xbf,0x89,0xe2,0xe8,0x84,0xe8,0x92,0x94,
]);

function _otsAnchorRow(r) {
  const s = r.ots_status;
  const esc = id => id.replace(/'/g, "\\'");
  if (s === 'confirmed') {
    const d = r.ots_confirmed ? new Date(r.ots_confirmed).toLocaleDateString() : '';
    return `<div class="ev-row-anchor"><span style="color:#4ade80">✓ Confirmed on Bitcoin${d?' · '+d:''}</span>` +
      `<button class="btn-ots" onclick="otsDownload('${esc(r.id)}')">Download .ots proof</button></div>`;
  }
  if (s === 'pending') {
    const d = r.ots_submitted ? new Date(r.ots_submitted).toLocaleDateString() : '';
    return `<div class="ev-row-anchor"><span>⏳ Pending Bitcoin block${d?' · submitted '+d:''}</span>` +
      `<button class="btn-ots" onclick="otsDownload('${esc(r.id)}')">Download receipt</button></div>`;
  }
  return `<div class="ev-row-anchor">` +
    `<button class="btn-ots" id="ots-btn-${r.id}" onclick="otsAnchorEntry('${esc(r.id)}')">Anchor to Bitcoin</button>` +
    `<span id="ots-msg-${r.id}"></span></div>`;
}

async function otsAnchorEntry(id) {
  const btn = document.getElementById('ots-btn-' + id);
  const msg = document.getElementById('ots-msg-' + id);
  if (btn) { btn.disabled = true; btn.textContent = 'Publishing…'; }
  try {
    const rec = await _dbGet(_ST_LOG, id);
    if (!rec?.commitment) throw new Error('No commitment hash');
    const hashBytes = fromB64(rec.commitment);
    let receipt = null, calendar = null;
    for (const cal of _OTS_CALENDARS) {
      try {
        const r = await fetch(cal + '/digest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/octet-stream', Accept: 'application/octet-stream' },
          body: hashBytes,
        });
        if (!r.ok) continue;
        receipt = new Uint8Array(await r.arrayBuffer()); calendar = cal; break;
      } catch (_) {}
    }
    if (!receipt) throw new Error('All calendar servers unreachable');
    await _dbPut(_ST_LOG, { ...rec, ots_status: 'pending', ots_receipt: toB64(receipt),
      ots_calendar: calendar, ots_submitted: new Date().toISOString() });
    setTimeout(refreshEvidentiary, 300);
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = 'Anchor to Bitcoin'; }
    if (msg) { msg.textContent = 'Error: ' + e.message; msg.style.color = 'var(--red)'; }
  }
}

async function _otsUpgradeOne(rec) {
  if (rec.ots_status !== 'pending' || !rec.ots_calendar || !rec.commitment) return false;
  const hex = Array.from(fromB64(rec.commitment)).map(b => b.toString(16).padStart(2,'0')).join('');
  try {
    const r = await fetch(`${rec.ots_calendar}/timestamp/${hex}`, { headers: { Accept: 'application/octet-stream' } });
    if (!r.ok) return false;
    const upgraded = new Uint8Array(await r.arrayBuffer());
    await _dbPut(_ST_LOG, { ...rec, ots_status: 'confirmed',
      ots_receipt: toB64(upgraded), ots_confirmed: new Date().toISOString() });
    return true;
  } catch (_) { return false; }
}

async function otsUpgradeAll() {
  const all     = await _dbGetAll(_ST_LOG);
  const pending = all.filter(r => r.ots_status === 'pending');
  if (!pending.length) return;
  let upgraded = 0;
  for (const r of pending) { if (await _otsUpgradeOne(r)) upgraded++; }
  if (upgraded) refreshEvidentiary();
}

async function otsDownload(id) {
  const rec = await _dbGet(_ST_LOG, id);
  if (!rec?.ots_receipt || !rec.commitment) return;
  const hash = fromB64(rec.commitment);
  const body = fromB64(rec.ots_receipt);
  const file = new Uint8Array(_OTS_MAGIC.length + 1 + 1 + 32 + body.length);
  let o = 0;
  file.set(_OTS_MAGIC, o); o += _OTS_MAGIC.length;
  file[o++] = 0x01; file[o++] = 0x08;
  file.set(hash, o); o += 32; file.set(body, o);
  const blob = new Blob([file], { type: 'application/octet-stream' });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement('a'),
    { href: url, download: `wellfair-${id.slice(0,8)}.ots`, style: 'display:none' });
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 3000);
}

'use strict';

// ── Sanctuary workspace — log, tripwire, synthesis engine ─────────────────────
// Depends on: vault-idb.js, vault-crypto.js, vault-sanctuary-pins.js

async function _enterSanctuaryMode(key) {
  sanctuaryKey = key; sanctuaryActive = true;
  document.body.classList.add('sanctuary-active');
  showStep('step-sanctuary');
  await Promise.all([
    refreshSanctuaryLog(), refreshTripwireFeed(),
    refreshEvidentiary(),  _loadSentinelRules(),
  ]);
  otsUpgradeAll().catch(() => {});
}

function exitSanctuaryMode() {
  sanctuaryActive = false; sanctuaryKey = null;
  document.body.classList.remove('sanctuary-active');
  showStep('step-owner');
}

// ── Unvarnished Log ───────────────────────────────────────────────────────────

async function refreshSanctuaryLog() {
  const container = document.getElementById('sanctuary-log-list');
  if (!container || !sanctuaryKey) return;
  container.innerHTML = '<div style="color:var(--dim);font-size:.78rem;padding:.3rem 0">Loading…</div>';
  try {
    const all     = await _dbGetAll(_ST_LOG);
    const records = all.filter(r => !r.type || r.type === 'assertion' || r.type === 'hypothesis');
    records.sort((a, b) => b.seq - a.seq);
    if (!records.length) {
      container.innerHTML = '<div style="color:var(--dim);font-size:.78rem;padding:.3rem 0">No entries yet.</div>';
      return;
    }
    container.innerHTML = '';
    for (const r of records) {
      try {
        const plain = await _sDec(sanctuaryKey, r.enc);
        const el    = document.createElement('div');
        el.className = 'sanctuary-entry';
        const ts = plain.created_at ? new Date(plain.created_at).toLocaleString() : '';
        el.innerHTML =
          `<div class="se-type ${plain.type}">${plain.type === 'assertion' ? '◉ Assertion' : '◎ Hypothesis'}</div>` +
          `<div class="se-content">${plain.content.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>` +
          `<div class="se-meta">${ts} · anchor: <span class="se-anchor">${r.commitment.slice(0,16)}…</span></div>`;
        container.appendChild(el);
      } catch (_) {}
    }
  } catch (e) {
    container.innerHTML = `<div style="color:var(--red);font-size:.78rem">Load error: ${e.message}</div>`;
  }
}

async function logSanctuaryEntry() {
  if (!sanctuaryKey) return;
  const type    = document.getElementById('sanctuary-entry-type').value;
  const content = document.getElementById('sanctuary-entry-content').value.trim();
  const status  = document.getElementById('sanctuary-entry-status');
  if (!content) { status.textContent = 'Write something first.'; status.style.color = 'var(--red)'; return; }
  status.textContent = 'Encrypting & anchoring…'; status.style.color = 'var(--dim)';
  try {
    const plain      = { type, content, created_at: new Date().toISOString() };
    const entryBytes = new TextEncoder().encode(JSON.stringify(plain));
    const { nonce, commitment } = await computeCommitment(entryBytes);
    const rec = { id: crypto.randomUUID(), seq: Date.now(), type,
      enc: await _sEnc(sanctuaryKey, plain), nonce, commitment };
    await _dbPut(_ST_LOG, rec);
    otsAnchorEntry(rec.id).catch(() => {});
    document.getElementById('sanctuary-entry-content').value = '';
    status.textContent = '✓ Logged · anchor: ' + commitment.slice(0, 16) + '…';
    status.style.color = 'var(--green)';
    console.info('[WellFair] Commitment ready to publish:', commitment);
    await refreshSanctuaryLog();
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

async function saveDuressContacts() {
  if (!sanctuaryKey) return;
  const c1     = document.getElementById('duress-contact-1').value.trim();
  const c2     = document.getElementById('duress-contact-2').value.trim();
  const dPin   = document.getElementById('duress-pin-update').value;
  const status = document.getElementById('duress-contacts-status');
  if (!dPin) { status.textContent = 'Enter your Duress PIN to save.'; status.style.color = 'var(--red)'; return; }
  status.textContent = 'Saving…'; status.style.color = 'var(--dim)';
  try {
    const dKey     = await deriveVaultKey(dPin, _DURS_SALT);
    const cfg      = (await _dbGet(_ST_CFG, 'wf-cfg')) || { id: 'wf-cfg' };
    const contacts = [{ address: c1 }, { address: c2 }].filter(c => c.address);
    cfg.d_contacts = await _sEnc(dKey, contacts);
    await _dbPut(_ST_CFG, cfg);
    status.textContent = '✓ Contacts saved'; status.style.color = 'var(--green)';
    document.getElementById('duress-pin-update').value = '';
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

// ── Tripwire Dashboard ────────────────────────────────────────────────────────

const _TW_CATS = {
  prescription: 'Prescription conflict', coercion: 'Coercive control',
  false_claim:  'False claim / fabrication', legal: 'Legal / administrative',
  surveillance: 'Surveillance / digital',   other: 'Other',
};

async function logTripwire() {
  if (!sanctuaryKey) return;
  const category = document.getElementById('tw-category').value;
  const trigger  = document.getElementById('tw-trigger').value.trim();
  const status   = document.getElementById('tw-status');
  if (!trigger) { status.textContent = 'Describe the event.'; status.style.color = 'var(--red)'; return; }
  status.textContent = 'Encrypting & anchoring…'; status.style.color = 'var(--dim)';
  try {
    const plain      = { category, trigger, resolution: 'pending', created_at: new Date().toISOString() };
    const entryBytes = new TextEncoder().encode(JSON.stringify(plain));
    const { nonce, commitment } = await computeCommitment(entryBytes);
    await _dbPut(_ST_LOG, { id: crypto.randomUUID(), seq: Date.now(), type: 'tripwire',
      enc: await _sEnc(sanctuaryKey, plain), nonce, commitment });
    document.getElementById('tw-trigger').value = '';
    status.textContent = '✓ Logged · anchor: ' + commitment.slice(0, 16) + '…';
    status.style.color = 'var(--green)';
    await refreshTripwireFeed();
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

async function refreshTripwireFeed() {
  if (!sanctuaryKey) return;
  const container = document.getElementById('tw-feed');
  try {
    const all     = await _dbGetAll(_ST_LOG);
    const records = all.filter(r => r.type === 'tripwire');
    records.sort((a, b) => b.seq - a.seq);
    if (!records.length) {
      container.innerHTML = '<div style="color:var(--dim);font-size:.78rem;padding:.3rem 0">No collisions logged.</div>';
      return;
    }
    container.innerHTML = '';
    for (const r of records) {
      try {
        const plain = await _sDec(sanctuaryKey, r.enc);
        const el = document.createElement('div');
        el.className = 'tw-entry';
        const ts  = plain.created_at ? new Date(plain.created_at).toLocaleString() : '';
        const cat = _TW_CATS[plain.category] || plain.category;
        const res = plain.resolution || 'pending';
        el.innerHTML =
          `<div class="tw-cat">${cat}</div>` +
          `<div class="tw-content">${plain.trigger.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>` +
          `<div class="tw-meta">${ts} · <span style="font-family:monospace">${r.commitment.slice(0,16)}…</span></div>` +
          `<div class="tw-resolve">` +
            `<button class="${res==='pending'?'res-active':''}"  onclick="resolveTripwire('${r.id}','pending')">Keep hidden</button>` +
            `<button class="${res==='revealed'?'res-active':''}" onclick="resolveTripwire('${r.id}','revealed')">Reveal temporarily</button>` +
            `<button class="${res==='exported'?'res-active':''}" onclick="resolveTripwire('${r.id}','exported')">Export to doctor</button>` +
          `</div>`;
        container.appendChild(el);
      } catch (_) {}
    }
  } catch (e) {
    container.innerHTML = `<div style="color:var(--red);font-size:.78rem">Load error: ${e.message}</div>`;
  }
}

async function resolveTripwire(id, resolution) {
  if (!sanctuaryKey) return;
  try {
    const r = await _dbGet(_ST_LOG, id);
    if (!r) return;
    const plain = await _sDec(sanctuaryKey, r.enc);
    await _dbPut(_ST_LOG, { ...r, enc: await _sEnc(sanctuaryKey, { ...plain, resolution }) });
    await refreshTripwireFeed();
  } catch (_) {}
}

// ── Synthesis Engine ──────────────────────────────────────────────────────────

async function runContradictionAudit() {
  if (!sanctuaryKey) return;
  const claim  = document.getElementById('synth-claim').value.trim();
  const status = document.getElementById('synth-status');
  const report = document.getElementById('synth-report');
  if (!claim) { status.textContent = 'Enter a claim to audit.'; status.style.color = 'var(--red)'; return; }
  status.textContent = 'Scanning immutable record…'; status.style.color = 'var(--dim)';
  report.innerHTML = '';
  const claimWords = claim.toLowerCase().split(/\W+/).filter(w => w.length > 3);
  try {
    const all  = await _dbGetAll(_ST_LOG);
    const hits = [];
    for (const r of all) {
      if (r.type === 'tripwire') continue;
      try {
        const plain = await _sDec(sanctuaryKey, r.enc);
        if (!plain.content) continue;
        const entryWords = plain.content.toLowerCase().split(/\W+/);
        const overlap    = claimWords.filter(w => entryWords.some(e => e.includes(w) || w.includes(e)));
        if (overlap.length > 0) hits.push({ plain, r, overlap });
      } catch (_) {}
    }
    if (!hits.length) { status.textContent = 'No direct contradictions found.'; status.style.color = 'var(--dim)'; return; }
    status.textContent = `Incoherence Report — ${hits.length} contradicting entr${hits.length === 1 ? 'y' : 'ies'}`;
    status.style.color = 'var(--yellow)';
    for (const { plain, r, overlap } of hits) {
      const el = document.createElement('div');
      el.className = 'synth-hit';
      const ts   = plain.created_at ? new Date(plain.created_at).toLocaleString() : '';
      const type = plain.type === 'assertion' ? '◉' : '◎';
      el.innerHTML =
        `<div class="sh-content">${type} ${plain.content.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>` +
        `<div class="sh-meta">${ts} · overlap: ${overlap.join(', ')} · <span style="font-family:monospace">${r.commitment.slice(0,16)}…</span></div>`;
      report.appendChild(el);
    }
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

async function saveSentinelRules() {
  if (!sanctuaryKey) return;
  const rules  = document.getElementById('sentinel-rules').value.trim();
  const status = document.getElementById('sentinel-status');
  status.textContent = 'Saving…'; status.style.color = 'var(--dim)';
  try {
    const cfg = (await _dbGet(_ST_CFG, 'wf-cfg')) || {};
    await _dbPut(_ST_CFG, { ...cfg, id: 'wf-cfg', sentinel_rules: await _sEnc(sanctuaryKey, rules) });
    status.textContent = '✓ Ruleset saved'; status.style.color = 'var(--green)';
  } catch (e) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
}

async function _loadSentinelRules() {
  if (!sanctuaryKey) return;
  try {
    const cfg = await _dbGet(_ST_CFG, 'wf-cfg');
    if (cfg && cfg.sentinel_rules)
      document.getElementById('sentinel-rules').value = await _sDec(sanctuaryKey, cfg.sentinel_rules);
  } catch (_) {}
}

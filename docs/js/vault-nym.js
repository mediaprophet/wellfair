'use strict';

// ── Nym mixnet — configuration, adapter, DMS, anonymous notification ─────────
// Run docs/nym-test.html to validate the SDK, then set NYM_SDK_URL.
// Requires SharedArrayBuffer → needs crossOriginIsolated (provided by sw.js).

const NYM_SDK_URL    = null; // TODO: set after validating with docs/nym-test.html
const NYM_API_URL    = 'https://validator.nymtech.net/api';
const NYM_FRAG_MAX   = 28 * 1024;
const NYM_SURB_TARGET = 20;
const NYM_SURB_ATTACH = 3;
const NYM_SURB_LOW    = 5;

let nymClient  = null;
let surbBudget = 0;

const _nymReassembly = new Map();
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of _nymReassembly) if (v.expires < now) _nymReassembly.delete(k);
}, 10000);

async function initNym() {
  if (!NYM_SDK_URL || !crossOriginIsolated) return;
  try {
    const { createNymMixnetClient } = await import(NYM_SDK_URL);
    nymClient = await createNymMixnetClient();
    await nymClient.connect(NYM_API_URL);
    surbBudget = 0;
    await _nymReplenish();
  } catch (e) {
    console.warn('[WellFair] Nym init failed:', e.message);
  }
}

const nymAdapter = {
  isActive() { return nymClient !== null; },
  async send(recipientAddress, payload) {
    if (!nymClient) throw new Error('Nym not initialised');
    const json = JSON.stringify(payload);
    const enc  = new TextEncoder().encode(json);
    if (enc.length <= NYM_FRAG_MAX) {
      const surbs = surbBudget >= NYM_SURB_ATTACH ? NYM_SURB_ATTACH : 0;
      await nymClient.send({ payload: { message: json, mimeType: 'application/json' },
        recipient: recipientAddress, replySurbs: surbs });
      surbBudget -= surbs;
      if (surbBudget < NYM_SURB_LOW) _nymReplenish();
    } else {
      const msgId = crypto.randomUUID();
      let offset = 0; let idx = 0;
      while (offset < enc.length) {
        const chunk = enc.slice(offset, offset + NYM_FRAG_MAX);
        offset += NYM_FRAG_MAX;
        const isLast = offset >= enc.length;
        const frag = JSON.stringify({ msg_id: msgId, fragment_idx: idx++, is_last: isLast,
          data: toB64(chunk) });
        await nymClient.send({ payload: { message: frag, mimeType: 'application/json' },
          recipient: recipientAddress });
      }
    }
  }
};

async function _nymReplenish() {
  if (!nymClient || surbBudget >= NYM_SURB_TARGET) return;
  try {
    await nymClient.generateSurbs(NYM_SURB_TARGET - surbBudget);
    surbBudget = NYM_SURB_TARGET;
  } catch (_) {}
}

function _nymReceive(raw) {
  try {
    const msg = JSON.parse(typeof raw === 'string' ? raw : new TextDecoder().decode(raw));
    if (msg.msg_id !== undefined) {
      const key = msg.msg_id + ':' + msg.fragment_idx;
      _nymReassembly.set(key, { ...msg, expires: Date.now() + 30000 });
      if (msg.is_last) {
        const frags = [];
        for (let i = 0; ; i++) {
          const f = _nymReassembly.get(msg.msg_id + ':' + i);
          if (!f) break;
          frags.push(fromB64(f.data));
          _nymReassembly.delete(msg.msg_id + ':' + i);
          if (f.is_last) break;
        }
        const merged = new Uint8Array(frags.reduce((n, a) => n + a.length, 0));
        let off = 0;
        for (const f of frags) { merged.set(f, off); off += f.length; }
        return JSON.parse(new TextDecoder().decode(merged));
      }
      return null;
    }
    return msg;
  } catch (_) { return null; }
}

// ── Dead Man's Switch ─────────────────────────────────────────────────────────

let dmsTimer       = null;
let dmsLastCheckin = null;

function toggleDmsPanel() {
  const b = document.getElementById('dms-body');
  b.style.display = b.style.display === 'none' ? 'block' : 'none';
}

function dmsCheckin() {
  dmsLastCheckin = Date.now();
  const interval = parseInt(document.getElementById('dms-interval').value, 10);
  clearTimeout(dmsTimer);
  dmsTimer = setTimeout(async () => {
    try { await dmsFire(false); } catch (e) { console.error('[WellFair] DMS fire failed:', e); }
  }, interval);
  const st = document.getElementById('dms-status');
  st.textContent = 'Checked in ' + new Date().toLocaleTimeString() +
    ' — next due ' + new Date(Date.now() + interval).toLocaleString();
  st.style.color = 'var(--green)';
}

async function dmsTestFire() {
  const st = document.getElementById('dms-status');
  st.textContent = 'Sending test alert…'; st.style.color = 'var(--dim)';
  try {
    await dmsFire(true);
    st.textContent = 'Test alert sent ✓'; st.style.color = 'var(--green)';
  } catch (e) {
    st.textContent = 'Failed: ' + e.message; st.style.color = 'var(--red)';
  }
}

async function dmsFire(isTest = false) {
  const addr1 = document.getElementById('dms-trustee-1').value.trim();
  const addr2 = document.getElementById('dms-trustee-2').value.trim();
  const addrs = [addr1, addr2].filter(Boolean);
  if (addrs.length === 0) throw new Error('No trustee Nym addresses configured');
  const payload = {
    type:         isTest ? 'dms_test' : 'dms_alert',
    vault_did:    typeof vaultDidKey !== 'undefined' && vaultDidKey ? vaultDidKey.did : 'unknown',
    issued_at:    new Date().toISOString(),
    last_checkin: dmsLastCheckin ? new Date(dmsLastCheckin).toISOString() : null,
  };
  for (const addr of addrs) await nymAdapter.send(addr, payload);
}

// ── Anonymous notification ────────────────────────────────────────────────────

function toggleAnonPanel() {
  const b = document.getElementById('anon-body');
  b.style.display = b.style.display === 'none' ? 'block' : 'none';
}

async function sendAnonMessage() {
  const recipient = document.getElementById('anon-recipient').value.trim();
  const message   = document.getElementById('anon-message').value.trim();
  const st        = document.getElementById('anon-status');
  if (!recipient || !message) {
    st.textContent = 'Recipient address and message are required';
    st.style.color = 'var(--yellow)'; return;
  }
  if (!nymClient) {
    st.textContent = 'Nym unavailable — set NYM_SDK_URL in vault-nym.js and reload';
    st.style.color = 'var(--red)'; return;
  }
  st.textContent = 'Sending…'; st.style.color = 'var(--dim)';
  try {
    await nymAdapter.send(recipient, { type: 'anon_message', message, sent_at: new Date().toISOString() });
    st.textContent = 'Sent anonymously ✓'; st.style.color = 'var(--green)';
    document.getElementById('anon-message').value = '';
  } catch (e) {
    st.textContent = 'Failed: ' + e.message; st.style.color = 'var(--red)';
  }
}

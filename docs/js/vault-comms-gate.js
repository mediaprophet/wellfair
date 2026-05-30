'use strict';

// ── Inbound Caller Gating — dual Nym+Gun transport, VC verification ───────────
// Depends on: vault-idb.js, vault-crypto.js (fromB64), vault-nym.js
//             (nymClient, _nymReceive), vault-directory.js (lookupByDid,
//             getRelationship)
//
// Call startGate() in openOwnerWorkspace(); stopGate() in lockVault().
//
// Expected call_request message shape:
//   { type:"call_request", callerDid, callerVc, sessionId, gunNode }
//   callerVc (optional) = base64(JSON.stringify({ sig, data }))
//   Absence of callerVc → hold for manual verification

// ── Constants ─────────────────────────────────────────────────────────────────

const GATE_RELAYS = ['https://gun.eco/gun', 'https://relay.peer.ooo/gun'];
const GATE_GUN_NS = 'wf-v1-signal';

// ── Module state ──────────────────────────────────────────────────────────────

let _gateGun     = null;
let _gateRunning = false;
let _activeCall  = null; // { contact | null, msg }

// ── Public API ────────────────────────────────────────────────────────────────

function startGate() {
  if (_gateRunning) return;
  _gateRunning = true;
  _startGunListener();
  _startNymListener();
}

function stopGate() {
  _gateRunning = false;
  _gateGun     = null;
  _gateHideOverlays();
}

// ── Gun transport ─────────────────────────────────────────────────────────────

function _startGunListener() {
  if (typeof Gun === 'undefined') return;
  const did = _gateVaultDid();
  if (!did) { setTimeout(_startGunListener, 600); return; }
  _gateGun = Gun(GATE_RELAYS);
  _gateGun.get(GATE_GUN_NS).get('calls').get(did).on(async (data) => {
    if (!_gateRunning || !data || data.type !== 'call_request') return;
    await _verifyInbound(data);
  });
}

// ── Nym transport ─────────────────────────────────────────────────────────────

function _startNymListener() {
  if (!nymClient) return;
  nymClient.onmessage = async (raw) => {
    if (!_gateRunning) return;
    const msg = _nymReceive(raw);
    if (msg && msg.type === 'call_request') await _verifyInbound(msg);
  };
}

// ── Inbound verification ─────────────────────────────────────────────────────

async function _verifyInbound(msg) {
  try {
    const contact = await lookupByDid(msg.callerDid);

    if (contact) {
      // Known caller: verify VC sig if present; check agreement
      if (msg.callerVc) {
        const sigOk = await _verifyCallerVc(msg.callerDid, msg.callerVc);
        if (!sigOk) { _rejectSilently(msg, 'invalid_sig'); return; }
      }
      const rel = await getRelationship(contact.id);
      if (rel && rel.agreement) {
        _ringDevice(contact, msg);
      } else {
        // Has contact entry but no signed agreement — hold for verification
        _holdForVerification(msg, contact);
      }
    } else {
      // Unknown caller: verify VC if present; either way hold for verification
      if (msg.callerVc) {
        const sigOk = await _verifyCallerVc(msg.callerDid, msg.callerVc);
        if (!sigOk) { _rejectSilently(msg, 'invalid_sig'); return; }
      }
      _holdForVerification(msg, null);
    }
  } catch (e) {
    console.warn('[Gate] _verifyInbound error:', e.message);
  }
}

async function _verifyCallerVc(did, vcB64) {
  if (!vcB64 || !did) return false;
  try {
    const { sig, data } = JSON.parse(atob(vcB64));
    const pubKey = await _gateImportPubKeyFromDid(did);
    const bytes  = new TextEncoder().encode(
      typeof data === 'string' ? data : JSON.stringify(data));
    return crypto.subtle.verify('Ed25519', pubKey, fromB64(sig), bytes);
  } catch (_) { return false; }
}

async function _gateImportPubKeyFromDid(did) {
  const b58 = did.replace(/^did:key:z/, '');
  const raw  = _gateB58Decode(b58);
  return crypto.subtle.importKey('raw', raw.slice(2),
    { name: 'Ed25519' }, false, ['verify']);
}

function _gateB58Decode(s) {
  const ALPHA = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  let n = BigInt(0);
  for (const c of s) n = n * BigInt(58) + BigInt(ALPHA.indexOf(c));
  const hex = n.toString(16).padStart(Math.ceil(s.length * 733 / 1000) * 2, '0');
  return new Uint8Array(hex.match(/.{2}/g).map(b => parseInt(b, 16)));
}

function _rejectSilently(msg, reason) {
  console.debug('[Gate] Rejected silently:', reason, msg.callerDid);
}

// ── Ring overlay ─────────────────────────────────────────────────────────────

function _ringDevice(contact, msg) {
  _activeCall = { contact, msg };
  document.getElementById('gate-ring-name').textContent = contact.name;
  document.getElementById('gate-ring-rel').textContent  =
    'Incoming call · verified contact';
  document.getElementById('gate-ring-did').textContent  =
    msg.callerDid ? msg.callerDid.slice(0, 28) + '…' : '—';
  document.getElementById('gate-ring-overlay').style.display = 'flex';
}

function _holdForVerification(msg, contact) {
  _activeCall = { contact, msg };
  document.getElementById('gate-verify-name').textContent =
    contact ? contact.name : 'Unknown caller';
  document.getElementById('gate-verify-did').textContent  =
    msg.callerDid || '—';
  document.getElementById('gate-verify-overlay').style.display = 'flex';
}

function _gateHideOverlays() {
  const r = document.getElementById('gate-ring-overlay');
  const v = document.getElementById('gate-verify-overlay');
  if (r) r.style.display = 'none';
  if (v) v.style.display = 'none';
  _activeCall = null;
}

// ── User actions (bound in vault.html) ───────────────────────────────────────

function gateAcceptCall() {
  if (!_activeCall) return;
  console.info('[Gate] Call accepted, caller:', _activeCall.msg.callerDid);
  _gateHideOverlays();
  // VC-10 will call answerCall(_activeCall.msg.sessionId, _activeCall.msg.gunNode)
}

function gateRejectCall() {
  if (!_activeCall) return;
  console.info('[Gate] Call rejected, caller:', _activeCall.msg.callerDid);
  _gateHideOverlays();
}

function gateVerifyAccept() {
  if (!_activeCall) return;
  const { contact, msg } = _activeCall;
  console.info('[Gate] Manual verify+accept, caller:', msg.callerDid);
  _gateHideOverlays();
  _ringDevice(contact || { name: 'Unverified caller', notes: '' }, msg);
}

function gateVerifyReject() {
  if (!_activeCall) return;
  console.info('[Gate] Manual verify+reject, caller:', _activeCall.msg.callerDid);
  _gateHideOverlays();
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function _gateVaultDid() {
  return typeof vaultDidKey !== 'undefined' && vaultDidKey
    ? vaultDidKey.did : null;
}

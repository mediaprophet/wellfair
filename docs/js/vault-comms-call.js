'use strict';

// ── Hypermedia Voice/Video — WebRTC call session management ───────────────────
// Depends on: vault-idb.js, vault-crypto.js (toB64, fromB64),
//             vault-did.js (generateDidKey), vault-directory.js (getRelationship),
//             vault-nym.js (nymAdapter)
//
// Topologies:
//   A: vault-owner ↔ vault-owner (both use phone+laptop)
//   B: vault-owner generates call link → guest/WellFair user opens join.html
//
// Script tag must come after vault-directory.js in vault.html.

// ── Constants ─────────────────────────────────────────────────────────────────

const CALL_GUN_RELAYS = ['https://gun.eco/gun', 'https://relay.peer.ooo/gun'];
const CALL_GUN_NS     = 'wf-v1-signal';
const CALL_ICE_CFG    = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

// ── Session state ─────────────────────────────────────────────────────────────

let _callGun       = null;
let _callPc        = null;
let _callDc        = null; // in-call data-sharing DataChannel
let _callStream    = null;
let _callSessionId = null;
let _callGunNode   = null;
const _guestTokens = new Map(); // sessionId → token (hex)

// ── Public API ────────────────────────────────────────────────────────────────

// Initiate a call to a contact. Returns { sessionId, callLink }.
async function startCall(contactId) {
  await endCall(); // clean up any existing call

  const sessionId = crypto.randomUUID();
  _callSessionId  = sessionId;

  _callGun     = _callGunInstance();
  _callGunNode = _callGun.get(CALL_GUN_NS).get('sessions').get(sessionId);

  _callStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
  _callPc     = new RTCPeerConnection(CALL_ICE_CFG);
  _callStream.getTracks().forEach(t => _callPc.addTrack(t, _callStream));

  _callPc.onicecandidate = ({ candidate }) => {
    if (candidate) _callGunNode.get('ice_a').put(JSON.stringify(candidate));
  };

  _callPc.ontrack = (ev) => _callRenderRemote(ev.streams[0]);

  // Data-sharing channel — offer side creates it; answer side receives via ondatachannel
  _callDc = _callPc.createDataChannel('wf-data');
  _callSetupDc(_callDc);

  const offer = await _callPc.createOffer();
  await _callPc.setLocalDescription(offer);
  _callGunNode.put({ offer: JSON.stringify(offer), callerDid: _callVaultDid() });

  // Listen for answer from callee
  _callGunNode.on(async (data) => {
    if (!data || !data.answer || !_callPc) return;
    if (_callPc.signalingState === 'stable') return;
    try {
      await _callPc.setRemoteDescription(JSON.parse(data.answer));
    } catch (_) {}
  });

  _callGunNode.get('ice_b').on((raw) => {
    if (!raw || !_callPc) return;
    try { _callPc.addIceCandidate(JSON.parse(raw)); } catch (_) {}
  });

  const callLink = generateGuestLink(sessionId);
  _callNotifyUI({ event: 'call.started', sessionId, callLink });
  return { sessionId, callLink };
}

// Answer an inbound call (called after user accepts the gate ring overlay).
// sessionId and gunNode come from the call_request message.
async function answerCall(sessionId, gunNode) {
  await endCall();

  _callSessionId = sessionId;
  _callGun       = _callGunInstance();
  _callGunNode   = gunNode ||
    _callGun.get(CALL_GUN_NS).get('sessions').get(sessionId);

  _callStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
  _callPc     = new RTCPeerConnection(CALL_ICE_CFG);
  _callStream.getTracks().forEach(t => _callPc.addTrack(t, _callStream));

  _callPc.onicecandidate = ({ candidate }) => {
    if (candidate) _callGunNode.get('ice_b').put(JSON.stringify(candidate));
  };

  _callPc.ontrack = (ev) => _callRenderRemote(ev.streams[0]);
  _callPc.ondatachannel = (ev) => { _callDc = ev.channel; _callSetupDc(_callDc); };

  // Wait for offer then answer
  _callGunNode.on(async (data) => {
    if (!data || !data.offer || !_callPc) return;
    if (_callPc.signalingState !== 'stable') return;
    try {
      await _callPc.setRemoteDescription(JSON.parse(data.offer));
      const answer = await _callPc.createAnswer();
      await _callPc.setLocalDescription(answer);
      _callGunNode.put({ answer: JSON.stringify(answer) });
    } catch (e) {
      console.warn('[Call] answerCall error:', e.message);
    }
  });

  _callGunNode.get('ice_a').on((raw) => {
    if (!raw || !_callPc) return;
    try { _callPc.addIceCandidate(JSON.parse(raw)); } catch (_) {}
  });

  _callNotifyUI({ event: 'call.answered', sessionId });
  return { sessionId };
}

// Generate a guest join link for session. Token is a random hex string stored
// server-side; join.html presents it back and the vault verifies in-memory.
function generateGuestLink(sessionId) {
  let token = _guestTokens.get(sessionId);
  if (!token) {
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    token = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
    _guestTokens.set(sessionId, token);
  }
  return `${location.origin}/join.html?id=${encodeURIComponent(sessionId)}&token=${token}`;
}

// Verify a guest token (called when join.html sends its token over the DataChannel
// or Gun node to prove it has the link).
function verifyGuestToken(sessionId, token) {
  return _guestTokens.get(sessionId) === token;
}

// Tear down the current call cleanly.
async function endCall() {
  if (_callStream) {
    _callStream.getTracks().forEach(t => t.stop());
    _callStream = null;
  }
  if (_callDc) { try { _callDc.close(); } catch (_) {} _callDc = null; }
  if (_callPc) {
    _callPc.close();
    _callPc = null;
  }
  if (_callGunNode) {
    try { _callGunNode.put(null); } catch (_) {}
    _callGunNode = null;
  }
  if (_callSessionId) {
    _guestTokens.delete(_callSessionId);
    _callSessionId = null;
  }
  _callNotifyUI({ event: 'call.ended' });
}

// Mute/unmute the local audio track.
function muteAudio(muted) {
  if (!_callStream) return;
  _callStream.getAudioTracks().forEach(t => { t.enabled = !muted; });
}

// Mute/unmute the local video track.
function muteVideo(muted) {
  if (!_callStream) return;
  _callStream.getVideoTracks().forEach(t => { t.enabled = !muted; });
}

// ── In-call data sharing (VC-11) ─────────────────────────────────────────────

// Send a signed data section to the call peer over the data channel.
function callSendData(id, section, data, sig, callSessionId) {
  if (!_callDc || _callDc.readyState !== 'open') return;
  _callDc.send(JSON.stringify({ type: 'data_response', id, section, data, sig, callSessionId }));
}

// Send a VP receipt to the call peer.
function callSendReceipt(id, receiptJsonLd, callSessionId) {
  if (!_callDc || _callDc.readyState !== 'open') return;
  _callDc.send(JSON.stringify({ type: 'data_receipt', id, receiptJsonLd, callSessionId }));
}

// ── DataChannel setup ─────────────────────────────────────────────────────────

function _callSetupDc(channel) {
  channel.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'data_request') {
        document.dispatchEvent(new CustomEvent('wf:data-request', { detail: msg }));
      } else if (msg.type === 'data_response' || msg.type === 'data_receipt') {
        document.dispatchEvent(new CustomEvent('wf:data-response', { detail: msg }));
      }
    } catch (_) {}
  };
  channel.onerror = (e) => console.warn('[Call] DataChannel error:', e);
}

// ── Internal helpers ──────────────────────────────────────────────────────────

function _callGunInstance() {
  // Reuse gate's Gun instance if available; otherwise create a new one.
  if (typeof _gateGun !== 'undefined' && _gateGun) return _gateGun;
  if (typeof Gun !== 'undefined') return Gun(CALL_GUN_RELAYS);
  throw new Error('[Call] Gun not available');
}

function _callVaultDid() {
  return typeof vaultDidKey !== 'undefined' && vaultDidKey
    ? vaultDidKey.did : null;
}

// Attach a remote stream to the vault.html in-call video element (added in VC-10b).
function _callRenderRemote(stream) {
  const el = document.getElementById('call-remote-video');
  if (el) { el.srcObject = stream; el.play().catch(() => {}); }
}

// Notify vault.html UI of call lifecycle events (VC-10b wires these to the panel).
function _callNotifyUI(ev) {
  document.dispatchEvent(new CustomEvent('wf:call', { detail: ev }));
}

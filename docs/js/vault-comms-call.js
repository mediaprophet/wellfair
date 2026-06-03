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

let _callGun             = null;
let _callPc              = null;
let _callDc              = null; // in-call data-sharing DataChannel
let _callStream          = null;
let _callSessionId       = null;
let _callGunNode         = null;
let _callActiveContactId = null; // directory contact id for the current call
const _guestTokens = new Map(); // sessionId → token (hex)

// WA-2 frame loop state
let _callRafId   = null;
let _callFrameTs = 0;
const _FRAME_MS  = 100; // ~10fps cap — matches MediaPipe throughput on mid-range hardware

// PIA3 — session start timestamp for duration calculation
let _callStartTs = 0;

// ── PIA3: Protocol event provenance ───────────────────────────────────────────
// Writes a wf:ProtocolEvent record to wf-events IDB (Q42 dual-write included
// via the existing dual-write hook in vault-idb.js).  Never throws — provenance
// failure must not break the call flow.

async function _writeProtocolEvent(fields) {
  try {
    const record = {
      id:                crypto.randomUUID(),
      type:              'wf:ProtocolEvent',
      protocolEventType: fields.protocolEventType,
      sessionId:         fields.sessionId  || null,
      participants:      fields.participants || null,
      durationSeconds:   fields.durationSeconds != null ? fields.durationSeconds : null,
      consentBasis:      fields.consentBasis || null,
      timestamp:         new Date().toISOString(),
      piaEvent:          true,
    };
    await _dbPut(_ST_EVENTS, record);
  } catch (e) {
    console.warn('[PIA3] _writeProtocolEvent failed:', e.message);
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

// Initiate a call to a contact. Returns { sessionId, callLink }.
async function startCall(contactId) {
  await endCall(); // clean up any existing call

  const sessionId          = crypto.randomUUID();
  _callSessionId           = sessionId;
  _callActiveContactId     = contactId ?? null;

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
  if (typeof initAgent === 'function') initAgent(sessionId, _callDc);
  _callStartFrameLoop();

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

  _callStartTs = Date.now();
  const callLink = generateGuestLink(sessionId);
  if (typeof captureEvent === 'function') {
    captureEvent(sessionId, 'call.start', _callVaultDid(), {}).catch(() => {});
  }
  _writeProtocolEvent({
    protocolEventType: 'webrtc_session_start',
    sessionId,
    participants: JSON.stringify([_callVaultDid(), contactId].filter(Boolean)),
  }).catch(() => {});
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
  _callPc.ondatachannel = (ev) => {
    _callDc = ev.channel;
    _callSetupDc(_callDc);
    if (typeof initAgent === 'function') initAgent(_callSessionId, _callDc);
    _callStartFrameLoop();
  };

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
  _callStopFrameLoop();
  if (typeof stopAgent === 'function') await stopAgent().catch(() => {});
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
    if (typeof captureEvent === 'function') {
      captureEvent(_callSessionId, 'call.end', _callVaultDid(), {}).catch(() => {});
    }
    const durationSeconds = _callStartTs ? Math.round((Date.now() - _callStartTs) / 1000) : null;
    _callStartTs = 0;
    _writeProtocolEvent({
      protocolEventType: 'webrtc_session_end',
      sessionId:         _callSessionId,
      participants:      JSON.stringify([_callVaultDid()].filter(Boolean)),
      durationSeconds,
    }).catch(() => {});
    _guestTokens.delete(_callSessionId);
    _callSessionId = null;
  }
  _callActiveContactId = null;
  _callNotifyUI({ event: 'call.ended' });
}

// Expose audio stream for vault-cv.js agentStartAudio (WA-4).
function callGetAudioStream() {
  return _callStream;
}

// Returns the directory contact id for the current call (null if unknown/guest).
// Used by _callOverlayPopulateInfo() in vault.html to resolve the call profile.
function callGetActiveContactId() {
  return _callActiveContactId;
}

// Set the active contact id from the gate module (inbound calls).
function callSetActiveContact(contactId) {
  _callActiveContactId = contactId ?? null;
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
        if (typeof captureEvent === 'function' && msg.callSessionId) {
          captureEvent(msg.callSessionId, 'data.request',
            msg.callerDid || 'unknown', { sections: msg.sections }).catch(() => {});
        }
        document.dispatchEvent(new CustomEvent('wf:data-request', { detail: msg }));
      } else if (msg.type === 'data_response' || msg.type === 'data_receipt') {
        document.dispatchEvent(new CustomEvent('wf:data-response', { detail: msg }));
      } else if (msg.type === 'job_result' || msg.type === 'job_error' || msg.type === 'job_progress') {
        // Route desktop job offload results back to the scheduler
        if (typeof schedHandleDesktopResult === 'function') {
          schedHandleDesktopResult(msg).catch(() => {});
        }
      } else if (msg.type === 'call_control') {
        // Remote call-control from peer (mute/end)
        if (msg.action === 'end') {
          endCall();
        } else if (msg.action === 'mute_audio') {
          muteAudio(!!msg.muted);
        } else if (msg.action === 'mute_video') {
          muteVideo(!!msg.muted);
        }
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

// ── WA-2 Vision frame capture loop ───────────────────────────────────────────

function _callStartFrameLoop() {
  if (_callRafId) return;

  // Wire local stream to hidden video so we can draw it to canvas
  const localVid = document.getElementById('call-local-video');
  if (localVid && _callStream) {
    localVid.srcObject = _callStream;
    localVid.play().catch(() => {});
  }

  // Start audio pipeline for prosody if consent was granted before the call began
  if (typeof agentStartAudio === 'function' && _callStream) {
    agentStartAudio(_callStream);
  }

  const tick = () => {
    _callRafId = requestAnimationFrame(tick);
    const now = performance.now();
    if (now - _callFrameTs < _FRAME_MS) return;
    if (!_callStream || !_callSessionId) return;
    if (typeof agentHasModule !== 'function') return;

    // Only capture if a vision module needs frames
    const needsEmotion = agentHasModule(CV_MODULE.EMOTION);
    const needsRpg     = agentHasModule(CV_MODULE.RPG);
    if (!needsEmotion && !needsRpg) return;

    const vEl = document.getElementById('call-local-video');
    if (!vEl || vEl.readyState < 2 || vEl.videoWidth === 0) return;

    _callFrameTs = now;
    try {
      const canvas = new OffscreenCanvas(vEl.videoWidth, vEl.videoHeight);
      canvas.getContext('2d').drawImage(vEl, 0, 0);

      if (needsEmotion && needsRpg) {
        // Both active: need two separate bitmaps (bitmap is transferable, can't split)
        const bm1 = canvas.transferToImageBitmap();
        createImageBitmap(vEl).then(bm2 => {
          agentSendFrame(CV_MODULE.EMOTION, bm1);
          agentSendFrame(CV_MODULE.RPG, bm2);
        }).catch(() => { bm1.close(); });
      } else {
        const bm = canvas.transferToImageBitmap();
        if (needsEmotion) agentSendFrame(CV_MODULE.EMOTION, bm);
        else              agentSendFrame(CV_MODULE.RPG, bm);
      }
    } catch (e) {
      console.warn('[Call] frame capture:', e.message);
    }
  };
  tick();
}

function _callStopFrameLoop() {
  if (_callRafId) { cancelAnimationFrame(_callRafId); _callRafId = null; }
  _callFrameTs = 0;
  const localVid = document.getElementById('call-local-video');
  if (localVid) { localVid.srcObject = null; }
}

'use strict';

// ── Webizen Agent — AgentController (WA-1) ────────────────────────────────
// Manages CV/audio/text analytics workers for telehealth calls.
// Workers live in docs/js/workers/ and are loaded only when consent is granted.
//
// Key constraint: raw video frames, audio buffers, and transcripts never leave
// the device. Only structured JSON telemetry travels over the DataChannel.
//
// Depends on: vault-idb.js (_ST_TELEMETRY, _dbPut),
//             vault-transcript.js (captureEvent — optional, VC-13 integration)
// Script load order: must come after vault-comms-call.js

// ── Module registry ────────────────────────────────────────────────────────

const CV_MODULE = Object.freeze({
  EMOTION:    'vision.emotion',
  RPG:        'vision.rpg',
  PROSODY:    'audio.prosody',
  LINGUISTIC: 'text.linguistic',
});

// ── Agent state ────────────────────────────────────────────────────────────

let _agentSessionId  = null;
let _agentDc         = null;   // DataChannel reference (set at call start)
let _agentWorkers    = {};     // module → Worker
let _agentConsent    = {};     // module → bool
let _agentFrame      = {};     // telemetry accumulator for current frame
let _agentPrevHash   = null;   // hash chain tail
let _agentSeq        = 0;      // monotonic frame sequence number

// ── Audio pipeline state (WA-4) ────────────────────────────────────────────

let _audioCtx         = null;  // AudioContext
let _audioWorkletNode = null;  // AudioWorkletNode (prosody-processor)
let _audioSourceNode  = null;  // MediaStreamAudioSourceNode

// ── Public API ─────────────────────────────────────────────────────────────

function initAgent(callSessionId, dataChannel) {
  _agentSessionId = callSessionId;
  _agentDc        = dataChannel;
  _agentWorkers   = {};
  _agentConsent   = {
    [CV_MODULE.EMOTION]:    false,
    [CV_MODULE.RPG]:        false,
    [CV_MODULE.PROSODY]:    false,
    [CV_MODULE.LINGUISTIC]: false,
  };
  _agentFrame    = {};
  _agentPrevHash = null;
  _agentSeq      = 0;
  console.debug('[AgentController] initAgent session:', callSessionId);
}

function setModuleConsent(module, granted) {
  if (!_agentSessionId) return;
  if (!Object.values(CV_MODULE).includes(module)) {
    console.warn('[AgentController] unknown module:', module);
    return;
  }
  _agentConsent[module] = granted;
  if (granted) {
    _spawnWorker(module);
    if (module === CV_MODULE.PROSODY) {
      // Start audio pipeline immediately if a call is already active
      const stream = typeof callGetAudioStream === 'function' ? callGetAudioStream() : null;
      if (stream) agentStartAudio(stream);
    }
  } else {
    _terminateWorker(module);
    if (module === CV_MODULE.PROSODY) _teardownAudio();
  }
  _updateConsentUI();
}

// Check if a specific module's worker is currently running.
function agentHasModule(module) {
  return !!_agentWorkers[module];
}

// Send a frame (ImageBitmap) to a vision worker. Bitmap ownership is transferred.
// Silently closes the bitmap if the worker is not running.
function agentSendFrame(module, bitmap) {
  const w = _agentWorkers[module];
  if (!w) {
    if (bitmap && typeof bitmap.close === 'function') bitmap.close();
    return;
  }
  w.postMessage({ bitmap }, [bitmap]);
}

// Forward a transcript segment to the LINGUISTIC worker (WA-5).
// Called from vault-comms-transcode.js after each speech.segment event.
function agentSendText(text, ts) {
  const w = _agentWorkers[CV_MODULE.LINGUISTIC];
  if (!w || !text) return;
  w.postMessage({ text, ts: ts || new Date().toISOString() });
}

async function stopAgent() {
  _teardownAudio(); // stop audio pipeline before workers
  // Send stop signal before closing
  if (_agentDc && _agentDc.readyState === 'open') {
    try {
      _agentDc.send(JSON.stringify({ type: 'agent.stop', sessionId: _agentSessionId }));
    } catch (_) {}
  }
  // Flush any partially-accumulated frame
  const pendingModules = Object.keys(_agentFrame);
  if (pendingModules.length > 0) {
    await _emitTelemetry(_buildFrame()).catch(() => {});
  }
  // Terminate all workers
  for (const m of Object.keys(_agentWorkers)) _terminateWorker(m);
  _agentSessionId = null;
  _agentDc        = null;
  _agentFrame     = {};
  _updateConsentUI();
  console.debug('[AgentController] stopAgent — all workers terminated');
}

// Start the AudioContext + AudioWorklet pipeline for the PROSODY module.
// No-op if already running or if the PROSODY worker is not active.
// Called from setModuleConsent (during-call consent) and from vault-comms-call.js
// _callStartFrameLoop (call-start with pre-consented PROSODY).
async function agentStartAudio(mediaStream) {
  if (!mediaStream || !agentHasModule(CV_MODULE.PROSODY)) return;
  if (_audioCtx) return; // already running

  const worker = _agentWorkers[CV_MODULE.PROSODY];
  if (!worker) return;

  try {
    _audioCtx = new AudioContext();
    await _audioCtx.audioWorklet.addModule('js/workers/audio-prosody.worklet.js');
    _audioWorkletNode = new AudioWorkletNode(_audioCtx, 'prosody-processor');

    // Relay audio chunks from worklet → features worker (zero-copy transfer)
    _audioWorkletNode.port.onmessage = (ev) => {
      if (!ev.data || !(ev.data.chunk instanceof Float32Array)) return;
      const { chunk, sampleRate } = ev.data;
      if (worker) worker.postMessage({ chunk, sampleRate }, [chunk.buffer]);
    };

    const audioTracks = mediaStream.getAudioTracks();
    if (audioTracks.length === 0) {
      console.warn('[AgentController] no audio tracks in stream');
      _teardownAudio();
      return;
    }
    _audioSourceNode = _audioCtx.createMediaStreamSource(
      new MediaStream([audioTracks[0]])
    );
    _audioSourceNode.connect(_audioWorkletNode);
    // Not connected to destination — no local playback of own microphone

    console.debug('[AgentController] audio pipeline started, sampleRate:', _audioCtx.sampleRate);
  } catch (e) {
    console.warn('[AgentController] audio pipeline setup failed:', e.message);
    _teardownAudio();
  }
}

// ── VaultCV compat shim — keeps the old stub API surface working ───────────

const VaultCV = {
  isAvailable:       () => _agentSessionId !== null,
  initAgent,
  setModuleConsent,
  stopAgent,
  agentHasModule,
  agentSendFrame,
  CV_MODULE,
};

// ── Worker file name map (module → file stem in docs/js/workers/) ──────────

const _WORKER_FILE = {
  [CV_MODULE.EMOTION]:    'cv-emotion',
  [CV_MODULE.RPG]:        'cv-rpg',
  [CV_MODULE.PROSODY]:    'audio-features',  // features Worker; worklet loaded by agentStartAudio
  [CV_MODULE.LINGUISTIC]: 'text-linguistic',
};

// ── Internal helpers ───────────────────────────────────────────────────────

function _spawnWorker(module) {
  if (_agentWorkers[module]) return; // already running
  const stem = _WORKER_FILE[module] || module;
  const path = 'js/workers/' + stem + '.worker.js';
  try {
    // Classic worker (not module) — required for MediaPipe's internal importScripts() calls.
    // Workers use dynamic import() for their own ESM dependencies.
    const w = new Worker(path);
    w.onmessage = (ev) => _onWorkerMessage(module, ev.data);
    w.onerror   = (e)  => console.warn('[AgentController] worker error:', module, e.message);
    _agentWorkers[module] = w;
    console.debug('[AgentController] spawned worker:', module);
  } catch (e) {
    // Worker file will not exist until WA-2 through WA-5 — catch gracefully
    console.warn('[AgentController] worker spawn failed (expected until WA-2+):', module, e.message);
  }
}

function _terminateWorker(module) {
  if (module === CV_MODULE.PROSODY) _teardownAudio();
  const w = _agentWorkers[module];
  if (!w) return;
  try { w.terminate(); } catch (_) {}
  delete _agentWorkers[module];
  delete _agentFrame[module];
  console.debug('[AgentController] terminated worker:', module);
}

function _teardownAudio() {
  if (_audioSourceNode) {
    try { _audioSourceNode.disconnect(); } catch (_) {}
    _audioSourceNode = null;
  }
  if (_audioWorkletNode) {
    try { _audioWorkletNode.disconnect(); _audioWorkletNode.port.close(); } catch (_) {}
    _audioWorkletNode = null;
  }
  if (_audioCtx) {
    _audioCtx.close().catch(() => {});
    _audioCtx = null;
  }
}

function _onWorkerMessage(module, payload) {
  // Lifecycle messages (ready, error) are not telemetry data
  if (payload && payload.type === 'ready') {
    console.debug('[AgentController] worker ready:', module);
    return;
  }
  if (payload && payload.type === 'error') {
    console.warn('[AgentController] worker init error:', module, payload.error);
    return;
  }

  _agentFrame[module] = payload;
  // Emit a telemetry frame once all active workers have reported
  const active = Object.keys(_agentWorkers);
  if (active.length > 0 && active.every(m => _agentFrame[m] !== undefined)) {
    const frame = _buildFrame();
    _agentFrame = {};
    _emitTelemetry(frame).catch(e => console.warn('[AgentController] emit error:', e));
  }
}

function _buildFrame() {
  const frame = {
    id:        'evt-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7),
    type:      'agent.telemetry',
    sessionId: _agentSessionId,
    seq:       ++_agentSeq,
    actorDid:  (typeof vaultDidKey !== 'undefined' && vaultDidKey) ? vaultDidKey.did : null,
    ts:        new Date().toISOString(),
    payload: {
      modules:    Object.keys(_agentWorkers),
      vision:     {},
      biometrics: {},
      audio:      {},
      linguistic: {},
    },
  };

  // Merge each module's result into the appropriate typed bucket
  for (const [mod, data] of Object.entries(_agentFrame)) {
    if (mod === CV_MODULE.EMOTION)    Object.assign(frame.payload.vision,     data);
    else if (mod === CV_MODULE.RPG)   Object.assign(frame.payload.biometrics, data);
    else if (mod === CV_MODULE.PROSODY) Object.assign(frame.payload.audio,    data);
    else if (mod === CV_MODULE.LINGUISTIC) frame.payload.linguistic = data;
  }
  return frame;
}

async function _emitTelemetry(frame) {
  // SHA-256 hash chain (same pattern as wf-events)
  const payloadStr = JSON.stringify(frame.payload);
  const hashBuf    = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(payloadStr));
  const hash       = 'sha256-' + Array.from(new Uint8Array(hashBuf))
                       .map(b => b.toString(16).padStart(2, '0')).join('');

  const record = { ...frame, hash, prevHash: _agentPrevHash };
  _agentPrevHash = hash;

  // Persist to IDB
  try {
    await _dbPut(_ST_TELEMETRY, record);
  } catch (e) {
    console.warn('[AgentController] IDB write failed:', e);
  }

  // Forward structured JSON over DataChannel (not raw biometrics)
  if (_agentDc && _agentDc.readyState === 'open') {
    try {
      _agentDc.send(JSON.stringify({ type: 'agent.telemetry', ...record }));
    } catch (_) {}
  }

  // VC-13 — append to call event log
  if (typeof captureEvent === 'function' && _agentSessionId) {
    captureEvent(
      _agentSessionId,
      'agent.telemetry',
      (typeof vaultDidKey !== 'undefined' && vaultDidKey) ? vaultDidKey.did : 'unknown',
      frame.payload
    ).catch(() => {});
  }
}

// Refresh the active-module indicator line in the consent UI
function _updateConsentUI() {
  const indicator = document.getElementById('agent-active-modules');
  if (!indicator) return;
  const active = Object.values(CV_MODULE)
    .filter(m => _agentWorkers[m])
    .map(m => m.split('.').pop());
  indicator.textContent = active.length ? 'Active: ' + active.join(' · ') : 'No modules active';
  indicator.style.color = active.length ? 'var(--green)' : 'var(--dim)';
}

// Called from vault.html consent checkboxes
function _cvToggle(module, checked) {
  setModuleConsent(module, checked);
  // Keep checkbox in sync with actual state (spawn may fail)
  const el = document.getElementById('agent-chk-' + module.replace('.', '-'));
  if (el) el.checked = !!_agentWorkers[module];
}

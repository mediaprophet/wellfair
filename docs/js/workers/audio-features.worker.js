// audio.prosody Worker — Meyda feature extraction from audio chunks
//
// Module key: 'audio.prosody'
// Loaded by:  vault-cv.js via new Worker('js/workers/audio-features.worker.js')
//             Classic worker (not module). Meyda loaded via dynamic import().
//
// Input:  postMessage({ chunk: Float32Array(2048), sampleRate: number })
//         Forwarded from AudioWorkletNode.port by vault-cv.js (agentStartAudio).
//
// Output: postMessage({ module, rms, pitchHz, energyVariance, tremorIndex, speechRate })
//         Emitted at most once per EMIT_INTERVAL_MS (500ms); earlier chunks update
//         internal state but do not generate a payload until the interval elapses.
//
// speechRate is always 0 here — it is populated in WA-5 from transcript word count.

const BUFFER_SIZE      = 2048;   // must match ProsodyProcessor CHUNK_SIZE
const EMIT_INTERVAL_MS = 500;
const RMS_HISTORY_MAX  = 20;     // rolling window ~10 s at 500 ms cadence

let _Meyda      = null;
let _ready      = false;
let _sampleRate = 44100;
let _lastEmitTs = 0;
const _rmsHistory = [];  // rolling rms for variance computation

// ── Init — dynamic import so this file works as a classic (non-module) worker ──
async function _init() {
  try {
    const m = await import('https://cdn.jsdelivr.net/npm/meyda@5/+esm');
    _Meyda = m.default || m;
    _Meyda.bufferSize = BUFFER_SIZE;
    _ready = true;
    self.postMessage({ module: 'audio.prosody', type: 'ready' });
  } catch (e) {
    self.postMessage({ module: 'audio.prosody', type: 'error', error: e.message });
  }
}

// ── Feature extraction ────────────────────────────────────────────────────────
function _processChunk(chunk, sampleRate) {
  if (!_ready || !_Meyda) return;
  if (chunk.length < BUFFER_SIZE) return; // drop incomplete chunks

  _sampleRate = sampleRate;

  let features;
  try {
    features = _Meyda.extract(['rms', 'spectralCentroid', 'zcr'], chunk);
  } catch (e) {
    console.warn('[cv-audio] Meyda extract error:', e.message);
    return;
  }
  if (!features) return;

  const rms = features.rms || 0;

  // Update rolling rms history for variance calculation
  _rmsHistory.push(rms);
  if (_rmsHistory.length > RMS_HISTORY_MAX) _rmsHistory.shift();

  // Rate-limit output to EMIT_INTERVAL_MS
  const now = Date.now();
  if (now - _lastEmitTs < EMIT_INTERVAL_MS) return;
  _lastEmitTs = now;

  // pitchHz: spectralCentroid (bins) → Hz
  // Meyda returns spectralCentroid in bins [0, bufferSize/2).
  // Conversion: bin × (sampleRate / bufferSize).
  // This is an approximation of voice brightness, not the true fundamental (F0).
  // Full F0 via autocorrelation is the v0.0.8 upgrade path.
  const pitchHz = +(Math.max(0, Math.min(600,
    (features.spectralCentroid || 0) * (sampleRate / BUFFER_SIZE)
  ))).toFixed(1);

  // energyVariance: population variance of rolling rms window
  let energyVariance = 0;
  if (_rmsHistory.length > 1) {
    const mean = _rmsHistory.reduce((a, b) => a + b, 0) / _rmsHistory.length;
    energyVariance = _rmsHistory.reduce((s, v) => s + (v - mean) ** 2, 0) / (_rmsHistory.length - 1);
  }

  // tremorIndex: zero-crossing rate normalised to [0, 1]
  // Higher ZCR correlates with more rapid amplitude oscillation (tremor proxy).
  // v0.0.8 upgrade: compute true 4–12 Hz modulation power from amplitude envelope.
  const tremorIndex = +Math.min(1, Math.max(0, features.zcr || 0)).toFixed(4);

  self.postMessage({
    module:         'audio.prosody',
    rms:            +rms.toFixed(4),
    pitchHz,
    energyVariance: +energyVariance.toFixed(6),
    tremorIndex,
    speechRate:     0,  // populated by WA-5
  });
}

// ── Message handler ───────────────────────────────────────────────────────────
self.onmessage = function(ev) {
  const { chunk, sampleRate } = ev.data || {};
  if (chunk instanceof Float32Array) {
    _processChunk(chunk, sampleRate || _sampleRate);
  }
};

_init();

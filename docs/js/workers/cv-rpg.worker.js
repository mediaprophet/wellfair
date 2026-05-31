// vision.rpg Worker — rPPG pulse detection (green-channel temporal FFT)
//
// Module key: 'vision.rpg'
// Loaded by:  vault-cv.js via new Worker('js/workers/cv-rpg.worker.js')
//             Classic worker (not module) — consistent with cv-emotion.worker.js.
//             No external libraries; pure JS. No importScripts() calls needed.
//
// COOP/COEP:  provided by sw.js — OffscreenCanvas available in classic workers
//
// Input:  postMessage({ bitmap: ImageBitmap })   — transferable, zero-copy
// Output: postMessage({ module, bpm, confidence, signalQuality })
//
// Algorithm: remote photoplethysmography (rPPG)
//   ROI: fixed forehead proxy — top 20% rows, centre 50% width (no landmark dependency)
//   Signal: per-frame average of green channel pixels in ROI → temporal buffer
//   Processing: detrend → Hann window → Cooley-Tukey FFT → peak in 0.75–4 Hz band
//   SNR thresholds: > 5 → good, > 2 → fair, else poor
//
// v0.0.8 upgrade path: replace _estimateBpm() with a Rust/Wasm CHROM bandpass module.
// The postMessage contract ({bpm, confidence, signalQuality}) stays identical.

// ── Constants ────────────────────────────────────────────────────────────────
const BUFFER_FRAMES = 300;    // ~10 s at 30 fps
const SAMPLE_RATE   = 30;     // assumed fps; overridden by measured timestamp delta
const FFT_SIZE      = 512;    // next power-of-2 ≥ BUFFER_FRAMES; signal is zero-padded
const BPM_LOW_HZ    = 0.75;   // 45 BPM
const BPM_HIGH_HZ   = 4.0;    // 240 BPM
const SNR_GOOD      = 5.0;
const SNR_FAIR      = 2.0;

// ── Circular buffer ──────────────────────────────────────────────────────────
const _gBuf  = new Float32Array(BUFFER_FRAMES); // green-channel samples
const _tsBuf = new Float64Array(BUFFER_FRAMES); // frame receipt timestamps (ms)
let _head    = 0;  // next write index
let _count   = 0;  // frames received; saturates at BUFFER_FRAMES once full

// ── OffscreenCanvas (lazy-init, resizes with bitmap dimensions) ───────────────
let _canvas = null;
let _ctx    = null;

// ── Cooley-Tukey FFT (radix-2, iterative, in-place) ─────────────────────────
// re[] and im[] must both have length equal to a power of 2.
function _fft(re, im) {
  const N = re.length;

  // Bit-reversal permutation
  for (let i = 1, j = 0; i < N; i++) {
    let bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      let t = re[i]; re[i] = re[j]; re[j] = t;
          t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }

  // Butterfly passes
  for (let len = 2; len <= N; len <<= 1) {
    const half = len >> 1;
    const ang  = -2 * Math.PI / len;
    const cosA = Math.cos(ang);
    const sinA = Math.sin(ang);
    for (let i = 0; i < N; i += len) {
      let wr = 1, wi = 0;
      for (let k = 0; k < half; k++) {
        const ur = re[i + k],          ui = im[i + k];
        const vr = re[i + k + half] * wr - im[i + k + half] * wi;
        const vi = re[i + k + half] * wi + im[i + k + half] * wr;
        re[i + k]        = ur + vr;  im[i + k]        = ui + vi;
        re[i + k + half] = ur - vr;  im[i + k + half] = ui - vi;
        const t = wr * cosA - wi * sinA;
        wi = wr * sinA + wi * cosA;
        wr = t;
      }
    }
  }
}

// ── Signal processing ────────────────────────────────────────────────────────

// Least-squares linear detrend — removes slow baseline drift from skin reflectance.
function _detrend(signal) {
  const n = signal.length;
  let sx = 0, sy = 0, sxy = 0, sxx = 0;
  for (let i = 0; i < n; i++) {
    sx  += i;
    sy  += signal[i];
    sxy += i * signal[i];
    sxx += i * i;
  }
  const denom = n * sxx - sx * sx;
  const slope  = denom !== 0 ? (n * sxy - sx * sy) / denom : 0;
  const offset = (sy - slope * sx) / n;
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) out[i] = signal[i] - (slope * i + offset);
  return out;
}

// Hann window — reduces spectral leakage at buffer boundaries.
function _hann(signal) {
  const n   = signal.length;
  const out = new Float32Array(n);
  const c   = 2 * Math.PI / (n - 1);
  for (let i = 0; i < n; i++) out[i] = signal[i] * (0.5 - 0.5 * Math.cos(c * i));
  return out;
}

// Estimate BPM from a BUFFER_FRAMES-length green-channel snapshot.
function _estimateBpm(signal, sampleRateHz) {
  const windowed = _hann(_detrend(signal));

  // Zero-pad to FFT_SIZE
  const re = new Float32Array(FFT_SIZE);
  const im = new Float32Array(FFT_SIZE);
  for (let i = 0; i < windowed.length; i++) re[i] = windowed[i];

  _fft(re, im);

  // Power spectrum (first half — up to Nyquist)
  const half  = FFT_SIZE >> 1;
  const power = new Float32Array(half);
  for (let i = 0; i < half; i++) power[i] = re[i] * re[i] + im[i] * im[i];

  // BPM band indices
  const freqRes = sampleRateHz / FFT_SIZE;
  const loIdx   = Math.max(1, Math.ceil(BPM_LOW_HZ  / freqRes));
  const hiIdx   = Math.min(half - 1, Math.floor(BPM_HIGH_HZ / freqRes));

  // Find peak bin in BPM band
  let peakIdx = loIdx, peakPow = 0;
  for (let i = loIdx; i <= hiIdx; i++) {
    if (power[i] > peakPow) { peakPow = power[i]; peakIdx = i; }
  }

  const bpm = peakIdx * freqRes * 60;

  // SNR: peak power vs mean power outside a ±3-bin exclusion zone
  let noiseSum = 0, noiseCount = 0;
  for (let i = 0; i < half; i++) {
    if (Math.abs(i - peakIdx) > 3) { noiseSum += power[i]; noiseCount++; }
  }
  const noiseMean = noiseCount > 0 ? noiseSum / noiseCount : 1;
  const snr       = noiseMean > 0 ? peakPow / noiseMean : 0;

  const confidence    = +Math.min(1, Math.max(0, snr / (SNR_GOOD * 2))).toFixed(3);
  const signalQuality = snr > SNR_GOOD ? 'good' : snr > SNR_FAIR ? 'fair' : 'poor';

  return { bpm: +bpm.toFixed(1), confidence, signalQuality };
}

// ── ROI pixel extraction ─────────────────────────────────────────────────────

// Draws the bitmap to an OffscreenCanvas, then reads the forehead-proxy ROI:
// top 20% rows × centre 50% columns.  Returns mean green value (0–255).
function _extractGreen(bitmap) {
  const w = bitmap.width;
  const h = bitmap.height;

  if (!_canvas || _canvas.width !== w || _canvas.height !== h) {
    _canvas = new OffscreenCanvas(w, h);
    _ctx    = _canvas.getContext('2d', { willReadFrequently: true });
  }

  _ctx.drawImage(bitmap, 0, 0, w, h);

  const roiX = Math.floor(w * 0.25);
  const roiY = 0;
  const roiW = Math.max(1, Math.floor(w * 0.50));
  const roiH = Math.max(1, Math.floor(h * 0.20));
  const data  = _ctx.getImageData(roiX, roiY, roiW, roiH).data;

  let gSum = 0;
  const nPixels = data.length >> 2;
  for (let i = 1; i < data.length; i += 4) gSum += data[i]; // G byte at offset 1

  return nPixels > 0 ? gSum / nPixels : 0;
}

// ── Ordered snapshot from circular buffer ────────────────────────────────────
function _getSnapshot() {
  const n = Math.min(_count, BUFFER_FRAMES);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    out[i] = _gBuf[(_head - n + i + BUFFER_FRAMES) % BUFFER_FRAMES];
  }
  return out;
}

// ── Measured sample rate from timestamp buffer ────────────────────────────────
function _measuredSampleRate() {
  const oldest = _tsBuf[_head % BUFFER_FRAMES];                        // about to be overwritten
  const newest = _tsBuf[(_head - 1 + BUFFER_FRAMES) % BUFFER_FRAMES]; // most recently written
  const elapsedS = (newest - oldest) / 1000;
  return elapsedS > 0.1 ? (BUFFER_FRAMES - 1) / elapsedS : SAMPLE_RATE;
}

// ── Message handler ──────────────────────────────────────────────────────────
self.onmessage = function(ev) {
  const { bitmap } = ev.data || {};
  if (!bitmap) return;

  let g = 0;
  try {
    g = _extractGreen(bitmap);
  } catch (e) {
    console.warn('[cv-rpg] pixel extract error:', e.message);
  } finally {
    try { bitmap.close(); } catch (_) {}
  }

  // Append to circular buffer
  _gBuf[_head]  = g;
  _tsBuf[_head] = performance.now();
  _head = (_head + 1) % BUFFER_FRAMES;
  _count++;

  // Buffer still filling — emit 'poor' placeholder
  if (_count < BUFFER_FRAMES) {
    self.postMessage({ module: 'vision.rpg', bpm: null, confidence: 0, signalQuality: 'poor' });
    return;
  }

  // Full buffer — run FFT pipeline
  const sampleRateHz = _measuredSampleRate();
  const snapshot     = _getSnapshot();
  const result       = _estimateBpm(snapshot, sampleRateHz);

  self.postMessage({ module: 'vision.rpg', ...result });
};

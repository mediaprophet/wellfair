// vision.emotion Worker — MediaPipe FaceLandmarker → emotion blendshapes
//
// Module key: 'vision.emotion'
// Loaded by:  vault-cv.js via new Worker('js/workers/cv-emotion.worker.js')
//             Classic worker (not module) — MediaPipe's WasmFileset.loadModule()
//             uses importScripts() internally, which is only available in classic workers.
//             ESM dependencies are loaded via dynamic import().
//
// COOP/COEP:  provided by sw.js — SharedArrayBuffer + crossOriginIsolated available
//
// Input:  postMessage({ bitmap: ImageBitmap })   — transferable, zero-copy
// Output: postMessage({ module, emotion, confidence, valence, arousal })

// ── Blendshape → emotion mapping (ARKit 52-blendshape convention) ──────────
const _EMOTION_MAP = {
  happy:     ['mouthSmileLeft', 'mouthSmileRight'],
  sad:       ['mouthFrownLeft', 'mouthFrownRight', 'browDownLeft', 'browDownRight'],
  angry:     ['browDownLeft', 'browDownRight', 'noseSneerLeft', 'noseSneerRight'],
  fearful:   ['browInnerUp', 'eyeWideLeft', 'eyeWideRight'],
  disgusted: ['noseSneerLeft', 'noseSneerRight', 'mouthLowerDownLeft'],
  surprised: ['jawOpen', 'eyeWideLeft', 'eyeWideRight', 'browOuterUpLeft'],
};

// Russell circumplex model weights — valence (pleasant↔unpleasant) and
// arousal (activated↔deactivated)
const _VALENCE = {
  happy: +1.0, sad: -0.9, angry: -0.8, fearful: -0.5,
  disgusted: -0.7, surprised: +0.2, neutral: 0.0,
};
const _AROUSAL = {
  happy: +0.6, sad: -0.5, angry: +0.9, fearful: +0.7,
  disgusted: +0.3, surprised: +0.8, neutral: 0.0,
};

// ── State ──────────────────────────────────────────────────────────────────
let _landmarker = null;
let _ready      = false;

// ── Init (dynamic import — avoids module worker restriction) ───────────────
async function _init() {
  try {
    const { FaceLandmarker, FilesetResolver } = await import(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm'
    );

    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm'
    );

    _landmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          'https://storage.googleapis.com/mediapipe-models/face_landmarker/' +
          'face_landmarker/float16/1/face_landmarker.task',
        delegate: 'CPU',  // GPU needs GL context; CPU works in any worker
      },
      outputFaceBlendshapes: true,
      runningMode: 'IMAGE',
      numFaces: 1,
    });

    _ready = true;
    self.postMessage({ module: 'vision.emotion', type: 'ready' });
  } catch (e) {
    self.postMessage({ module: 'vision.emotion', type: 'error', error: e.message });
  }
}

// ── Frame processing ────────────────────────────────────────────────────────
self.onmessage = function(ev) {
  const { bitmap } = ev.data || {};
  if (!bitmap) return;

  if (!_ready || !_landmarker) {
    bitmap.close();
    return;
  }

  try {
    const result = _landmarker.detect(bitmap);
    bitmap.close();

    if (!result.faceBlendshapes || result.faceBlendshapes.length === 0) {
      self.postMessage({
        module: 'vision.emotion',
        emotion: 'none', confidence: 0, valence: 0, arousal: 0,
      });
      return;
    }

    // Build blendshape score lookup by name
    const bs = {};
    for (const { categoryName, score } of result.faceBlendshapes[0].categories) {
      bs[categoryName] = score;
    }

    // Score each emotion as the average of its indicator blendshapes
    const scores = {};
    for (const [emotion, blendshapes] of Object.entries(_EMOTION_MAP)) {
      scores[emotion] = blendshapes.reduce((sum, b) => sum + (bs[b] || 0), 0)
                        / blendshapes.length;
    }

    // Dominant emotion: highest score above neutral threshold
    let topEmotion = 'neutral';
    let topScore   = 0.15; // below this → neutral
    for (const [emotion, score] of Object.entries(scores)) {
      if (score > topScore) { topEmotion = emotion; topScore = score; }
    }

    // Confidence: how decisive the top emotion is (clamped 0–1)
    const confidence = Math.min(1, topScore / 0.45);

    // Valence/arousal: weighted blend across all active emotion scores
    let valence = 0, arousal = 0, total = 0;
    for (const [emotion, score] of Object.entries(scores)) {
      valence += score * (_VALENCE[emotion] !== undefined ? _VALENCE[emotion] : 0);
      arousal += score * (_AROUSAL[emotion] !== undefined ? _AROUSAL[emotion] : 0);
      total   += score;
    }
    if (total > 0) { valence /= total; arousal /= total; }
    valence = Math.max(-1, Math.min(1, valence));
    arousal = Math.max(-1, Math.min(1, arousal));

    self.postMessage({
      module:     'vision.emotion',
      emotion:    topEmotion,
      confidence: +confidence.toFixed(3),
      valence:    +valence.toFixed(3),
      arousal:    +arousal.toFixed(3),
    });
  } catch (e) {
    console.warn('[cv-emotion] detect error:', e.message);
    try { bitmap.close(); } catch (_) {}
    self.postMessage({
      module: 'vision.emotion',
      emotion: 'none', confidence: 0, valence: 0, arousal: 0,
    });
  }
};

_init();

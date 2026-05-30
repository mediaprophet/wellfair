'use strict';

// ── OpenCV placeholder — emotional recognition + pulse estimation ──────────────
// This stub reserves the API surface for future OpenCV.js integration.
// All processing is fully client-side — no frames ever leave the device.
//
// To activate: load OpenCV.js, set VaultCV.isAvailable = () => true,
// implement analyzeFrame() using cv.Mat + facial landmark detection.

const VaultCV = {
  isAvailable: () => false, // set true when OpenCV.js loads successfully

  // Analyse a single video frame. Returns null until OpenCV is available.
  // When implemented, returns:
  //   { emotion: string, confidence: number, pulse_bpm: number|null }
  analyzeFrame: async (_videoElement) => null,
};

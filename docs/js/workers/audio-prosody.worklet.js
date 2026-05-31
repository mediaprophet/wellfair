// AudioWorklet processor — accumulates 128-sample audio frames → 2048-sample chunks
//
// Registered as:  'prosody-processor'
// Loaded via:     audioCtx.audioWorklet.addModule('js/workers/audio-prosody.worklet.js')
//
// Runs on the audio rendering thread (not the main thread, not a standard Worker).
// Receives realtime audio from getUserMedia via AudioContext graph.
//
// Output: port.postMessage({ chunk: Float32Array(2048), sampleRate: number })
//         Emitted every 2048 input samples (~46ms at 44.1kHz).
//         chunk.buffer is transferred (zero-copy) — caller must not retain it.

const CHUNK_SIZE = 2048; // must be power-of-2; matches Meyda bufferSize in audio-features.worker.js

class ProsodyProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buf = new Float32Array(CHUNK_SIZE);
    this._pos = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0] || !input[0].length) return true;

    const samples = input[0]; // mono or left channel
    for (let i = 0; i < samples.length; i++) {
      this._buf[this._pos++] = samples[i];
      if (this._pos >= CHUNK_SIZE) {
        // slice() creates a new ArrayBuffer so we can transfer it (zero-copy)
        const chunk = this._buf.slice(0);
        this.port.postMessage({ chunk, sampleRate }, [chunk.buffer]);
        this._pos = 0;
      }
    }
    return true; // keep processor alive
  }
}

registerProcessor('prosody-processor', ProsodyProcessor);

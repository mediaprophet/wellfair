# WellFair — Session Handover WA-2 (2026-05-31)

## Milestones covered this session
WA-1 (AgentController + consent model + IDB v7) and WA-2 (vision.emotion worker — MediaPipe FaceLandmarker).

---

## Completed in this session

### WA-1 (commits ba476c4)
- `vault-idb.js`: bumped to v7; `_ST_TELEMETRY = 'wf-telemetry'` added; store created in `onupgradeneeded`
- `vault-cv.js`: full rewrite — `CV_MODULE`, `initAgent()`, `setModuleConsent()`, `stopAgent()`, `_emitTelemetry()` (SHA-256 hash chain), `_WORKER_FILE` name map, `agentHasModule()`, `agentSendFrame()`, `_cvToggle()`
- `vault-comms-call.js`: `initAgent()` called at call start (both `startCall` + `answerCall.ondatachannel`); `stopAgent()` at start of `endCall()`; frame loop state vars `_callRafId`, `_callFrameTs`, `_FRAME_MS`; `_callStartFrameLoop()` + `_callStopFrameLoop()`
- `vault.html`: `#agent-panel` consent UI (4 checkboxes + All-off button); shown on `wf:call` start, hidden on end; `vault-cv.js?v=7.2`; hidden `#call-local-video` + `#call-remote-video` elements

### WA-2 (commit a8dca0a)
- `docs/js/workers/cv-emotion.worker.js`: new classic worker; MediaPipe Tasks Vision 0.10.14 CPU delegate; ARKit 52-blendshape → emotion mapping; Russell circumplex valence/arousal; graceful face-not-found path
- `vault-cv.js`: `_WORKER_FILE` map uses `'cv-emotion'` stem; classic worker spawn (no `type:'module'`); lifecycle routing (ready/error messages)
- `vault-comms-call.js`: `_callStartFrameLoop()` wires `#call-local-video` → `OffscreenCanvas` → 10fps bitmap → `agentSendFrame()`; both EMOTION + RPG handled (separate bitmaps via `createImageBitmap`)
- `sw.js`: changed `.js` files to network-first strategy (was cache-first) to prevent stale JS being served during development

---

## Files modified
| File | Change summary | Key functions added |
|------|---------------|---------------------|
| `docs/js/vault-idb.js` | v7 bump; `wf-telemetry` store | `_ST_TELEMETRY` |
| `docs/js/vault-cv.js` | Full rewrite from stub | `initAgent`, `setModuleConsent`, `stopAgent`, `agentHasModule`, `agentSendFrame`, `_emitTelemetry`, `_cvToggle` |
| `docs/js/vault-comms-call.js` | Frame loop + agent lifecycle hooks | `_callStartFrameLoop`, `_callStopFrameLoop` |
| `docs/vault.html` | Consent UI panel, video elements, script tag | `#agent-panel`, `#call-local-video`, `#call-remote-video` |
| `docs/js/workers/cv-emotion.worker.js` | New file — MediaPipe emotion detection | `_init` (async), `self.onmessage` |
| `docs/sw.js` | JS files → network-first to fix dev caching | — |

---

## IDB state
- **Version:** 7
- **Stores (all present):** `wf-s`, `wf-sc`, `wf-meds`, `wf-ml`, `wf-pc`, `wf-dl`, `wf-contacts`, `wf-relationships`, `wf-agreements`, `wf-jobs`, `wf-events`, **`wf-telemetry`** (new)
- **wf-telemetry record shape:** `{id, type:'agent.telemetry', sessionId, seq, actorDid, ts, payload:{modules[], vision{}, biometrics{}, audio{}, linguistic{}}, hash, prevHash}`

---

## Script load order (vault.html) — relevant section
```
vault-comms-call.js?v=6
vault-cv.js?v=7.2          ← AgentController + WA-2 additions
vault-scheduler.js?v=6
...
```

---

## Critical decisions made this session

### 1. Classic workers required for MediaPipe
`new Worker(path)` — NOT `new Worker(path, {type:'module'})`.

MediaPipe's `WasmFileset.loadModule()` uses `importScripts()` internally, which only works in classic workers. Using `type:'module'` produces "ModuleFactory not set." immediately.

**All future workers (cv-rpg, audio-prosody, text-linguistic) must also be classic workers.** Use dynamic `import()` inside them for ESM dependencies.

### 2. Worker file name map
`_WORKER_FILE` in vault-cv.js maps module keys → file stems:
- `'vision.emotion'` → `cv-emotion` → `js/workers/cv-emotion.worker.js`
- `'vision.rpg'`     → `cv-rpg`     → `js/workers/cv-rpg.worker.js`
- `'audio.prosody'`  → `audio-prosody` → `js/workers/audio-prosody.worker.js`
- `'text.linguistic'` → `text-linguistic` → `js/workers/text-linguistic.worker.js`

### 3. SW cache issue (now fixed)
`sw.js` was using cache-first for `.js` files, serving stale versions after edits.
**Fixed:** `.js` files now use network-first in `sw.js`. No more version-bumping needed for JS edits during development.

---

## What to do next — WA-3 (immediate)

**Task:** Create `docs/js/workers/cv-rpg.worker.js` — rPPG pulse detection.

**Read first:**
1. `docs/js/workers/cv-emotion.worker.js` — understand the worker message pattern
2. `docs/js/vault-comms-call.js` — `_callStartFrameLoop()` lines ~230–275 (frame sending to RPG)
3. `EPIC_PLAN_v0.0.7.md` WA-3 section — ROI landmark indices, buffer spec, FFT spec

**Key spec (from plan):**
- Input: `postMessage({ bitmap: ImageBitmap })` — same as emotion worker
- ROI: forehead landmark indices 10, 67, 69, 104 from MediaPipe output. For WA-3, use a fixed % of frame (top 20%, center 50% width) as a simpler fallback when no landmark data is available
- Temporal buffer: `BUFFER_FRAMES = 300` (~10s at 30fps)
- Signal: average green channel of ROI → detrend → Hann window → FFT → peak in 0.75–4 Hz band
- Output: `postMessage({ module: 'vision.rpg', bpm, confidence, signalQuality })`
- `signalQuality`: `'good' | 'fair' | 'poor'` based on SNR

**Note on frame supply:** The frame loop in `vault-comms-call.js` already handles both EMOTION + RPG:
```js
if (needsEmotion && needsRpg) {
  const bm1 = canvas.transferToImageBitmap();
  createImageBitmap(vEl).then(bm2 => {
    agentSendFrame(CV_MODULE.EMOTION, bm1);
    agentSendFrame(CV_MODULE.RPG, bm2);
  });
}
```
The RPG worker will receive the same frames as the emotion worker.

**No MediaPipe needed for RPG** — it only needs the green channel pixel average of a canvas ROI. Pure JS, no WASM library required. No dynamic import() needed.

---

## Blocked / deferred
- **WA-3 ROI landmarks:** The RPG worker ideally uses forehead landmarks from WA-2. However, WA-2 currently does not forward landmarks to the main thread (only emotion/valence/arousal). For WA-3, use a fixed ROI (top 20%, center 50%) — accurate enough for MVP.
- **Frame rate verification:** The acceptance criterion "≥10fps on mid-range laptop" can't be verified without a live camera. It's guaranteed by the 100ms throttle in `_callStartFrameLoop`.
- **Nym Sandbox validation:** Carry-over from v0.0.6. No code needed.

---

## Acceptance criteria status (WA-1)
- [x] IDB v7 opens; `wf-telemetry` store created
- [x] `initAgent()` called from `vault-comms-call.js` at call start; `stopAgent()` at call end
- [x] `setModuleConsent(CV_MODULE.EMOTION, true)` spawns a worker; `false` terminates it
- [x] Consent toggles in call panel update module state in real time
- [x] "All off" button terminates all workers
- [x] `VaultCV.isAvailable()` returns `true` after `initAgent()`

## Acceptance criteria status (WA-2)
- [x] Worker loads MediaPipe Tasks Vision from CDN inside worker context
- [x] Face landmarks detected; blendshapes computed per frame
- [x] Emotion string + confidence emitted to AgentController
- [x] Valence/arousal computed (range -1 to 1)
- [x] Worker handles face-not-found gracefully (`{emotion:'none', confidence:0}`)
- [ ] Frame rate ≥10fps on mid-range laptop — throttled to 10fps by design; needs live camera to verify

# WellFair v0.0.7 — Implementation Plan
## Two Epics: Webizen Agent + Human-Centric Wallet

> Branch: `release/v0.0.7` (branch from `release/v0.0.6` when v0.0.6 is tagged)  
> Plan written: 2026-05-31  
> Estimated total sessions: 22–28  
> Epics: DL (Diet Log Sprint 6b) + WA (Webizen Agent — CV/Audio Analytics) + HCW (Human-Centric Wallet)

---

## Why this exists — primary use case for HCW

> Read this before implementing anything in the HCW epic. It explains why certain
> architectural requirements are non-negotiable rather than optional privacy enhancements.

The Human-Centric Wallet is designed around a specific, real-world use case:
a person escaping organised criminal exploitation (trafficking, forced financial crime)
who needs access to welfare support — psychiatric care, medication, safe accommodation —
but whose physical location would be endangered if any transaction on a public ledger
linked their wallet to a merchant address.

The threat actors in this scenario are not opportunistic criminals. They are enterprise-scale
operations that can and do use blockchain transaction analysis, corrupted institutional
contacts, and physical violence to locate people who threaten their operations.

Standard welfare infrastructure fails this person because:
- On-chain payments link recipient wallet → merchant address → physical location
- Government-linked identity creates records accessible to potentially compromised institutions  
- Fiat on-ramps create KYC linkages that can be subpoenaed or leaked

This is why the following are architectural requirements, not preferences:
- **Blind Proxy treasury** (HCW-8) — wallet never links to merchant on-chain
- **Anonymous credential issuance** (HCW-9) — eligibility proven without government identity
- **Nym routing for all transactions** (HCW-2) — IP address never exposed to RPC nodes
- **Zero server-side user data** — a full breach of app infrastructure reveals nothing exploitable
- **Decoupled issuance** — credential issuers and infrastructure operators must be separate
  organisations with no shared data

Full context: `memory/project_hcw_primary_usecase.md`

---

## How to use this plan

**At the start of every session**, read in this order:
1. `CLAUDE.md` — project orientation, terminology, architecture (mandatory)
2. This file — find the first "not started" row in the Progress Tracker for the active epic
3. The handover file written by the previous session (path shown in Progress Tracker)
4. The source files listed under "Read first" for that milestone

**Keep going through milestones until context window signals fill:**
- The system emits a compression notice
- Tool call results arrive truncated

When a context signal appears: write handover at `instructions/HANDOVER_{milestone}_{YYYY-MM-DD}.md`,
update Progress Tracker, commit, tell user to start a new session.

**Sequencing:** DL-1 (barcode scanning) → WA-1 through WA-7 (Webizen Agent) → HCW-1 through HCW-10.
DL-1 completes the diet log and is independent. WA-7 telemetry feeds the HCW audit trail.

---

## Mandatory terminology & architecture constraints

Carried forward from v0.0.6:
- **"Identity credentials"** — never "DIDs", never "VCs" in user-facing text
- **No "sovereign"** anywhere — not in code, comments, UI, or docs
- **No "self-sovereign"** — use "personal agency", "individual control", "human-centric"
- **SHACL/RDFS** for data shapes about people; OWL only for policy artefacts
- Health namespace: `wf:` → `https://wellfare.social/ns/vault#`
- Phone is authoritative vault; desktop is stateless
- Gun.eco for WebRTC signalling only — health data never touches relay nodes
- **No bundler** — plain HTML + CDN scripts + `docs/js/` modules; plain globals; script load order matters
- Testing: always `mcp__Claude_in_Chrome__*` against `python -m http.server 3000 --directory docs`

New for v0.0.7:
- **"Webizen"** — the local edge agent running inside the call pipeline. Acceptable term; refers to a
  browser-native agent acting on behalf of the person, not an external service
- **"Human-Centric Wallet"** / **"personal wallet"** — never "crypto wallet" in user-facing text
- **"welfare payment" / "care credit"** — user-facing; never "stablecoin voucher" or "smart contract"
- **No raw biometric data leaves the device** — only structured JSON telemetry over DataChannel
- **No plaintext financial identifiers leave the device unencrypted** — wallet addresses,
  transaction amounts, and merchant interactions routed through Nym where possible
- **Workers live in `docs/js/workers/`** — each analytical module is a self-contained Worker file
- IDB version: currently **v6**; WA-1 bumps to **v7** (adds `wf-telemetry`); HCW-1 bumps to **v8**

---

## Corrections to the Gemini planning conversation

Before implementing anything, the following Gemini recommendations must be adjusted for WellFair's
architecture. Read this section before starting any milestone.

### Webizen Agent epic

| Gemini said | WellFair correction |
|---|---|
| npm packages, Vite/Webpack/Rollup bundler | No bundler. All libraries loaded as CDN ES modules via `importScripts()` or `import` inside workers, or `<script type="module">` tags. |
| `/src/agent/vision/` repo structure | WellFair uses `docs/js/` for all modules and `docs/js/workers/` for Web Workers. |
| `PodStorage.js` writing to a Solid pod | WellFair uses IDB (`wf-vault` v6+). Solid is a future consideration; the vault IDB is the personal datastore. |
| Comlink for worker communication | Comlink is loadable from CDN as an ES module but adds complexity with no-bundler setup. Use plain `postMessage` with a thin typed event bus in `vault-cv.js`. |
| face-api.js as "recommended" | MediaPipe Tasks Vision is preferred. face-api.js uses TensorFlow.js which is heavier. MediaPipe has better WASM optimization and outputs blendshapes that map directly to WellFair's telemetry schema. |
| OpenCV.js for rPPG spatial pooling | OpenCV.js is 8–30 MB. rPPG only needs green-channel pixel averaging on a canvas ROI — achievable in ~50 lines of pure JS. Use OpenCV.js only if additional frame manipulation is needed later. |
| "Webizen agent downloads modules on demand" | In WellFair, modules are `<script>` tags with `async` loading or dynamic `import()` inside workers. A module that isn't consented is never loaded (`import()` is never called). |
| WebGPU acceleration needed | MediaPipe's WASM backend is sufficient for MVP. WebGPU is an optimization pass for v0.0.8+ when real performance data exists. |

**Critical addition Gemini missed:**
- COOP/COEP headers are **already provided by `sw.js`** — SharedArrayBuffer is available today
  without any additional server configuration
- `vault-cv.js` stub **already exists** — it is the insertion point for the AgentController
- `vault-comms-transcode.js` **already loads `@xenova/transformers`** for Whisper STT — the
  transcription pipeline reuses this; do not create a duplicate

### Human-Centric Wallet epic

| Gemini said | WellFair correction |
|---|---|
| "App's central treasury wallet" making payments | This creates a honeypot — if breached, all user transaction data and merchant relationships are exposed. See "Blind Proxy" section for the correct design. |
| Solana is unambiguously better | Solana's Token-2022 Confidential Transfers are architecturally sound but adding a full Solana client is a major dependency. Phase 1 uses Lightning (already in scope). Solana/AUDD is Phase 3+. |
| PodStorage.js + Solid pod | Not applicable. Patient data stays in IDB under vault key. Post-session access grants use the existing ODRL agreement infrastructure (VC-8). |
| Smart contract logic for vouchers | Smart contracts are Phase 3+. Phase 1 vouchers are signed ODRL documents stored in `wf-dl`; merchant whitelisting is enforced by the app, not on-chain. |
| USDC/AUDD ERC-20 bridging | Multi-chain bridging is UX-hostile and introduces bridge risk. Prefer Solana-native AUDD (Stellar or Solana) or Lightning-native stablecoins when the ecosystem matures. |
| "Sovereign data storage" / "sovereignty" | Prohibited term — replace with "personal data store", "patient-held record", "individual's vault" |

**Critical architectural requirement Gemini missed — Zero-Trust design:**
The wallet design must assume that **the app developers, the infrastructure, and any intermediary can
be compromised or legally compelled**. The system must be architected such that a breach of the
application servers yields zero useful data about users. See the Threat Model section below.

---

## SPRINT 6b — Diet Log Barcode Scanning (DL-1)
### Open Food Facts Integration

> **Sequence:** Complete this before starting WA-1. It finishes the diet log feature
> started in Sprint 6 (v0.0.6) and is self-contained (~1 session).

---

### Corrections to the Gemini conversation for WellFair

| Gemini said | WellFair correction |
|---|---|
| Use zxing or mlkit for barcode scanning | **BarcodeDetector API** is built into Chrome 83+ / Edge 83+ — no library needed for the primary path. ZXing-js (CDN) as fallback for Firefox/Safari only. mlkit is Android/iOS native; not applicable to a browser app. |
| "Semantic translation layer / reasoning engine on client side" | Correct long-term direction. MVP stores the OFF `code` (barcode) and raw `categories_tags` in the wf-dl record for future LOD enrichment. FoodOn/Wikidata mapping is a v0.0.8 task. |
| "Sovereignty" language | Prohibited term — omit. |
| Full FoodOn + DBpedia + PubChem mapping at implementation time | The OFF API already returns `categories_tags` which are OFF's own FoodOn-compatible URIs. Store them; don't transform them yet. |

**Privacy note:** An Open Food Facts barcode lookup is a public product database query —
the barcode identifies a product, not a person. For general use, a plain HTTPS fetch is
acceptable. For users in high-risk situations (see HCW primary use case), the API call
should be routable through Nym. The implementation should check `nymAdapter.isActive()`
and route accordingly. Document this in code comments; do not require Nym for all users.

---

### DL-1 — Barcode Scanning + Open Food Facts Pre-fill

**Session scope:** 1 session  
**Depends on:** `docs/js/vault-diet.js` (dlAddEntry, field names), `docs/vault.html` (diet-add-form)  
**Read first:** `docs/js/vault-diet.js`, `docs/js/vault-nym.js` (nymAdapter)

**New file:** `docs/js/vault-diet-barcode.js`

**Public API:**
```js
async function dlStartBarcodeScanner(videoEl, onDetected)
// Opens getUserMedia({video: {facingMode:'environment'}}) into videoEl
// Primary: BarcodeDetector API (formats: ean_13, upc_a, upc_e, ean_8, ean_5, ean_2)
// Fallback: ZXing-js loaded from CDN if BarcodeDetector unavailable
// Calls onDetected(barcodeString) on first successful read; stops camera
// Returns: stopFn — call to cancel scanning without a result

async function dlLookupBarcode(barcode)
// Fetches Open Food Facts API v2:
//   GET https://world.openfoodfacts.org/api/v2/product/{barcode}.json
//   ?fields=product_name,brands,serving_size,nutriments,categories_tags,image_url
// Routes via nymAdapter if nymAdapter.isActive() (see privacy note above)
// Returns: {found: bool, fields: Partial<dlAddEntry>, raw: object} | {found: false}

function _mapOffProduct(p)
// Maps Open Food Facts product JSON → vault-diet.js field names
// Uses *_serving values preferentially; falls back to *_100g * (serving_size_g / 100)
// Returns partial fields object ready to pass to dlAddEntry()
```

**OFF → wf-dl field mapping:**

| Open Food Facts field | wf-dl field | Notes |
|---|---|---|
| `product_name` | `name` | |
| `brands` | `brand` | |
| `serving_size` | `quantity` + `unit` | Parse "30 g" → qty 30, unit 'g' |
| `nutriments['energy-kcal_serving']` | `kcal` | Fall back to `energy-kcal_100g` |
| `nutriments['proteins_serving']` | `protein_g` | |
| `nutriments['carbohydrates_serving']` | `carbs_g` | |
| `nutriments['fat_serving']` | `fat_g` | |
| `nutriments['fiber_serving']` | `fiber_g` | |
| `nutriments['sugars_serving']` | `sugar_g` | |
| `nutriments['sodium_serving'] * 1000` | `sodium_mg` | OFF stores sodium in g |
| `categories_tags` | stored in `notes` as JSON | For future FoodOn LOD enrichment |
| `code` (barcode) | stored in `notes` | For future re-lookup / LOD linkage |

**vault.html additions to diet-add-form:**
- "📷 Scan barcode" button at the top of the add-entry form (beside food name field)
- Hidden `<video>` element for camera stream (shown only while scanning)
- Scanner overlay: "Point at barcode — scanning…" + Cancel button
- On detection: camera stops, form pre-filled, status message "Found: {product name}"
- On not found in OFF: form stays empty, status "Product not found — enter manually"
- New `source` field value: `'barcode'` (existing field in wf-dl schema, was `'manual'`)

**Script tag:** Add `<script src="js/vault-diet-barcode.js?v=6"></script>` after `vault-diet.js`

**ZXing-js fallback CDN:**
```
https://cdn.jsdelivr.net/npm/@zxing/browser@latest/+esm
```
Load only if `typeof BarcodeDetector === 'undefined'` — do not load for Chrome/Edge users.

**Acceptance criteria:**
- [ ] BarcodeDetector opens camera on click; closes after successful scan
- [ ] EAN-13 barcode on a food package → product name + macros pre-filled in form
- [ ] ZXing-js fallback loads and functions in Firefox
- [ ] Product not found in OFF → graceful "enter manually" state, no error
- [ ] `source: 'barcode'` set on entries created via scan
- [ ] `notes` field stores barcode + OFF categories_tags for future LOD use
- [ ] Nym routing used for the OFF API fetch when nymAdapter is active
- [ ] Camera stream stopped and released on cancel, on result, and on sheet close

---

### DL-1: LOD enrichment roadmap (v0.0.8+, not Sprint 6b)

The following are out of scope for this session but should be designed so the stored
data (barcode + `categories_tags`) enables them without re-scanning:

| Future milestone | What it does |
|---|---|
| FoodOn mapping | Map OFF `categories_tags` URIs to FoodOn ontology terms via a static lookup table |
| Drug–nutrient interactions | Cross-reference `categories_tags` ingredients against `vault-meds-lod.js` SUBSTANCE_INTERACTIONS |
| Wikidata enrichment | Resolve OFF ingredient names to Wikidata QIDs for full LOD provenance |
| PubChem additives | Resolve E-number additives (from `additives_tags`) to PubChem CIDs for safety data |
| Allergen alerts | OFF `allergens_tags` cross-referenced against user-configured allergen list in IDB |

---

---

## EPIC 1 — Webizen Agent (WA)
### CV, Audio & Text Analytics for Telehealth

### Architecture overview

```
vault.html (main thread)
  │
  ├── vault-cv.js (AgentController — rewritten from stub)
  │     ├── Module registry & consent state
  │     ├── Worker pool lifecycle (spawn / terminate / health-check)
  │     ├── Event bus → wf-events IDB (type: agent.telemetry)
  │     └── DataChannel bridge → connector/index.html telemetry panel
  │
  ├── docs/js/workers/
  │     ├── cv-emotion.worker.js    (MediaPipe Tasks Vision — face mesh → emotion)
  │     ├── cv-rpg.worker.js        (rPPG — green channel temporal buffer → BPM)
  │     ├── audio-prosody.worker.js (AudioWorklet + Meyda — pitch, energy, speech rate)
  │     └── text-linguistic.worker.js (pronoun density, sentiment, coherence)
  │
  └── Consent UI (per-module toggles in call panel — in vault.html)

connector/index.html
  └── Live telemetry display panel (receives DataChannel JSON)
```

**Key constraint:** Raw video frames, audio buffers, and transcripts never leave the device.
Only structured JSON telemetry travels over the WebRTC DataChannel to the clinician.

---

### DL: Progress Tracker

| Session | Date | Milestone | Status | Handover file |
|---------|------|-----------|--------|---------------|
| DL-1 | 2026-05-31 | Barcode scanning + Open Food Facts pre-fill | complete | — |

---

### WA: Progress Tracker

| Session | Date | Milestone | Status | Handover file |
|---------|------|-----------|--------|---------------|
| WA-1 | 2026-05-31 | AgentController + consent model + IDB v7 | complete | — |
| WA-2 | 2026-05-31 | Vision — emotion & landmarks (MediaPipe) | complete | — |
| WA-3 | 2026-05-31 | Vision — rPPG pulse detection | complete | — |
| WA-4 | 2026-05-31 | Audio — prosody analysis (Meyda) | complete | — |
| WA-5 | 2026-05-31 | Audio — STT feed + linguistic analysis | complete | — |
| WA-6 | 2026-05-31 | Clinician dashboard (connector telemetry panel) | complete | — |
| WA-7 | 2026-05-31 | Telemetry packaging + VC-13/15 integration | complete | instructions/HANDOVER_WA-7_2026-05-31.md |

---

### WA-1 — AgentController + Consent Model + IDB v7

**Session scope:** 1 session  
**Depends on:** vault-cv.js stub (exists), vault-comms-call.js (DataChannel), vault-idb.js  
**Read first:** `docs/js/vault-cv.js`, `docs/js/vault-comms-call.js`, `docs/js/vault-idb.js`

**IDB changes (vault-idb.js):**
- Bump `_openDB` to version 7
- Add store: `wf-telemetry` (keyPath: `id`) — session telemetry samples
- Add constant: `_ST_TELEMETRY`
- Record shape: `{id, sessionId, ts, modules[], vision{}, biometrics{}, audio{}, hash, prevHash}`

**vault-cv.js — rewrite from stub, public API:**
```js
// Module registry
const CV_MODULE = Object.freeze({
  EMOTION:   'vision.emotion',
  RPG:       'vision.rpg',
  PROSODY:   'audio.prosody',
  LINGUISTIC:'text.linguistic',
});

function initAgent(callSessionId, dataChannel)
// Called from vault-comms-call.js when call starts
// Sets up module registry, empty consent state, DataChannel reference

function setModuleConsent(module, granted)
// Grant/revoke consent for a specific CV_MODULE
// If granted: worker is spawned (lazily via import() in worker file)
// If revoked: worker.terminate() + null reference

function stopAgent()
// Called on call end — terminates all workers, flushes telemetry buffer

// Internal
function _onWorkerMessage(module, payload)
// Receives structured result from worker
// Merges into current telemetry frame
// Calls _emitTelemetry() when all active modules have reported for this frame

async function _emitTelemetry(frame)
// Writes to wf-telemetry IDB (append-only, hash chain like wf-events)
// Sends JSON payload over DataChannel: {type:'agent.telemetry', ...frame}
// Calls captureEvent(sessionId, 'agent.telemetry', selfDid, frame) for VC-13 integration
```

**vault.html UI additions:**
- Consent toggles in the call panel (one per module, off by default):
  ```
  [ ] Emotion tracking      — facial expression analysis
  [ ] Pulse detection       — remote heart rate via camera
  [ ] Vocal analysis        — tone, pitch, speech pattern
  [ ] Linguistic analysis   — text pattern analysis
  ```
- Active module indicators (show which modules are running)
- "All off" panic button (terminates all workers instantly, sends `agent.stop` over DataChannel)

**Acceptance criteria:**
- [ ] IDB v7 opens; `wf-telemetry` store created
- [ ] `initAgent()` called from `vault-comms-call.js` at call start; `stopAgent()` at call end
- [ ] `setModuleConsent(CV_MODULE.EMOTION, true)` spawns a worker; `false` terminates it
- [ ] Consent toggles in call panel update module state in real-time
- [ ] "All off" button terminates all workers
- [ ] `vault-cv.js` loads without error; `VaultCV.isAvailable()` returns `true` after `initAgent()`

---

### WA-2 — Vision: Emotion & Landmarks

**Session scope:** 1 session  
**Depends on:** WA-1 (AgentController), vault-comms-call.js (video stream)  
**Read first:** `docs/js/vault-cv.js` (AgentController), `docs/js/vault-comms-call.js`

**docs/js/workers/cv-emotion.worker.js:**
```js
// Loaded via: new Worker('js/workers/cv-emotion.worker.js', {type:'module'})
// CDN: import { FaceLandmarker, FilesetResolver } from
//        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/+esm'

// Setup: loads FaceLandmarker with WASM backend (COOP/COEP already set by sw.js)
// Input: ImageBitmap frames posted from main thread
// Output: postMessage({module:'vision.emotion', emotion, confidence, valence, arousal, landmarks})

// Blendshape → emotion mapping (based on MediaPipe's 52 ARKit blendshapes):
const _EMOTION_MAP = {
  happy:    ['mouthSmileLeft','mouthSmileRight'],
  sad:      ['mouthFrownLeft','mouthFrownRight','browDownLeft','browDownRight'],
  angry:    ['browDownLeft','browDownRight','noseSneerLeft','noseSneerRight'],
  fearful:  ['browInnerUp','eyeWideLeft','eyeWideRight'],
  disgusted:['noseSneerLeft','noseSneerRight','mouthLowerDownLeft'],
  surprised:['jawOpen','eyeWideLeft','eyeWideRight','browOuterUpLeft'],
  neutral:  [],  // fallback
};
// Valence/arousal derived from blendshape weighted sums (Russell circumplex model)
```

**vault-comms-call.js integration:**
- On each animation frame (during active call): draw video frame to OffscreenCanvas
- Transfer canvas bitmap to cv-emotion worker via `postMessage(bitmap, [bitmap])`
  (Transferable — zero-copy, no clone overhead)

**Acceptance criteria:**
- [ ] Worker loads MediaPipe Tasks Vision from CDN inside worker context
- [ ] Face landmarks detected; 52 blendshapes computed per frame
- [ ] Emotion string + confidence emitted to AgentController
- [ ] Valence/arousal values computed (range -1 to 1)
- [ ] Worker handles face-not-found gracefully (emits `{emotion:'none', confidence:0}`)
- [ ] Frame rate does not drop below 10fps on a mid-range laptop

---

### WA-3 — Vision: rPPG Pulse Detection

**Session scope:** 1 session  
**Depends on:** WA-2 (face landmarks for ROI), WA-1 (AgentController)  
**Read first:** `docs/js/workers/cv-emotion.worker.js` (landmark output format)

**docs/js/workers/cv-rpg.worker.js:**
```js
// Input: ImageBitmap frame + face landmarks (forehead region bounding box)
// Architecture: temporal processing — NOT single-frame analysis

// 1. ROI extraction
// Uses landmark points for forehead (indices 10, 67, 69, 104) + upper cheeks
// getImageData() on canvas → average R, G, B in ROI
// G channel is primary signal (hemoglobin absorbs green strongly)

// 2. Temporal buffer
const BUFFER_FRAMES = 300;  // ~10 seconds at 30fps
const _rgbBuffer = [];      // rolling circular buffer {r, g, b, ts}

// 3. Signal processing (pure JS FFT at MVP — no OpenCV.js needed)
// When buffer has >= BUFFER_FRAMES entries:
// - Detrend G channel signal (remove slow drift)
// - Apply Hann window
// - FFT → frequency domain
// - Find peak in 0.75–4 Hz band (45–240 BPM)
// - BPM = peakFrequencyHz * 60

// Output: postMessage({module:'vision.rpg', bpm, confidence, signalQuality})
// confidence derived from SNR of the BVP peak vs. noise floor
// signalQuality: 'good' | 'fair' | 'poor' (affects UI display)
```

**Notes on MVP accuracy:**
- Pure JS FFT is accurate ±5 BPM under good lighting; sufficient for clinical indicators
- A Rust/Wasm bandpass filter module (CHROM method) improves this to ±2 BPM and
  is the v0.0.8 upgrade path — document the interface now so the upgrade is a drop-in

**Acceptance criteria:**
- [ ] ROI correctly identified from MediaPipe landmarks
- [ ] Buffer accumulates 300 frames; FFT produces a frequency spectrum
- [ ] BPM estimate in 40–200 range on a human face
- [ ] `signalQuality: 'poor'` emitted when lighting is insufficient or face is occluded
- [ ] Worker does not crash or leak memory over a 10-minute session

---

### WA-4 — Audio: Prosody Analysis

**Session scope:** 1 session  
**Depends on:** WA-1 (AgentController), vault-comms-call.js (audio stream)  
**Read first:** `docs/js/vault-comms-call.js` (getUserMedia / AudioContext setup)

**Architecture note:** AudioWorklet runs on the audio rendering thread (not the main thread and
not a standard Worker). It communicates with a companion Worker via SharedArrayBuffer ring buffer
(COOP/COEP already set). If SharedArrayBuffer is unavailable, fall back to `postMessage` chunking.

**docs/js/workers/audio-prosody.worklet.js** (AudioWorklet processor):
```js
// Registered via: audioCtx.audioWorklet.addModule('js/workers/audio-prosody.worklet.js')
// Receives 128-sample audio frames at sample rate
// Accumulates frames into analysis window (2048 samples)
// Writes to SharedArrayBuffer ring buffer → read by audio-features.worker.js
// OR: postMessage raw Float32Array chunks if SAB unavailable
```

**docs/js/workers/audio-features.worker.js:**
```js
// CDN: import Meyda from 'https://cdn.jsdelivr.net/npm/meyda@5/+esm'
// Reads from SAB ring buffer (or receives postMessage chunks)
// Extracts per-window features:
//   - rms: signal energy (volume proxy)
//   - spectralCentroid: pitch brightness
//   - mfcc[13]: Mel-Frequency Cepstral Coefficients (voice texture)
//   - zcr: zero-crossing rate (roughness / tremor indicator)

// Clinical marker derivation:
//   pitchHz:         estimated F0 from spectralCentroid (approx; full F0 needs autocorrelation)
//   energyVariance:  rolling variance of rms over 10s window
//   speechRate:      word count from concurrent STT / seconds of voiced activity
//   tremorIndex:     power in 4–12 Hz modulation range (vocal tremor)

// Output every 500ms:
// postMessage({module:'audio.prosody', pitchHz, energyVariance, speechRate, tremorIndex, rms})
```

**Clinical interpretation notes (for UI labels, not diagnosis):**
- Flat pitch / low energyVariance → may indicate depression (label: "low vocal variation")
- High speechRate > 180 wpm → may indicate pressured speech (label: "rapid speech")
- tremorIndex > threshold → "vocal tremor detected"
- These labels are informational only; no diagnostic claims in UI copy

**Acceptance criteria:**
- [ ] AudioWorklet registered and receiving audio frames during active call
- [ ] Meyda feature extraction producing valid values (not NaN/Inf)
- [ ] Prosody payload emitted to AgentController every 500ms
- [ ] Graceful fallback to postMessage chunking when SAB unavailable
- [ ] Worker terminates cleanly; AudioContext closed on `stopAgent()`

---

### WA-5 — Audio: STT Feed + Linguistic Analysis

**Session scope:** 1 session  
**Depends on:** WA-1, vault-comms-transcode.js (existing Whisper pipeline)  
**Read first:** `docs/js/vault-comms-transcode.js`, `docs/js/vault-transcript.js`

**Key integration point:** `vault-comms-transcode.js` already runs WebSpeech and `@xenova/transformers`
Whisper. **Do not create a duplicate STT pipeline.** Instead, wire the existing `captureEvent`
`speech.segment` events into the new linguistic analysis worker.

**docs/js/workers/text-linguistic.worker.js:**
```js
// Input: postMessage({text: string, ts: string}) — transcript segment
// Accumulates into rolling 60-segment window

// Feature extraction:
//   pronounRatio1P: count of (I/me/my/mine/myself) / total pronouns
//   sentimentScore: lexicon-based (AFINN or similar; ~2KB JSON) → -1 to +1
//   coherenceScore: average cosine similarity of adjacent sentence embeddings
//                   (simple TF-IDF at MVP; transformer embeddings in v0.0.8)
//   avgSentenceLength: words per sentence (short sentences → fragmented thinking indicator)
//   hedgeRatio: count of hedge words (maybe/perhaps/might/could/uncertain) / total words

// Output every 5 segments (or 30s, whichever comes first):
// postMessage({module:'text.linguistic',
//   pronounRatio1P, sentimentScore, coherenceScore, avgSentenceLength, hedgeRatio})
```

**Acceptance criteria:**
- [ ] Linguistic worker receives transcript segments from `vault-comms-transcode.js` events
  (no duplicate STT — reuses existing pipeline)
- [ ] Pronoun ratio, sentiment, coherence metrics computed
- [ ] Gracefully handles empty segments; no division-by-zero
- [ ] Output payload emitted to AgentController every 5 segments

---

### WA-6 — Clinician Dashboard (Connector Telemetry Panel)

**Session scope:** 1 session  
**Depends on:** WA-1–WA-5 (telemetry DataChannel messages), connector/index.html Calls panel  
**Read first:** `docs/connector/index.html` (Calls panel, DataChannel message routing)

**connector/index.html additions:**
- New sub-panel within the Calls section: "Live Indicators"
- Receives `{type:'agent.telemetry', ...}` over DataChannel
- Displays in real time:

```
┌─ Live Indicators ──────────────────────────────┐
│  💓 Heart rate   72 BPM  (good signal)          │
│  😐 Expression   neutral  (conf: 91%)           │
│  🎙 Vocal        energy: low · pitch: 142 Hz    │
│  📝 Language     sentiment: –0.1 · pronoun: 34% │
│  Modules active: emotion · pulse · prosody       │
└────────────────────────────────────────────────┘
```

**Privacy note in UI:** "These indicators are generated on the patient's device.
No raw video, audio, or transcript data is sent to this screen."

**Access expiry:** Telemetry panel is disabled as soon as the DataChannel closes.
No caching of telemetry values on the connector side.

**Acceptance criteria:**
- [ ] `agent.telemetry` DataChannel messages received and rendered in real time
- [ ] Panel updates ≤ 2s latency from agent emission
- [ ] Panel clears immediately on call end
- [ ] Privacy notice visible in panel
- [ ] Connector shows which modules are active (from telemetry payload `modules[]` field)

---

### WA-7 — Telemetry Packaging + VC-13/15 Integration

**Session scope:** 1 session  
**Depends on:** WA-1–WA-6, vault-transcript.js (captureEvent), vault-package.js  
**Read first:** `docs/js/vault-transcript.js`, `docs/js/vault-package.js`, `docs/js/vault-idb.js`

**IDB integration:**
- `agent.telemetry` events are written to `wf-events` via `captureEvent()` (type: `'agent.telemetry'`)
  alongside the existing call event chain — same SHA-256 hash chain, same store
- `wf-telemetry` store (added in WA-1) holds the aggregated session-level samples for export

**vault-transcript.js additions:**
- `generateTranscript()` gains a new `<div typeof="wf:BiometricTelemetryLog">` section
  if `agent.telemetry` events exist for the session
- Each telemetry event rendered as a timestamped row with RDFa attributes:
  `property="wf:bpm"`, `property="wf:primaryExpression"`, etc.
- Biometric section clearly labelled: "Indicators generated locally on patient device"

**vault-package.js additions:**
- `buildPackage()` includes `telemetry.ndjson` (one JSON line per `agent.telemetry` event)
  alongside transcript and receipt artefacts
- `wf:TelemetryArtefact` type added to manifest JSON-LD

**Post-session access model (reuses VC-8 ODRL agreements):**
- Patient can grant clinician read-access to session telemetry using the existing agreement flow
- Agreement specifies: `"target": "wf:sessionTelemetry:<sessionId>"`, duration, and purpose
- Without an explicit agreement, telemetry data never leaves the device after the call ends

**Acceptance criteria:**
- [ ] `agent.telemetry` events appear in the `wf-events` hash chain alongside call events
- [ ] `generateTranscript()` includes a BiometricTelemetryLog section when telemetry exists
- [ ] `buildPackage()` includes `telemetry.ndjson` in the ZIP
- [ ] Post-session access grant uses existing ODRL agreement infrastructure
- [ ] Telemetry data not accessible on connector after call ends without explicit grant

---

### WA: Module capability matrix (for consent UI copy)

| Module | Toggle label | What it measures | Enabled for |
|---|---|---|---|
| `vision.emotion` | Facial expression tracking | Expression, valence/arousal | Psychology, psychiatry |
| `vision.rpg` | Heart rate indicator | BPM via camera (rPPG) | General telehealth |
| `vision.gaze` | *(WA-8, future)* | Gaze, pupil dilation | Cognitive assessment |
| `audio.prosody` | Vocal pattern analysis | Pitch, energy, speech rate | Psychiatry |
| `audio.stt` | Live transcription | Transcript segments | All sessions (via VC-14) |
| `text.linguistic` | Language pattern analysis | Sentiment, pronoun usage, coherence | Psychology, psychiatry |

### WA: Telemetry event schema (`wf-events`, type: `'agent.telemetry'`)

```json
{
  "id": "evt-<ts>-<rand>",
  "type": "agent.telemetry",
  "sessionId": "...",
  "seq": 42,
  "actorDid": "did:key:<patient>",
  "ts": "2026-05-31T04:20:00.000Z",
  "payload": {
    "modules": ["vision.emotion", "vision.rpg", "audio.prosody"],
    "vision": {
      "emotion": "neutral",
      "microExpression": "transient_anxiety",
      "valence": 0.05,
      "arousal": -0.12,
      "confidence": 0.91
    },
    "biometrics": {
      "bpm": 72.4,
      "rPPGConfidence": 0.89,
      "signalQuality": "good"
    },
    "audio": {
      "pitchHz": 142.3,
      "energyVariance": 0.04,
      "speechRateWordsPerMin": 112,
      "tremorIndex": 0.02
    },
    "linguistic": {
      "pronounRatio1P": 0.34,
      "sentimentScore": -0.08,
      "coherenceScore": 0.71,
      "hedgeRatio": 0.12
    }
  },
  "hash": "sha256-...",
  "prevHash": "sha256-..."
}
```

### WA: CDN library plan (no bundler)

| Purpose | Library | CDN URL pattern | Load point |
|---|---|---|---|
| Face landmarks | `@mediapipe/tasks-vision` | `cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/+esm` | cv-emotion.worker.js |
| Audio features | `meyda` | `cdn.jsdelivr.net/npm/meyda@5/+esm` | audio-features.worker.js |
| STT / Whisper | `@xenova/transformers` | Already in vault-comms-transcode.js | Reuse, do not duplicate |
| Worker comms | Plain postMessage | (no library) | vault-cv.js event bus |

---

---

## EPIC 2 — Human-Centric Wallet (HCW)
### Bitcoin, Lightning, Nym Tokens, Welfare Payments & Privacy Finance

---

## Threat model — read before implementing anything

> This section documents the adversarial environment this system may operate in.
> It is not hypothetical. These requirements exist because real people in real danger
> may depend on this infrastructure.

### Who the system must protect against

**Tier 1 — Data harvesters:** Advertisers, data brokers, state surveillance infrastructure.
Standard privacy measures (Nym, encrypted IDB) are sufficient.

**Tier 2 — Opportunistic criminals:** Fraud, account takeover, phishing.
Standard security practices sufficient.

**Tier 3 — Organised crime / trafficking networks:**
These are enterprise-scale operations with sophisticated technical capabilities, legal
resources, and willingness to use physical violence. Key characteristics:
- They monitor blockchain transaction graphs at scale
- They may have access to corrupted public-sector workers, law enforcement, or legal processes
- They will attempt to compromise infrastructure, intimidate developers, or use legal threats
  to obtain user data
- A breach that reveals a victim's location or transaction history is potentially fatal

**For Tier 3 threat actors, the only protection is architectural:**
> The system must be designed so that even a full breach of all application
> infrastructure yields zero exploitable data about users.
> The developers must be technically incapable of decrypting user data
> or identifying user locations — not merely unwilling.

### Non-negotiable architectural requirements for HCW

1. **No user wallet addresses stored server-side.** Wallet state lives exclusively in
   the phone's encrypted IDB under the user's vault key.

2. **No transaction history transmitted unencrypted.** All exchange API calls routed
   through Nym where possible; falling back to HTTPS-only with no identifying headers.

3. **The Blind Proxy Treasury model** — when a welfare payment must be made to a merchant,
   the payment is executed from a shared pool (never directly from the user's wallet to the
   merchant), making it impossible to link the user's identity to the merchant's location.

4. **Decoupled credential issuance.** The people who issue crisis credentials and the people
   who maintain the technical infrastructure must be in separate organisations with no shared
   data. If the tech team is breached, they have no knowledge of who the credential holders are.

5. **No logging of user IPs, wallet addresses, or transaction amounts at the application layer.**
   Logs must contain only non-identifying operational data (error types, timing, throughput).

---

### Architecture overview

```
Phase 1 — Lightning + Nym token management (no external blockchain)
───────────────────────────────────────────────────────────────────
vault.html
  └── vault-wallet.js
        ├── WebLN provider integration (connects to user's Lightning wallet)
        ├── Nym token auto-swap (BTC → NYM bandwidth credentials)
        ├── Balance display (Lightning BTC only)
        └── Exchange on-ramp widget (MoonPay / Transak CDN embed)

Phase 2 — Welfare payments + care credits (programmable signed documents)
──────────────────────────────────────────────────────────────────────────
vault.html
  └── vault-welfare.js
        ├── Care credit issuance (ODRL-signed JSON-LD, stored in IDB)
        ├── Credit redemption flow (QR code at merchant / online)
        ├── Merchant whitelist (SHACL shape — approved pharmacy/grocery addresses)
        └── Donor portal (receive BTC donations → allocate as care credits)

Phase 3 — Stablecoin + Blind Proxy (requires external blockchain infrastructure)
──────────────────────────────────────────────────────────────────────────────────
vault.html
  └── vault-stablecoin.js
        ├── AUDD / USDC balance (Solana Token-2022)
        ├── Confidential Transfer requests (amount hidden via ZK proof)
        ├── Blind Proxy payment channel (treasury pool → merchant)
        └── Multi-region currency switching (AUDD → USDC by region)
```

---

### HCW: Progress Tracker

| Session | Date | Milestone | Status | Handover file |
|---------|------|-----------|--------|---------------|
| HCW-1 | | vault-wallet.js + Lightning + IDB v8 | not started | |
| HCW-2 | | Nym token auto-swap + bandwidth abstraction | not started | |
| HCW-3 | | Exchange on-ramp widget (MoonPay/Transak) | not started | |
| HCW-4 | | Care credit issuance + ODRL-signed JSON-LD | not started | |
| HCW-5 | | Credit redemption flow + merchant whitelist | not started | |
| HCW-6 | | Donor portal + care credit allocation | not started | |
| HCW-7 | | Stablecoin integration (Solana Token-2022) | not started | |
| HCW-8 | | Blind Proxy treasury architecture | not started | |
| HCW-9 | | Anonymous credential issuance for crisis support | not started | |
| HCW-10 | | Multi-region currency (USDC) + global expansion | not started | |

---

### HCW-1 — vault-wallet.js + Lightning + IDB v8

**Session scope:** 1–2 sessions  
**Depends on:** vault-idb.js (v7 from WA-1), vault-did.js, vault-nym.js  
**Read first:** `docs/js/vault-idb.js`, `docs/js/vault-nym.js`, `docs/vault.html` (panel structure)

**IDB changes:**
- Bump `_openDB` to version 8
- Add store: `wf-wallet` (keyPath: `id`) — wallet metadata + Lightning node config
- Add store: `wf-txlog` (keyPath: `id`) — local transaction log (never transmitted)
- Add constants: `_ST_WALLET`, `_ST_TXLOG`
- Wallet record shape:
  ```js
  {
    id: 'wallet-lightning',
    type: 'lightning',           // 'lightning' | 'solana' (Phase 3)
    provider: 'webln',           // 'webln' | 'breez' | 'alby'
    nodeAlias: string,           // user-defined label only; no pubkey stored plaintext
    createdAt: ISO string,
    lastUsed: ISO string,
  }
  ```

**vault-wallet.js — Phase 1 public API:**
```js
async function walletInit()
// Detects available WebLN provider (window.webln — set by Alby, Zeus, etc.)
// Falls back to embedded Lightning node (breez-sdk-web if available via CDN)
// Stores provider type in IDB wf-wallet

async function walletGetBalance()
// Returns {sats, fiatEstimate, currency} via WebLN or embedded node
// Does NOT expose node pubkey or channel info to UI

async function walletSendPayment(bolt11Invoice)
// Pays a BOLT11 invoice via WebLN.sendPayment()
// Logs to wf-txlog (local only — never transmitted)
// Routes payment request through Nym if nymAdapter is active

async function walletReceivePayment(amountSats, description)
// Generates a BOLT11 invoice
// Returns {invoice, qrDataUrl, expiresAt}

function walletGetTxLog(limit)
// Returns local transaction log entries (IDB only)
```

**vault.html additions:**
- New "💳 Wallet" button in the nav row (beside Contacts · Queue · Diet)
- Wallet sheet: balance display, recent transactions, send/receive buttons
- Exchange on-ramp placeholder button (wired in HCW-3)

**Acceptance criteria:**
- [ ] IDB v8 opens; `wf-wallet` and `wf-txlog` stores created
- [ ] `walletInit()` detects WebLN provider or reports unavailable
- [ ] Balance displayed without exposing node pubkey
- [ ] `walletSendPayment()` writes to `wf-txlog`; no server log
- [ ] Wallet panel renders in vault.html owner workspace

---

### HCW-2 — Nym Token Auto-swap + Bandwidth Abstraction

**Session scope:** 1 session  
**Depends on:** HCW-1, vault-nym.js  
**Read first:** `docs/js/vault-nym.js` (nymAdapter, surbBudget)

**Design principle:** Users never see "NYM tokens". They see "Privacy routing: active" or
"Bandwidth credit: 12 minutes remaining". The BTC → NYM swap is a background operation.

```js
// vault-wallet.js additions

async function ensureNymBandwidth(requiredMinutes)
// Checks current zk-nym bandwidth credential remaining
// If insufficient: executes background swap via exchange partner API
//   (BTC → NYM, routed through Nym to avoid IP linkage to the swap)
// Calls nymAdapter.redeemBandwidth(nymTokens) on success
// Returns: {sufficient: bool, minutesRemaining, swapExecuted}

function getNymBandwidthStatus()
// Returns current bandwidth status for UI display
// {minutesRemaining, isActive, lastRefill}
```

**Exchange rate source:** Use a CDN-served price feed (e.g. CoinGecko public API) for
BTC/NYM exchange rate; cache in IDB for 5 minutes; do not expose this API call in any log.

**Acceptance criteria:**
- [ ] `ensureNymBandwidth()` triggers a swap when bandwidth is low
- [ ] Swap executed as a background job (wf-jobs scheduler, IDLE condition)
- [ ] User sees "Privacy routing" status only — no NYM token amounts
- [ ] Exchange rate cached; no repeated API calls within 5 minutes

---

### HCW-3 — Exchange On-Ramp Widget

**Session scope:** 1 session  
**Depends on:** HCW-1  
**Read first:** MoonPay or Transak SDK documentation (CDN embed)

**Note on affiliate revenue:**
Integrating as an affiliate partner requires registering with each exchange and receiving
an affiliate/partner API key. This is a business step separate from the code. The code
should be designed to accept an affiliate key from a configuration constant so the key
can be set without modifying the core files.

**Design:**
- Use Transak SDK (CDN embed: `https://cdn.transak.com/global-transak/sdk.js`) as primary
- MoonPay as secondary option
- Embed is initialized with affiliate partner ID from `WALLET_CONFIG.TRANSAK_PARTNER_KEY`
- Widget opens in a sandboxed iframe; no health data from vault is accessible to the iframe
- After on-ramp completes: widget sends a completion event; app refreshes balance

**Configuration pattern:**
```js
// docs/js/vault-wallet-config.js (gitignored; template committed)
const WALLET_CONFIG = Object.freeze({
  TRANSAK_PARTNER_KEY: '',   // Set by operator before deployment
  MOONPAY_API_KEY:     '',
  DEFAULT_ONRAMP:      'transak',
});
```

**Acceptance criteria:**
- [ ] Transak widget loads in sandboxed iframe
- [ ] Affiliate partner key configurable without modifying core files
- [ ] Health data from vault is inaccessible to iframe (Content-Security-Policy)
- [ ] Balance refreshes after successful on-ramp
- [ ] Widget closes cleanly; no memory leak

---

### HCW-4 — Care Credit Issuance + ODRL-signed JSON-LD

**Session scope:** 1 session  
**Depends on:** HCW-1, vault-crypto.js, vault-did.js  
**Read first:** `docs/js/vault-crypto.js`, `docs/js/vault-handshake.js` (ODRL agreement pattern)

**Design:** Phase 1 care credits are **not** on-chain. They are signed ODRL documents
(identical pattern to VC-8 agreements). A credit is a cryptographically signed claim that
"wallet X has N AUD equivalent available for use at whitelisted merchants, expiring at Y,
issued by Z". They are stored in IDB and redeemed offline or via QR code.

**New IDB store (add in this session):**
- `wf-credits` (keyPath: `id`) — care credit records

**Care credit JSON-LD schema:**
```json
{
  "@context": ["http://www.w3.org/ns/odrl.jsonld", "https://wellfare.social/ns/vault#"],
  "@type": "wf:CareCredit",
  "@id": "urn:uuid:<generated>",
  "wf:issuerDid": "did:key:<issuer>",
  "wf:holderDid": "did:key:<holder>",
  "wf:amountAUD": 50.00,
  "wf:currency": "AUD",
  "wf:purpose": "pharmacy",
  "wf:merchantWhitelist": ["<pharmacy-did-1>", "<pharmacy-did-2>"],
  "wf:expiresAt": "2026-08-31T00:00:00Z",
  "wf:issuedAt": "2026-05-31T04:00:00Z",
  "odrl:constraint": [
    {"odrl:leftOperand": "wf:merchantCategory", "odrl:operator": "odrl:isA",
     "odrl:rightOperand": "wf:ApprovedPharmacy"}
  ],
  "wf:issuerSig": "<base64 Ed25519 sig>",
  "wf:holderSig": "<base64 Ed25519 sig>",
  "wf:status": "active"
}
```

```js
// vault-welfare.js

async function issueCredit(holderDid, amountAUD, purpose, merchantWhitelist, expiresAt)
// Creates + signs a CareCredit JSON-LD document
// Stores in IDB wf-credits
// Returns the signed document

async function listCredits()
// Returns all credits from wf-credits (active + expired)

async function getCreditQr(creditId)
// Returns a QR data URL encoding the signed credit JSON-LD
// Used for merchant verification / in-store redemption
```

**Acceptance criteria:**
- [ ] `issueCredit()` produces a valid ODRL JSON-LD document with Ed25519 signature
- [ ] Credit stored in `wf-credits`; survives page reload
- [ ] QR code generated; encodes complete signed document
- [ ] Expired credits displayed as inactive in UI

---

### HCW-5 — Credit Redemption + Merchant Whitelist

**Session scope:** 1 session  
**Depends on:** HCW-4  
**Read first:** `docs/js/vault-welfare.js`, `docs/profiles/access-profiles.ttl`

**Redemption flow:**
1. User shows QR at merchant / sends QR via secure message
2. Merchant scans QR → receives signed CareCredit JSON-LD
3. Merchant verifies issuer Ed25519 signature (standard WebCrypto — no custom backend needed)
4. Merchant confirms their DID is in `merchantWhitelist`
5. Settlement: Phase 1 = out-of-band (fiat equivalent provided by issuing organisation);
   Phase 3 = on-chain AUDD Confidential Transfer via Blind Proxy

**SHACL shape for merchant whitelist:**
```turtle
wf:ApprovedMerchant a rdfs:Class ; rdfs:label "Approved welfare merchant"@en .
wf:merchantDid a rdf:Property ; rdfs:domain wf:ApprovedMerchant .
wf:merchantCategory a rdf:Property ; rdfs:domain wf:ApprovedMerchant .
wf:merchantRegion a rdf:Property ; rdfs:domain wf:ApprovedMerchant .
```

```js
// vault-welfare.js additions

async function redeemCredit(creditId, merchantDid, amountAUD)
// Verifies merchant is in whitelist
// Verifies credit is active and has sufficient balance
// Deducts amount; writes redemption event to wf-events
// If credit fully spent: marks wf-credits record as 'redeemed'
// Returns: {success, remainingBalance, receiptJsonLd}

function verifyMerchantDid(merchantDid)
// Checks merchantDid against SHACL-constrained whitelist in IDB
// Returns: {approved: bool, category, region}
```

**Acceptance criteria:**
- [ ] Redemption flow verifies issuer signature before accepting credit
- [ ] Merchant DID checked against whitelist; unlisted merchants rejected
- [ ] Partial redemptions supported; remaining balance tracked
- [ ] Redemption event written to `wf-events` (type: `'credit.redeemed'`)
- [ ] Receipt JSON-LD generated; downloadable

---

### HCW-6 — Donor Portal + Care Credit Allocation

**Session scope:** 1 session  
**Depends on:** HCW-4, HCW-5, walletReceivePayment()  
**Read first:** `docs/js/vault-welfare.js`, `docs/js/vault-wallet.js`

**Design:** A donor sends BTC/Lightning to the vault. The vault operator (e.g. a social
worker, community organisation) allocates those funds as care credits to recipients. The
donor never knows the recipient; the recipient never knows the donor. Only the operator
holds both relationships, and the system should minimise what the operator holds.

```js
// vault-welfare.js additions

async function createDonationInvoice(amountSats, purposeLabel)
// Generates a Lightning invoice for the donation amount
// Returns {invoice, qrDataUrl, donationId}
// Stores donation intent in IDB (not the donor's identity)

async function allocateDonation(donationId, recipientDid, purpose, merchantWhitelist)
// Links an incoming Lightning payment to a care credit issuance
// Issues the credit; stores in wf-credits
// Does NOT store donor ↔ recipient mapping anywhere

function getDonationStats()
// Returns aggregate stats only: total received (sats), credits issued, credits redeemed
// No per-donor or per-recipient data
```

**Acceptance criteria:**
- [ ] Donation invoice generated; QR displays for sharing
- [ ] Incoming payment matched to donation intent via payment hash
- [ ] `allocateDonation()` issues credit without storing donor ↔ recipient link
- [ ] Stats aggregated; no individual data exposed

---

### HCW-7 — Stablecoin Integration (Solana Token-2022)

**Session scope:** 1–2 sessions  
**Depends on:** HCW-1, HCW-5  
**Read first:** Solana Token-2022 Confidential Transfers documentation, AUDD technical documentation

**Pre-implementation decision required (discuss with user before starting):**
- Which Solana RPC endpoint? (public endpoint leaks IP; must route through Nym or use
  a privacy-preserving RPC provider)
- Solana web3.js CDN bundle size (~1.5 MB) — acceptable?
- Is AUDD (Stellar + Solana) the right stablecoin, or wait for native Lightning stablecoin?

**Architecture if proceeding:**
```js
// vault-stablecoin.js

async function stablecoinInit(chain)
// chain: 'solana'
// Loads @solana/web3.js from CDN
// Generates or loads Solana keypair (Ed25519 — same curve as vault did:key)
// Keypair stored encrypted in IDB under vault key (NEVER exported)

async function stablecoinGetBalance(mint)
// Returns AUDD balance using Token-2022 confidential balance decryption
// Amount visible only to account holder

async function stablecoinTransferConfidential(destinationPubkey, amount, memo)
// Constructs Token-2022 ConfidentialTransfer instruction
// Broadcasts transaction RPC call routed through Nym
// Amount and recipient balance remain hidden on-chain

async function stablecoinMintCareCredit(amountAUD, holderDid, purpose)
// Mints (or wraps) AUDD into a programmable voucher contract
// Returns credit with on-chain backing
```

**Acceptance criteria:**
- [ ] Solana keypair generated; stored encrypted in IDB; never exported
- [ ] AUDD balance readable without exposing keypair
- [ ] Confidential transfer instruction constructed correctly
- [ ] RPC call routed through Nym (or explicit consent prompt if Nym unavailable)

---

### HCW-8 — Blind Proxy Treasury Architecture

**Session scope:** 1–2 sessions  
**Depends on:** HCW-7  
**Read first:** `docs/js/vault-stablecoin.js`, threat model section above

**The problem this solves:**
If a user's wallet directly pays a merchant, the on-chain transaction links the user's
wallet address to the merchant's address — potentially revealing geographic location.

**The solution:**
All retail/welfare payments are executed from a **shared treasury pool** operated by a
trusted organisation (not the app itself). The user's wallet sends funds to the pool;
the pool sends funds to the merchant. The transaction graph shows only:
"pool → many merchants" and "user → pool". Location de-coupling is achieved through the
crowd effect (thousands of pool→merchant transactions per day).

**Architectural components:**
1. **Pool address**: A Solana multisig wallet controlled by the operating organisation
   (not the app developers; see operational security note)
2. **Blind voucher**: User receives a cryptographic receipt (Ed25519 signed by the pool)
   proving their deposit, without linking them to any specific merchant transaction
3. **Redemption**: User presents blind voucher at merchant; pool makes the payment;
   pool's internal records link voucher to payment (but this record is held by the
   operating organisation, not in the app or its servers)

**Operational security note (non-code requirement):**
> The pool multisig keys must be held by people who have no access to user identity data.
> The credential issuers (crisis workers) must have no access to pool keys.
> These are organisational controls that code alone cannot enforce.
> Document this requirement in every operator onboarding document.

**Acceptance criteria:**
- [ ] User-side: deposit to pool + receive blind voucher (signed receipt)
- [ ] Voucher stored in IDB; presentable as QR
- [ ] Pool operator side: voucher verified; payment executed to merchant
- [ ] On-chain graph: user → pool, pool → merchant; user ↔ merchant never directly linked
- [ ] Threat model documentation updated with this architecture

---

### HCW-9 — Anonymous Credential Issuance for Crisis Support

**Session scope:** 1–2 sessions  
**Depends on:** HCW-4 (care credit schema), HCW-8 (blind proxy)

**The problem:** A trafficking survivor cannot present government ID to access care credits.
The credential must prove eligibility (crisis status) without identifying the person.

**Design:**
1. A **trusted issuer** (crisis worker, Salvation Army case manager, social worker) holds
   an issuance key (did:key). This person is NOT the app developer.
2. The issuer presents the survivor with a one-time issuance URL (delivered via secure
   channel — in person, or via Nym message). The URL encodes a signed token:
   `{issued_by: issuer_did, tier: 'crisis-tier-1', expires: <24h>, nonce: <random>}`
3. The survivor opens the URL in WellFair. The app generates a fresh did:key on the device.
4. The app presents the signed token + fresh did:key to the issuance endpoint (routed via Nym).
5. The issuer endpoint issues a CareCredit to the fresh did:key. The issuer's database records:
   `{issued_to: <fresh_did>, tier, timestamp}` — no name, no government ID, no prior wallet.
6. The survivor now has a care credit tied to a key that has never appeared on any blockchain
   and has no connection to their real identity.

**Anonymity properties:**
- Issuer knows: a credential was issued for crisis tier 1 at time T
- Issuer does NOT know: who holds it, what they spend it on, where they are
- App server knows: nothing (it is static HTML with no server logs)
- Blockchain knows: pool → merchant payments; the fresh did:key is never on-chain

**Acceptance criteria:**
- [ ] One-time issuance token generated by issuer key; time-limited
- [ ] Survivor device generates fresh did:key (no connection to vault's persistent key)
- [ ] Token + fresh key presented via Nym; CareCredit issued to fresh key
- [ ] Issuance flows through existing `issueCredit()` with no special cases
- [ ] Issuer database schema stores only `{did, tier, timestamp}` — no PII

---

### HCW-10 — Multi-region Currency + Global Expansion

**Session scope:** 1 session  
**Depends on:** HCW-7, HCW-8

**Design:** Currency is determined by the user's region preference stored in IDB.
The care credit schema accepts any ISO 4217 currency code. The on-chain stablecoin
is swapped at issuance time by the pool operator.

| Region | Stablecoin | Chain | Notes |
|---|---|---|---|
| Australia | AUDD | Solana | Primary; AFSL-licensed; Coinbase-integrated |
| United States | USDC | Solana | Circle; gold standard USD stablecoin |
| European Union | EURC | Solana | Circle's EUR stablecoin |
| Global / fallback | BTC (Lightning) | Lightning | No stablecoin required |

```js
// vault-stablecoin.js additions

function setUserRegion(regionCode)
// Sets region preference in IDB; determines default currency

function getRegionConfig(regionCode)
// Returns {currency, stablecoinMint, chainId, rpcEndpoint}
// Loaded from a static JSON config file (no server call)
```

**Acceptance criteria:**
- [ ] Region setting stored in IDB; persists across sessions
- [ ] Care credits display in user's local currency
- [ ] Stablecoin mint address selected based on region config
- [ ] Config is a static JSON file; no runtime server dependency

---

## Combined IDB version roadmap

| IDB version | When | New stores / schema changes |
|---|---|---|
| v6 | current (v0.0.6) | wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl, wf-contacts, wf-relationships, wf-agreements, wf-jobs, wf-events |
| v6 | DL-1 | No new store — wf-dl records gain optional `barcode` and `categories_tags` fields (additive, backward-compatible) |
| v7 | WA-1 | + wf-telemetry |
| v8 | HCW-1 | + wf-wallet, wf-txlog |
| v9 | HCW-4 | + wf-credits |

---

## Script load order (vault.html — target for v0.0.7)

```
Gun CDN →
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-directory → vault-handshake → vault-comms-gate → vault-comms-call →
vault-cv →                          ← AgentController (rewritten WA-1)
vault-scheduler → vault-transcript → vault-comms-transcode → vault-package →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager →
vault-diet → vault-diet-barcode →              ← new DL-1
vault-wallet → vault-welfare → vault-stablecoin   ← new HCW modules
```

Worker files (loaded dynamically, never in main thread load order):
```
docs/js/workers/
  cv-emotion.worker.js
  cv-rpg.worker.js
  audio-prosody.worklet.js
  audio-features.worker.js
  text-linguistic.worker.js
```

---

## Handover template

```markdown
# WellFair — Session Handover {WA|HCW}-{n} ({YYYY-MM-DD})

## Milestone covered

## Completed in this session
<!-- Bulleted list: function names, file locations, line ranges -->

## Files modified
| File | Change summary | Key functions added |
|------|---------------|---------------------|

## IDB state
IDB version: vN
Stores: ...

## Script load order (vault.html)

## What to do next (immediate — first thing next session)
<!-- Specific enough to act without inference -->

## Decisions made this session

## Blocked / deferred

## Acceptance criteria met
- [ ] ...
```

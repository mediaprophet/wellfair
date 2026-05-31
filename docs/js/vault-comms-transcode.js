'use strict';

// ── Language Transcoding — 3-tier progressive STT + translation (VC-14) ────────
// Tier 1: WebSpeech API — live realtime transcription (always available in Chrome)
// Tier 2: transformers.js — local-LLM translation (if library present)
// Tier 3: external API — user-configured endpoint, explicit per-session consent required
//
// Depends on: vault-transcript.js (captureEvent), vault-scheduler.js (registerJobHandler, enqueueJob, JOB_TRIGGER)
//
// Public API:
//   detectAvailableTier()           → 'webspeech' | 'local-llm' | 'external-api' | null
//   startRealtimeTranscription(stream, sessionId, langHint)
//   stopRealtimeTranscription()
//   transcodeSegment(segment, targetLang)   → job handler (transcript.transcode)
//   configureExternalApi(endpoint)          → set external API endpoint (owner settings)
//   getWhisperModelId()                     → resolved model id from owner preferences

// ── Module state ──────────────────────────────────────────────────────────────

let _txcRecognition  = null; // SpeechRecognition instance
let _txcSessionId    = null;
let _txcSelfDid      = null;
let _txcLangHint     = 'en';
let _txcExternalApi  = null;      // user-configured external endpoint
let _txcExternalConsent = false;  // must be re-granted each session

// Returns the Whisper model id chosen by the vault owner.
// Falls back to whisper-base if vault-model-prefs.js is not loaded.
function getWhisperModelId() {
  return (typeof getModelPref === 'function')
    ? (getModelPref('whisperModel') || 'Xenova/whisper-base')
    : 'Xenova/whisper-base';
}

// ── Tier detection ─────────────────────────────────────────────────────────────

// Returns the highest available tier name, or null if nothing is available.
function detectAvailableTier() {
  if (typeof SpeechRecognition !== 'undefined' ||
      typeof webkitSpeechRecognition !== 'undefined') {
    return 'webspeech';
  }
  if (typeof pipeline !== 'undefined') { // transformers.js exposes pipeline()
    return 'local-llm';
  }
  if (_txcExternalApi) {
    return 'external-api';
  }
  return null;
}

// ── Tier 1 — WebSpeech live transcription ────────────────────────────────────

// Start live speech recognition on a MediaStream.
// Emits captureEvent('speech.segment', ...) for each recognised segment.
function startRealtimeTranscription(stream, sessionId, langHint) {
  stopRealtimeTranscription();

  const SR = typeof SpeechRecognition !== 'undefined'
    ? SpeechRecognition : typeof webkitSpeechRecognition !== 'undefined'
    ? webkitSpeechRecognition : null;

  if (!SR) {
    console.warn('[Transcode] WebSpeech API not available in this browser');
    return;
  }

  _txcSessionId = sessionId;
  _txcSelfDid   = typeof vaultDidKey !== 'undefined' && vaultDidKey ? vaultDidKey.did : null;
  _txcLangHint  = langHint || 'en';

  const sr = new SR();
  sr.lang        = _txcLangHint;
  sr.continuous  = true;
  sr.interimResults = false;

  // SpeechRecognition requires audio from the system microphone, not a
  // MediaStream. We start it in parallel to the call audio; stream is
  // accepted for API symmetry and future MediaStreamTrackProcessor use.
  sr.onresult = async (ev) => {
    for (let i = ev.resultIndex; i < ev.results.length; i++) {
      if (!ev.results[i].isFinal) continue;
      const text = ev.results[i][0].transcript.trim();
      if (!text) continue;

      // Capture the raw speech segment in the event log
      if (typeof captureEvent === 'function' && _txcSessionId) {
        await captureEvent(_txcSessionId, 'speech.segment', _txcSelfDid, {
          original: text,
          lang: _txcLangHint,
          serviceUsed: 'webspeech',
        }).catch(() => {});
      }

      // WA-5 — forward raw segment to the linguistic analysis worker (no STT duplication)
      if (typeof agentSendText === 'function') {
        agentSendText(text, new Date().toISOString());
      }

      // If the user's vault language differs, enqueue a translation job
      const vaultLang = _txcVaultLang();
      if (vaultLang && vaultLang !== _txcLangHint && typeof enqueueJob === 'function') {
        enqueueJob(
          'transcript.transcode',
          { sessionId: _txcSessionId, original: text, lang: _txcLangHint, targetLang: vaultLang },
          JOB_TRIGGER.ALWAYS,
          4
        ).catch(() => {});
      }
    }
  };

  sr.onerror = (e) => {
    if (e.error !== 'aborted' && e.error !== 'no-speech') {
      console.warn('[Transcode] SpeechRecognition error:', e.error);
    }
  };

  sr.onend = () => {
    // Auto-restart if we're still in a live session
    if (_txcRecognition === sr && _txcSessionId) {
      try { sr.start(); } catch (_) {}
    }
  };

  try {
    sr.start();
    _txcRecognition = sr;
  } catch (e) {
    console.warn('[Transcode] Could not start SpeechRecognition:', e.message);
  }
}

function stopRealtimeTranscription() {
  if (_txcRecognition) {
    try { _txcRecognition.abort(); } catch (_) {}
    _txcRecognition = null;
  }
  _txcSessionId = null;
}

// ── Tier 2 + 3 — Batch translation job handler ────────────────────────────────

// Translates a speech segment.
// Tier 2: transformers.js pipeline() if available
// Tier 3: external API — requires _txcExternalConsent === true for this session
async function transcodeSegment(segment, targetLang, onProgress) {
  const { original, lang } = segment;

  // Tier 2 — local transformers.js
  // Model size is configurable via vault-model-prefs.js (owner preference).
  // Translation uses the opus-mt family; the Whisper model pref governs future ASR batching.
  if (typeof pipeline === 'function') {
    try {
      onProgress && onProgress(30);
      const translator = await pipeline('translation', 'Xenova/opus-mt-' + lang + '-' + targetLang);
      onProgress && onProgress(70);
      const out = await translator(original);
      onProgress && onProgress(100);
      return {
        translated: out[0]?.translation_text || '',
        targetLang,
        serviceUsed: 'local-llm',
      };
    } catch (e) {
      console.warn('[Transcode] Tier-2 translation failed:', e.message);
    }
  }

  // Tier 3 — external API (requires explicit per-session consent)
  if (_txcExternalApi && _txcExternalConsent) {
    onProgress && onProgress(20);
    const resp = await fetch(_txcExternalApi, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: original, source: lang, target: targetLang }),
    });
    if (!resp.ok) throw new Error('[Transcode] External API error: ' + resp.status);
    onProgress && onProgress(90);
    const data = await resp.json();
    onProgress && onProgress(100);
    return {
      translated: data.translated || data.text || '',
      targetLang,
      serviceUsed: 'external',
    };
  }

  if (_txcExternalApi && !_txcExternalConsent) {
    throw new Error('External translation API requires explicit per-session consent. Grant via Settings → Translation.');
  }

  // No tier available
  return { translated: null, targetLang, serviceUsed: null };
}

// ── External API configuration (owner settings) ───────────────────────────────

function configureExternalApi(endpoint) {
  _txcExternalApi = endpoint || null;
  _txcExternalConsent = false; // consent always resets when endpoint changes
}

// Grant per-session consent for external API use. Shown to user before first use.
function grantExternalApiConsent() {
  if (!_txcExternalApi) return false;
  _txcExternalConsent = true;
  return true;
}

function revokeExternalApiConsent() {
  _txcExternalConsent = false;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

// Returns the vault owner's preferred language (from vault settings or browser).
function _txcVaultLang() {
  return (navigator.language || 'en').split('-')[0];
}

// ── Register job handler with the scheduler ───────────────────────────────────

if (typeof registerJobHandler === 'function') {
  registerJobHandler('transcript.transcode', {
    estimateFn: () => 2000,
    runFn: async (job, onProgress) => {
      const seg = JSON.parse(job.payload);
      const targetLang = seg.targetLang || _txcVaultLang();
      const result = await transcodeSegment(seg, targetLang, onProgress);

      // Update the original speech.segment event in wf-events with translation
      if (result.translated && typeof captureEvent === 'function' && seg.sessionId) {
        await captureEvent(seg.sessionId, 'speech.segment', null, {
          original: seg.original,
          lang: seg.lang,
          translated: result.translated,
          targetLang: result.targetLang,
          serviceUsed: result.serviceUsed,
        }).catch(() => {});
      }

      return result;
    },
  });
}

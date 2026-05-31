'use strict';

// ── Model Preferences — vault owner AI model selection ────────────────────────
// Lets the vault owner choose which local AI models to use for:
//   • Speech-to-text / transcription (Whisper model size)
//   • Call analysis defaults (which Webizen Agent modules start enabled)
//
// Preferences are non-sensitive configuration — stored in localStorage.
// Key: 'wf-model-prefs'
//
// Public API:
//   getModelPref(key)              → current value (with default fallback)
//   setModelPref(key, value)       → persist a preference
//   renderModelPrefPanel(elId)     → render the settings UI into a container element

const _MODEL_PREF_KEY = 'wf-model-prefs';

const _MODEL_DEFAULTS = {
  whisperModel:        'Xenova/whisper-base',
  cvDefaultEmotion:    false,
  cvDefaultRpg:        false,
  cvDefaultProsody:    false,
  cvDefaultLinguistic: false,
};

function _loadPrefs() {
  try {
    const raw = localStorage.getItem(_MODEL_PREF_KEY);
    return raw ? { ..._MODEL_DEFAULTS, ...JSON.parse(raw) } : { ..._MODEL_DEFAULTS };
  } catch (_) {
    return { ..._MODEL_DEFAULTS };
  }
}

function _savePrefs(prefs) {
  try { localStorage.setItem(_MODEL_PREF_KEY, JSON.stringify(prefs)); } catch (_) {}
}

function getModelPref(key) {
  return _loadPrefs()[key] ?? _MODEL_DEFAULTS[key];
}

function setModelPref(key, value) {
  const prefs = _loadPrefs();
  prefs[key]  = value;
  _savePrefs(prefs);
}

// Render the model preferences UI into an existing container element.
function renderModelPrefPanel(elId) {
  const el = document.getElementById(elId);
  if (!el) return;

  const prefs = _loadPrefs();

  const whisperOpts = [
    {
      id:    'Xenova/whisper-tiny',
      label: 'Whisper Tiny',
      desc:  '~39 MB · fastest · good for English, lower accuracy',
    },
    {
      id:    'Xenova/whisper-base',
      label: 'Whisper Base',
      desc:  '~74 MB · balanced · recommended default',
    },
    {
      id:    'Xenova/whisper-small',
      label: 'Whisper Small',
      desc:  '~244 MB · most accurate · best for multilingual calls',
    },
  ];

  const cvOpts = [
    { key: 'cvDefaultEmotion',    label: 'Facial expression tracking' },
    { key: 'cvDefaultRpg',        label: 'Heart rate indicator (rPPG via camera)' },
    { key: 'cvDefaultProsody',    label: 'Vocal pattern analysis (tone & pitch)' },
    { key: 'cvDefaultLinguistic', label: 'Language pattern analysis' },
  ];

  el.innerHTML = `
    <div style="margin-bottom:1rem">
      <p style="font-size:.8rem;font-weight:700;color:var(--text);margin-bottom:.25rem">
        Transcription &amp; translation model
      </p>
      <p style="font-size:.71rem;color:var(--dim);margin-bottom:.6rem;line-height:1.45">
        Used for in-call speech recognition and batch translation (Tier 2).
        Downloaded once and cached locally — nothing is sent to the model provider.
      </p>
      ${whisperOpts.map(o => `
        <label style="display:flex;align-items:flex-start;gap:.55rem;
                      margin-bottom:.45rem;cursor:pointer">
          <input type="radio" name="whisper-model" value="${o.id}"
                 ${prefs.whisperModel === o.id ? 'checked' : ''}
                 onchange="setModelPref('whisperModel', this.value)"
                 style="margin-top:.2rem;accent-color:var(--accent)" />
          <span>
            <strong style="font-size:.8rem;color:var(--text)">${o.label}</strong>
            <br><span style="font-size:.7rem;color:var(--dim)">${o.desc}</span>
          </span>
        </label>`).join('')}
    </div>

    <div>
      <p style="font-size:.8rem;font-weight:700;color:var(--text);margin-bottom:.25rem">
        Call analysis — default modules
      </p>
      <p style="font-size:.71rem;color:var(--dim);margin-bottom:.6rem;line-height:1.45">
        Modules enabled at the start of every call. You can always adjust them
        live via the 📊 panel during a call. All analysis runs on your device only.
      </p>
      ${cvOpts.map(o => `
        <label style="display:flex;align-items:center;gap:.5rem;font-size:.78rem;
                      margin-bottom:.38rem;cursor:pointer;color:var(--text)">
          <input type="checkbox" ${prefs[o.key] ? 'checked' : ''}
                 onchange="setModelPref('${o.key}', this.checked)"
                 style="accent-color:var(--accent);width:15px;height:15px;flex-shrink:0" />
          ${o.label}
        </label>`).join('')}
    </div>`;
}

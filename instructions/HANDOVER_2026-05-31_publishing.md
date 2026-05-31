# WellFair — Session Handover: Publishing Prep (2026-05-31)

## What happened this session

Five things completed and committed on `release/v0.0.6`:

| Commit | What |
|---|---|
| `8f34f5b` | HCW-2: Nym bandwidth abstraction + `setModuleConsent` session guard |
| `38a3aec` | Call overlay UI redesign: full-screen, ticker, PiP, Info slide-out, Live drawer |
| `679a5f2` | Call profiles: 8 per-contact presets wired into directory + call overlay |
| `9ffb55a` | Model preferences panel: Whisper model selector + CV module defaults |

---

## Current branch state

- **Branch:** `release/v0.0.6`
- **Commits ahead of master:** 49
- **All working tree clean** — nothing uncommitted

---

## What was NOT completed this session (interrupted)

The user asked for three more things that were started but not finished:

### 1. README.md restructure (NOT done — no files changed)

**Task:** Split the current `README.md` into two files:
- `README.md` — human-centred overview for early adopters and potential collaborators
- `techinfo.md` — all current technical implementation detail

**Current `README.md`** is at `C:\Projects\health\README.md`. It is 472 lines, comprehensive
but heavily technical. The technical content should move to `techinfo.md`; the new `README.md`
should lead with the mission, use case (trafficking survivor), what works right now, how to
install, and how to contribute.

**Template approach for new README.md:**
- Open with the primary use case (see CLAUDE.md §"Why this exists")
- "What works today" section (vault + calls + profiles + wallet + sanctuary)
- Quick start (one-liner `python -m http.server 3000 --directory docs`)
- Links to demo mode (`vault.html?demo`)
- "What's coming" (HCW-3 through HCW-10, remaining epics)
- Contributing / collaboration call
- License (CC BY-NC-ND 4.0)

### 2. `pages.yml` update (NOT done)

**Task:** Simplify `.github/workflows/pages.yml` to skip the Rust WASM build and Python
stlite steps (both will fail in CI; neither is needed for the vault). Just deploy `docs/`
directly.

**Current file:** `.github/workflows/pages.yml` — builds Rust WASM + runs Python stlite build
before deploying `docs/`. These steps will fail because the Rust build is complex and the
Python scripts may not exist.

**New pages.yml should be:**
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - master

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs
      - uses: actions/deploy-pages@v4
        id: deployment
```

### 3. Merge release/v0.0.6 → master + push (NOT done)

**Task:** Merge the release branch into master so GitHub Pages deploys.

```bash
git checkout master
git merge release/v0.0.6 --no-ff -m "release: merge v0.0.6-dev into master for gh-pages"
git push origin master
```

After pushing, the pages workflow should trigger and the vault should be live at:
`https://mediaprophet.github.io/wellfair/vault.html`

---

## Model preferences feature (completed `9ffb55a`)

### What it does

A "⚙️ Model preferences" toggle card in the owner workspace (shown after PIN unlock).
Clicking it opens a panel with two sections:

1. **Transcription & translation model** — radio selector for Whisper model size:
   - Whisper Tiny (~39 MB) — fastest, English-focused
   - Whisper Base (~74 MB) — balanced, recommended default
   - Whisper Small (~244 MB) — most accurate, multilingual

2. **Call analysis defaults** — checkboxes for which CV modules start enabled at call start:
   - Facial expression tracking
   - Heart rate indicator (rPPG)
   - Vocal pattern analysis
   - Language pattern analysis

### Storage

`localStorage` key `wf-model-prefs` (JSON). Not health data — no encryption needed.

### API

```js
getModelPref('whisperModel')        // → 'Xenova/whisper-base' (or user choice)
setModelPref('cvDefaultEmotion', true)
getWhisperModelId()                 // in vault-comms-transcode.js — reads pref, fallback to base
```

### Call overlay integration

`_callOverlayOpen()` now reads CV defaults from prefs instead of always resetting to false.
So if the user has pre-enabled "Heart rate indicator", it starts enabled on every call.

---

## Call overlay (completed `38a3aec`)

Full-screen overlay shown on `wf:call` start, hidden on `wf:call` end.

- **Ticker strip** (top, 34px): live telemetry from vault-cv.js workers; falls back to call duration timer
- **Remote video**: fills overlay, `object-fit: cover`
- **Local PiP**: 112×84px, bottom-left
- **Control bar**: Mute, End, Share, 📋 Info, 📊 Live
- **Info slide-out**: right panel, shows contact name + call profile sections with Share buttons
- **Live drawer**: slides up, holds CV consent checkboxes (same IDs as old agent-panel)

---

## Call profiles (completed `679a5f2`)

8 profiles in `docs/js/vault-call-profiles.js`:

| ID | Icon | Sections |
|---|---|---|
| `generic_call` | 📞 | none |
| `health_consultation` | 🩺 | overview, vitals, meds, conditions, allergies |
| `mental_health_call` | 🧠 | mental health, sleep, psych meds |
| `social_work_call` | 🤝 | social context, emergency contacts |
| `specialist_call` | 🔬 | full clinical + surgical history |
| `carer_call` | 🏠 | overview, meds, conditions, allergies |
| `legal_call` | ⚖️ | none |
| `crisis_support_call` | 🆘 | social context, emergency contacts, mental health |

Stored as `callProfileId` on contact records in IDB. Shown as badge + inline change selector in
contact detail view. Profile icon appears next to contact name in the list.

---

## Script load order (vault.html tail — updated this session)

```
vault-directory.js?v=6
vault-call-profiles.js?v=1      ← new
vault-model-prefs.js?v=1        ← new
vault-handshake.js?v=6
vault-comms-gate.js?v=6
vault-comms-call.js?v=7
vault-cv.js?v=7.5               ← bumped (last session)
vault-scheduler.js?v=6
...
vault-wallet.js?v=2             ← bumped (HCW-2)
```

---

## HCW epic status

| Milestone | Status | Commit |
|---|---|---|
| HCW-1 — Lightning wallet + IDB v8 | ✅ complete | `e0f6eb2` |
| HCW-2 — Nym bandwidth abstraction | ✅ complete | `8f34f5b` |
| HCW-3 — Exchange on-ramp widget | not started | |
| HCW-4 through HCW-10 | not started | |

---

## First prompt for next session

See below (copy-paste as the opening message).

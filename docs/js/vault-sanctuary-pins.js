'use strict';

// ── Sanctuary Mode — PIN state machine, setup, canary, duress, wake lock ─────
// Depends on: vault-idb.js, vault-crypto.js, vault-nym.js

let sanctuaryKey     = null;
let sanctuaryActive  = false;
let duressModeActive = false;

// ── Canary verification and setup ─────────────────────────────────────────────

async function _sanctuaryExists() {
  const cfg = await _dbGet(_ST_CFG, 'wf-cfg');
  return !!(cfg && cfg.s_canary);
}

async function _verifySancPin(pin) {
  const key = await deriveVaultKey(pin, _SANC_SALT);
  const cfg = await _dbGet(_ST_CFG, 'wf-cfg');
  if (!cfg || !cfg.s_canary) return null;
  const canary = await _sDec(key, cfg.s_canary).catch(() => null);
  return canary === _S_CANARY_OK ? key : null;
}

async function _setupSanctuary(sPin, dPin) {
  const sKey = await deriveVaultKey(sPin, _SANC_SALT);
  const dKey = await deriveVaultKey(dPin, _DURS_SALT);
  const cfg  = (await _dbGet(_ST_CFG, 'wf-cfg')) || { id: 'wf-cfg' };
  cfg.s_canary = await _sEnc(sKey, _S_CANARY_OK);
  cfg.d_canary = await _sEnc(dKey, _D_CANARY_OK);
  await _dbPut(_ST_CFG, cfg);
}

// Duress check: if entered PIN matches duress PIN, activate decoy vault and
// fire a silent Nym alert. Returns true so caller opens the normal-looking workspace.
async function _checkAndFireDuress(pin) {
  try {
    const dKey = await deriveVaultKey(pin, _DURS_SALT);
    const cfg  = await _dbGet(_ST_CFG, 'wf-cfg');
    if (!cfg || !cfg.d_canary) return false;
    const canary = await _sDec(dKey, cfg.d_canary).catch(() => null);
    if (canary !== _D_CANARY_OK) return false;

    duressModeActive = true;
    console.warn('[WellFair] Duress mode — decoy vault active, firing silent alert');

    if (nymClient && cfg.d_contacts) {
      try {
        const contacts = await _sDec(dKey, cfg.d_contacts);
        const payload  = {
          type:      'duress_alert',
          vault_did: typeof vaultDidKey !== 'undefined' && vaultDidKey ? vaultDidKey.did : 'unknown',
          issued_at: new Date().toISOString(),
        };
        for (const c of contacts) {
          if (c.address) nymAdapter.send(c.address, payload).catch(() => {});
        }
      } catch (_) {}
    }
    return true;
  } catch (_) { return false; }
}

// ── Sanctuary PIN state machine ───────────────────────────────────────────────

let _spEntry   = '';
let _spSetup   = false;
let _spState   = null;
let _spSancPin = null;

function enterSanctuaryPinStep() {
  _spEntry = ''; _spSetup = false; _spState = null; _spSancPin = null;
  _updateSpDots('');
  document.getElementById('sanctuary-pin-hint').textContent        = 'Enter your Sanctuary PIN';
  document.getElementById('sanctuary-pin-hint').style.color        = '';
  document.getElementById('sanctuary-pin-banner-desc').textContent = 'Enter Sanctuary PIN to continue';
  showStep('step-sanctuary-pin');
}

function exitSanctuaryPinStep() {
  _spEntry = ''; _spSetup = false; _spState = null; _spSancPin = null;
  showStep('step-owner');
}

function _updateSpDots(state) {
  for (let i = 0; i < 4; i++) {
    const d = document.getElementById('spd' + i);
    if (!d) return;
    d.classList.toggle('filled', i < _spEntry.length && state !== 'error');
    d.classList.toggle('error',  state === 'error');
  }
}
function _spHint(msg, color) {
  const el = document.getElementById('sanctuary-pin-hint');
  el.textContent = msg; el.style.color = color || '';
}
function _spBannerDesc(msg) {
  document.getElementById('sanctuary-pin-banner-desc').textContent = msg;
}

async function sanctuaryPinKey(k) {
  if (k === 'del') { _spEntry = _spEntry.slice(0, -1); _updateSpDots(''); return; }
  if (_spEntry.length >= 4) return;
  _spEntry += k;
  _updateSpDots('');
  if (_spEntry.length < 4) return;

  const entered = _spEntry;
  const exists  = await _sanctuaryExists();

  if (!exists) {
    _spSetup = true; _spBannerDesc('First-time setup');
    await _handleSetupStep(entered); return;
  }

  const key = await _verifySancPin(entered);
  if (key) {
    _spHint('✓ Sanctuary PIN verified', 'var(--green)');
    setTimeout(() => _enterSanctuaryMode(key), 400);
  } else {
    _updateSpDots('error');
    _spHint('Incorrect PIN — try again', 'var(--red)');
    setTimeout(() => { _spEntry = ''; _updateSpDots(''); _spHint('Enter your Sanctuary PIN'); }, 1200);
  }
}

async function _handleSetupStep(entered) {
  if (!_spState) {
    _spState = { step: 'sanc_1', sPin: entered }; _spEntry = '';
    _updateSpDots(''); _spBannerDesc('Confirm Sanctuary PIN');
    _spHint('Re-enter sanctuary PIN to confirm'); return;
  }
  if (_spState.step === 'sanc_1') {
    if (entered !== _spState.sPin) {
      _updateSpDots('error'); _spHint('PINs do not match — start over', 'var(--red)');
      setTimeout(() => { _spState = null; _spEntry = ''; _updateSpDots('');
        _spBannerDesc('First-time setup'); _spHint('Choose a Sanctuary PIN'); }, 1400);
      return;
    }
    _spSancPin = entered; _spState = { step: 'durs_1' }; _spEntry = '';
    _updateSpDots(''); _spBannerDesc('Set Duress PIN');
    _spHint('Choose a duress PIN (shown to coercers — opens normal vault)'); return;
  }
  if (_spState.step === 'durs_1') {
    if (entered === _spSancPin) {
      _updateSpDots('error'); _spHint('Duress PIN must differ from Sanctuary PIN', 'var(--red)');
      setTimeout(() => { _spState = { step: 'durs_1' }; _spEntry = ''; _updateSpDots(''); }, 1200);
      return;
    }
    _spState = { step: 'durs_2', dPin: entered }; _spEntry = '';
    _updateSpDots(''); _spBannerDesc('Confirm Duress PIN');
    _spHint('Re-enter duress PIN to confirm'); return;
  }
  if (_spState.step === 'durs_2') {
    if (entered !== _spState.dPin) {
      _updateSpDots('error'); _spHint('PINs do not match — start over', 'var(--red)');
      setTimeout(() => { _spState = null; _spEntry = ''; _updateSpDots('');
        _spBannerDesc('First-time setup'); _spHint('Choose a Sanctuary PIN'); }, 1400);
      return;
    }
    _spHint('Setting up Sanctuary Mode…', 'var(--dim)');
    try {
      await _setupSanctuary(_spSancPin, entered);
      _spHint('✓ Sanctuary Mode set up', 'var(--green)');
      const key = await deriveVaultKey(_spSancPin, _SANC_SALT);
      setTimeout(() => _enterSanctuaryMode(key), 600);
    } catch (e) { _spHint('Setup failed: ' + e.message, 'var(--red)'); }
  }
}

// ── Wake Lock ─────────────────────────────────────────────────────────────────

let _wakeLock = null;

async function acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    _wakeLock = await navigator.wakeLock.request('screen');
    _wakeLock.addEventListener('release', () => { _wakeLock = null; });
    document.addEventListener('visibilitychange', _reacquireWakeLock);
  } catch (_) {}
}
async function _reacquireWakeLock() {
  if (_wakeLock === null && document.visibilityState === 'visible') await acquireWakeLock();
}
function releaseWakeLock() {
  document.removeEventListener('visibilitychange', _reacquireWakeLock);
  if (_wakeLock) { try { _wakeLock.release(); } catch (_) {} _wakeLock = null; }
}

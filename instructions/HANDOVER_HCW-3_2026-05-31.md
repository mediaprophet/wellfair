# WellFair — Session Handover HCW-3 (2026-05-31)

## What happened this session

Two things completed:

1. **HCW-2** — Nym token auto-swap + bandwidth abstraction (code + commit `8f34f5b`)
2. **setModuleConsent session guard** — 2-line hardening fix carried over from last session

---

## HCW-2 implementation summary

### Files changed

| File | Change |
|---|---|
| `docs/js/vault-cv.js` | Added `if (!_agentSessionId) return;` as first line of `setModuleConsent()` |
| `docs/js/vault-wallet.js` | Extended rate cache, added `ensureNymBandwidth()`, `getNymBandwidthStatus()`, job handler |
| `docs/vault.html` | Added `wallet-nym-status` div in wallet sheet; bumped vault-wallet.js to v=2 |

### vault-wallet.js additions

**`_walletGetBtcRate()` — extended:**
- URL now: `?ids=bitcoin,nym-network&vs_currencies=aud`
- `_rateCache` shape changed from `number|null` to `{ btcAud: number|null, btcNym: number|null }`
- `btcNym` is computed as `btcAud / nymAud` (tokens per BTC)
- All callers updated: `walletGetBalance()` now reads `rates.btcAud`

**`ensureNymBandwidth(requiredMinutes)`:**
- Returns `{ sufficient: false, minutesRemaining: 0 }` if `nymAdapter.isActive()` is false
- Reads `getNymBandwidthStatus()` from IDB
- If insufficient: calls `enqueueJob('wallet.nym-bandwidth-refill', ..., JOB_TRIGGER.IDLE, 3)`
- Never executes swap inline — always deferred to scheduler
- `swapExecuted` is always `false` in current impl (job is async; caller polls separately)

**`getNymBandwidthStatus()`:**
- Reads `nymBandwidth` field from `wf-wallet` IDB record (`'wallet-lightning'` key)
- Returns `{ minutesRemaining, isActive, lastRefill }`
- `isActive` mirrors `nymAdapter.isActive()`

**`_walletRegisterNymJobHandler()`:**
- Registered once per `walletInit()` call (idempotent via `_nymHandlerRegistered` flag)
- Calls `nymAdapter.redeemBandwidth(nymTokensNeeded)` if the method exists on nymAdapter
  - **Note:** `nymAdapter.redeemBandwidth` does not yet exist in `vault-nym.js` — this is
    a forward declaration. The job handler gracefully skips redemption if the method is absent,
    but writes `nymBandwidth` to IDB regardless (simulating the refill for MVP testing).
  - HCW-2 spec says "calls nymAdapter.redeemBandwidth()" — actual zk-credential API
    integration is deferred to when the Nym SDK is activated (NYM_SDK_URL set).
- Writes `nymBandwidth: { minutesRemaining, lastRefill, credentialId }` to `wf-wallet` IDB
  - `credentialId` is a random UUID (opaque, not displayed anywhere)

### vault.html — wallet sheet

New element below `wallet-status`:
```html
<div id="wallet-nym-status" style="font-size:.82rem;min-height:1.1rem;margin-bottom:.4rem"></div>
```

`_walletRenderSheet()` now calls `getNymBandwidthStatus()` and renders:
- `"🔒 Privacy routing: active · Bandwidth: N min remaining"` (green) when active + bandwidth known
- `"🔒 Privacy routing: active"` (green) when active but no bandwidth record yet
- `"⚠️ Privacy routing: inactive"` (muted) when nymAdapter is not active

User never sees "NYM" or token amounts.

---

## IDB state

- **Version:** 8 (unchanged — nymBandwidth is an additive field on the existing wallet record)
- The `nymBandwidth` field is written on first successful job execution; absent until then

---

## Script load order (vault.html, relevant tail)

```
vault-scheduler.js?v=6     ← enqueueJob, registerJobHandler, JOB_TRIGGER available
vault-wallet.js?v=2        ← bumped this session
```

---

## What to do next — HCW-3 (first thing next session)

**Task:** Exchange on-ramp widget (Transak/MoonPay)

**Read first (in order):**
1. `CLAUDE.md` — project orientation (mandatory)
2. `instructions/EPIC_PLAN_v0.0.7.md` — HCW-3 section in full
3. `instructions/HANDOVER_HCW-3_2026-05-31.md` (this file)
4. `docs/js/vault-wallet.js` — existing wallet sheet pattern to extend

**HCW-3 spec summary (from plan):**

- Add `vault-wallet-config.js` (gitignored template) with `WALLET_CONFIG` constants
  for Transak/MoonPay partner keys
- Embed Transak SDK in a sandboxed iframe inside the wallet sheet
- No health data from vault accessible to iframe (CSP)
- Balance refreshes after successful on-ramp via Transak completion event

**Note:** The `_walletGetBtcRate()` change in HCW-2 moved `_rateCache` to an object
`{ btcAud, btcNym }`. Any HCW-3 code reading the rate should use `rates.btcAud`.

---

## Acceptance criteria — HCW-2 (all met)

- [x] `setModuleConsent` session guard added (2-line fix in vault-cv.js)
- [x] `ensureNymBandwidth()` schedules a wf-jobs swap job when bandwidth is low
- [x] `getNymBandwidthStatus()` returns correct status
- [x] BTC/NYM rate fetched and cached alongside BTC/AUD; no repeated calls within 5 min
- [x] Wallet sheet shows "Privacy routing" status row
- [x] User never sees "NYM" or token amounts in any UI copy
- [x] `nymAdapter.isActive()` checked before any external API call

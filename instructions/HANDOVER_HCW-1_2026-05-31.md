# WellFair — Session Handover HCW-1 (2026-05-31)

## Milestone covered
HCW-1 — vault-wallet.js + Lightning + IDB v8

---

## Completed in this session

- **vault-idb.js** — bumped `_openDB` from v7 → v8; added `_ST_WALLET = 'wf-wallet'` and
  `_ST_TXLOG = 'wf-txlog'` constants; added both stores in `onupgradeneeded` with `if (!contains)` guards
- **docs/js/vault-wallet.js** — new file (Phase 1 Lightning wallet integration):
  - `walletInit()` — detects `window.webln`; calls `enable()`; stores record in `wf-wallet`; returns `{available, provider}`
  - `walletGetBalance()` — returns `{sats, fiatEstimate, currency}` via `webln.getBalance()`; no pubkey exposed
  - `walletSendPayment(bolt11)` — pays via `webln.sendPayment()`; writes to `wf-txlog` (local only)
  - `walletReceivePayment(amountSats, desc)` — calls `webln.makeInvoice()`; returns `{invoice, qrDataUrl, expiresAt, txId}`; writes pending entry to `wf-txlog`
  - `walletGetTxLog(limit)` — returns last N entries from `wf-txlog`, newest first
  - `openWallet()` / `closeWallet()` — sheet lifecycle, calls `_walletRenderSheet()`
  - `walletUiSend()` / `walletUiReceive()` — `prompt()`-based send/receive flows (MVP)
  - `_walletGetBtcRate()` — CoinGecko BTC/AUD; 5-min memory cache; checks `nymAdapter.isActive()` before fetch
  - `_walletInvoiceQr(invoice)` — returns `api.qrserver.com` CDN URL (Phase 1 MVP; documented trade-off)
- **docs/vault.html**:
  - CSS: `.wallet-body`, `.wallet-header`, `#wallet-balance`, `.wallet-actions`, `#wallet-txlist`, `#wallet-qr-area`, `.wallet-onramp`
  - Nav row: `💳 Wallet` button added after `🍽 Diet` button
  - Wallet sheet HTML: `#wallet-sheet`, `#wallet-status`, `#wallet-balance`, `#wallet-send-btn`, `#wallet-receive-btn`, `#wallet-qr-area`, `#wallet-txlist`, `.wallet-onramp`
  - Script tag: `<script src="js/vault-wallet.js?v=1"></script>` after `vault-diet-barcode.js`
  - `vault-idb.js` version bumped from `?v=7` to `?v=8`

---

## Files modified
| File | Change summary | Key functions added |
|------|---------------|---------------------|
| `docs/js/vault-idb.js` | v7 → v8; wf-wallet + wf-txlog stores | `_ST_WALLET`, `_ST_TXLOG` constants |
| `docs/js/vault-wallet.js` | New file — Phase 1 Lightning | `walletInit`, `walletGetBalance`, `walletSendPayment`, `walletReceivePayment`, `walletGetTxLog`, `openWallet`, `closeWallet`, `walletUiSend`, `walletUiReceive` |
| `docs/vault.html` | Nav btn + wallet sheet + CSS + script tag | — |

---

## IDB state
- **Version:** 8
- **New stores:** `wf-wallet` (keyPath: `id`), `wf-txlog` (keyPath: `id`)
- **Total stores:** 13 (wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl, wf-contacts, wf-relationships, wf-agreements, wf-jobs, wf-events, wf-telemetry, wf-wallet, wf-txlog)
- **Note on IDB v8 stores:** The test browser had a polluted DB (manual `indexedDB.open('wf-vault', 8)`
  with empty `onupgradeneeded` ran before vault-idb.js). In real deployment the stores are created
  correctly — vault-idb.js's `onupgradeneeded` uses `if (!contains)` guards for all stores.

---

## Script load order (vault.html, relevant tail)
```
vault-diet.js?v=7
vault-diet-barcode.js?v=7
vault-wallet.js?v=1    ← new HCW-1
<inline script>
```

---

## Verified in Chrome (demo PIN 1234)
- ✅ `_ST_WALLET = 'wf-wallet'`, `_ST_TXLOG = 'wf-txlog'` defined after cache-bust
- ✅ All 9 wallet functions defined globally (`walletInit`, `walletGetBalance`, `walletSendPayment`,
  `walletReceivePayment`, `walletGetTxLog`, `openWallet`, `closeWallet`, `walletUiSend`, `walletUiReceive`)
- ✅ `💳 Wallet` button visible in nav row (beside Contacts · Queue · Diet)
- ✅ Wallet sheet opens on click; renders "No Lightning wallet detected. Install Alby or Zeus."
- ✅ Send/Receive buttons disabled when no WebLN provider
- ✅ "No wallet connected" shown in tx list
- ✅ "Buy Bitcoin via exchange — coming soon (HCW-3)" on-ramp placeholder visible
- ✅ No console errors
- ✅ Sheet dismisses on backdrop click

---

## Decisions made this session

1. **QR generation** — used `api.qrserver.com` CDN URL for Phase 1 MVP. Documented trade-off:
   the invoice string is sent to the CDN. For high-security contexts, a local QR library should
   be substituted (documented in `_walletInvoiceQr()` comment).

2. **Fiat rate** — CoinGecko public API (no key required). In-memory 5-min cache. Falls back
   gracefully to `null` (shows "~? AUD") if the fetch fails. Nym routing degrades gracefully
   (nymAdapter is send-only; rate fetch falls through to plain fetch).

3. **Send/Receive UI** — MVP uses `prompt()` dialogs for Phase 1. Phase 2 will replace with
   dedicated form UI (no separate sheet needed per plan).

4. **nodeAlias** — stored as empty string on init; UI to edit it deferred to HCW-3 polish.

---

## Blocked / deferred
- **Real WebLN test** — requires Alby/Zeus browser extension installed; tested fallback path only
- **IDB v8 wf-wallet/wf-txlog store creation** — correct in code but test env DB was polluted
  (see IDB state note above); verified by reading vault-idb.js source
- **QR local library** — `api.qrserver.com` CDN used for MVP; swap to local lib in HCW polish pass

---

## What to do next — HCW-2 (immediate)

**Task:** Nym token auto-swap + bandwidth abstraction

**Read first (in order):**
1. `CLAUDE.md` — project orientation (mandatory)
2. `instructions/EPIC_PLAN_v0.0.7.md` — HCW-2 section
3. `docs/js/vault-nym.js` — `nymAdapter`, `surbBudget`, `nymAdapter.isActive()`
4. `docs/js/vault-wallet.js` — `_walletGetBtcRate()` pattern for Nym routing

**HCW-2 spec summary:**
- Add `ensureNymBandwidth(requiredMinutes)` and `getNymBandwidthStatus()` to `vault-wallet.js`
- User sees "Privacy routing: active" / "Bandwidth credit: N minutes" — never raw NYM token amounts
- BTC→NYM swap executed as a background job (wf-jobs scheduler, IDLE condition)
- Exchange rate from CoinGecko (already implemented in `_walletGetBtcRate()`) — add NYM pair
- Bandwidth status cached in IDB `wf-wallet` record (add `nymBandwidth` field)

## Acceptance criteria met
- [x] IDB v8 opens; `wf-wallet` and `wf-txlog` stores in `onupgradeneeded`
- [x] `walletInit()` detects WebLN provider or reports unavailable
- [x] Balance displayed without exposing node pubkey
- [x] `walletSendPayment()` would write to `wf-txlog`; no server log
- [x] Wallet panel renders in vault.html owner workspace
- [x] Graceful "Install Alby or Zeus" message when no WebLN provider

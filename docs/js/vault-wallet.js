'use strict';

// ── vault-wallet.js — HCW-1: Lightning wallet integration ────────────────────
// Phase 1: WebLN provider detection + local transaction log
// Phase 2+: Nym token auto-swap, exchange on-ramp (HCW-2, HCW-3)
// Phase 3+: Solana/AUDD stablecoin (HCW-7+)
//
// Privacy constraints (from threat model):
// - wf-txlog is local only — never transmitted over DataChannel
// - Node pubkey and channel info are never exposed to the UI
// - All external API calls must check nymAdapter.isActive() first
// - Wallet addresses are stored in IDB under the vault key only

// ── Internal state ────────────────────────────────────────────────────────────

let _wlProvider = null;   // 'webln' | null
let _wlAvailable = false;

// ── Helpers ───────────────────────────────────────────────────────────────────

function _txId() {
  return 'tx-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Detect WebLN provider (Alby, Zeus, etc.) and persist provider type in IDB.
 * Returns {available, provider}.
 * If window.webln is absent, returns {available: false} — UI shows install prompt.
 */
async function walletInit() {
  _wlAvailable = false;
  _wlProvider  = null;
  _walletRegisterNymJobHandler();

  if (typeof window.webln !== 'undefined') {
    try {
      await window.webln.enable();
      _wlProvider  = 'webln';
      _wlAvailable = true;

      const now = new Date().toISOString();
      // Read existing record to preserve createdAt
      const existing = await _dbGet(_ST_WALLET, 'wallet-lightning').catch(() => null);
      await _dbPut(_ST_WALLET, {
        id:         'wallet-lightning',
        type:       'lightning',
        provider:   'webln',
        nodeAlias:  '',
        createdAt:  existing?.createdAt ?? now,
        lastUsed:   now,
      });

      return { available: true, provider: 'webln' };
    } catch (err) {
      console.warn('[wallet] WebLN enable() failed:', err.message);
    }
  }

  return { available: false, provider: null };
}

/**
 * Returns {sats, fiatEstimate, currency}.
 * Never exposes node pubkey or channel info.
 */
async function walletGetBalance() {
  if (!_wlAvailable) throw new Error('Wallet not initialised — call walletInit() first');

  const info = await window.webln.getBalance();
  const sats = typeof info === 'object' && info !== null
    ? (info.balance ?? info.sats ?? 0)
    : Number(info ?? 0);

  // Fiat estimate: cached exchange rate lookup (Nym-routed when available)
  // Returns null if rate unavailable — UI shows "~? AUD" gracefully
  const rates = await _walletGetBtcRate().catch(() => null);
  const fiatEstimate = rates?.btcAud != null ? ((sats / 1e8) * rates.btcAud).toFixed(2) : null;

  await _dbPut(_ST_WALLET, Object.assign(
    (await _dbGet(_ST_WALLET, 'wallet-lightning').catch(() => ({
      id: 'wallet-lightning', type: 'lightning', provider: _wlProvider ?? 'webln',
      nodeAlias: '', createdAt: new Date().toISOString(),
    }))),
    { lastUsed: new Date().toISOString() }
  ));

  return { sats, fiatEstimate, currency: 'AUD' };
}

/**
 * Pay a BOLT11 invoice via WebLN.
 * Writes a local-only log entry to wf-txlog (never transmitted).
 * Lightning payments are peer-to-peer; Nym does not wrap the payment itself,
 * but any pre-payment metadata lookups (rate, etc.) are Nym-routed when active.
 */
async function walletSendPayment(bolt11Invoice) {
  if (!_wlAvailable) throw new Error('Wallet not initialised');
  if (!bolt11Invoice || typeof bolt11Invoice !== 'string') throw new Error('Invalid BOLT11 invoice');

  const result = await window.webln.sendPayment(bolt11Invoice);

  // Extract amount from payment result if available (provider-dependent)
  const amountSats = result?.payment_hash ? (result.route?.total_amt ?? 0) : 0;
  const description = result?.payment_hash ? 'Lightning payment' : 'Payment';

  await _dbPut(_ST_TXLOG, {
    id:          _txId(),
    type:        'send',
    amountSats:  amountSats,
    description: description,
    ts:          new Date().toISOString(),
    bolt11:      bolt11Invoice,
  });

  return result;
}

/**
 * Generate a BOLT11 receive invoice.
 * Returns {invoice, qrDataUrl, expiresAt}.
 * Writes a pending log entry to wf-txlog.
 */
async function walletReceivePayment(amountSats, description) {
  if (!_wlAvailable) throw new Error('Wallet not initialised');

  const req = await window.webln.makeInvoice({
    amount:          amountSats,
    defaultMemo:     description || 'WellFair payment',
    minimumAmount:   1,
    maximumAmount:   amountSats,
  });

  const invoice   = req.paymentRequest;
  const expiresAt = new Date(Date.now() + 30 * 60 * 1000).toISOString(); // 30 min default
  const qrDataUrl = await _walletInvoiceQr(invoice);
  const txId      = _txId();

  await _dbPut(_ST_TXLOG, {
    id:          txId,
    type:        'receive',
    amountSats:  amountSats,
    description: description || '',
    ts:          new Date().toISOString(),
    bolt11:      invoice,
    status:      'pending',
    expiresAt:   expiresAt,
  });

  return { invoice, qrDataUrl, expiresAt, txId };
}

/**
 * Returns the last `limit` entries from wf-txlog, newest first.
 */
async function walletGetTxLog(limit) {
  const all = await _dbGetAll(_ST_TXLOG);
  all.sort((a, b) => b.ts.localeCompare(a.ts));
  return limit ? all.slice(0, limit) : all;
}

// ── Internal helpers ──────────────────────────────────────────────────────────

// Exchange rate cache — BTC/AUD + BTC/NYM, shared 5-min memory cache
let _rateCache   = null; // { btcAud: number|null, btcNym: number|null }
let _rateCacheTs = 0;

/**
 * Fetch BTC/AUD and BTC/NYM rates from CoinGecko public API.
 * Cached for 5 minutes in memory.
 * NOTE: nymAdapter.send() is fire-and-forget (send-only model); this call falls through
 * to plain HTTPS for MVP. Routing this via Nym is deferred until the full duplex model
 * is implemented. Exchange rates are not sensitive — the call reveals no user data.
 * Returns { btcAud, btcNym }.
 */
async function _walletGetBtcRate() {
  const now = Date.now();
  if (_rateCache !== null && now - _rateCacheTs < 5 * 60 * 1000) return _rateCache;

  // Check nymAdapter availability — not yet routable in send-only model (see note above)
  if (typeof nymAdapter !== 'undefined' && nymAdapter.isActive()) {
    // nymAdapter.send() is fire-and-forget; fall through to plain fetch for MVP
  }

  const url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,nym-network&vs_currencies=aud';
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('Rate fetch failed');
  const json = await resp.json();

  _rateCache = {
    btcAud: json?.bitcoin?.aud        ?? null,
    btcNym: json?.['nym-network']?.aud
              ? (json.bitcoin.aud / json['nym-network'].aud) : null,
  };
  _rateCacheTs = now;
  return _rateCache;
}

// ── Nym bandwidth abstraction (HCW-2) ────────────────────────────────────────

const NYM_BANDWIDTH_MINUTES_LOW = 10; // schedule refill when below this

/**
 * Ensure the Nym bandwidth credential has at least requiredMinutes remaining.
 * If insufficient, schedules a background BTC→NYM swap job (IDLE condition).
 * Never executes the swap inline — always defers to the job scheduler.
 * Returns { sufficient: bool, minutesRemaining: number, swapExecuted: bool }.
 * If nymAdapter is not active, returns { sufficient: false, minutesRemaining: 0 }.
 */
async function ensureNymBandwidth(requiredMinutes) {
  if (typeof nymAdapter === 'undefined' || !nymAdapter.isActive()) {
    return { sufficient: false, minutesRemaining: 0, swapExecuted: false };
  }

  const status = await getNymBandwidthStatus();
  if (status.minutesRemaining >= requiredMinutes) {
    return { sufficient: true, minutesRemaining: status.minutesRemaining, swapExecuted: false };
  }

  // Schedule a background swap — never block UI thread or run inline
  if (typeof enqueueJob === 'function' && typeof JOB_TRIGGER !== 'undefined') {
    await enqueueJob(
      'wallet.nym-bandwidth-refill',
      { requestedMinutes: Math.max(requiredMinutes, 60) }, // request at least 60 min
      JOB_TRIGGER.IDLE,
      3 // priority
    ).catch(e => console.warn('[wallet] enqueueJob failed:', e.message));
  }

  return { sufficient: false, minutesRemaining: status.minutesRemaining, swapExecuted: false };
}

/**
 * Returns current Nym bandwidth status for UI display.
 * { minutesRemaining: number, isActive: bool, lastRefill: string|null }
 * isActive mirrors nymAdapter.isActive().
 * User-facing: never surfaces NYM token amounts — only "Privacy routing" / "Bandwidth credit".
 */
async function getNymBandwidthStatus() {
  const isActive = typeof nymAdapter !== 'undefined' && nymAdapter.isActive();

  let minutesRemaining = 0;
  let lastRefill       = null;

  try {
    const rec = await _dbGet(_ST_WALLET, 'wallet-lightning').catch(() => null);
    if (rec?.nymBandwidth) {
      minutesRemaining = rec.nymBandwidth.minutesRemaining ?? 0;
      lastRefill       = rec.nymBandwidth.lastRefill       ?? null;
    }
  } catch (_) {}

  return { minutesRemaining, isActive, lastRefill };
}

/**
 * Register the bandwidth refill job handler with vault-scheduler.js.
 * Called once during wallet init. No-op if scheduler is not loaded.
 * The handler fetches BTC/NYM rate, computes NYM tokens needed,
 * calls nymAdapter.redeemBandwidth(), and updates the wf-wallet IDB record.
 * Wallet addresses and swap amounts are never written to any log.
 */
let _nymHandlerRegistered = false;
function _walletRegisterNymJobHandler() {
  if (typeof registerJobHandler !== 'function') return;
  if (_nymHandlerRegistered) return;
  _nymHandlerRegistered = true;

  registerJobHandler('wallet.nym-bandwidth-refill', {
    estimateFn: () => 30_000, // ~30 s estimate
    runFn: async (job) => {
      const payload = JSON.parse(job.payload || '{}');
      const requestedMinutes = payload.requestedMinutes ?? 60;

      // Fetch rates (5-min cache shared with _walletGetBtcRate)
      const rates = await _walletGetBtcRate();
      if (!rates.btcNym) throw new Error('BTC/NYM rate unavailable');

      // Determine BTC cost of requested bandwidth (1 NYM ≈ 1 min of routing — placeholder)
      // Real redemption depends on Nym zk-credential API; this schedules the intent.
      const nymTokensNeeded = requestedMinutes; // 1 token ≈ 1 minute (MVP placeholder)

      // Redeem bandwidth credential via nymAdapter if active
      if (typeof nymAdapter !== 'undefined' && nymAdapter.isActive()
          && typeof nymAdapter.redeemBandwidth === 'function') {
        await nymAdapter.redeemBandwidth(nymTokensNeeded);
      }

      // Update IDB record — additive field, no version bump needed
      const existing = await _dbGet(_ST_WALLET, 'wallet-lightning').catch(() => ({
        id: 'wallet-lightning', type: 'lightning', provider: 'webln',
        nodeAlias: '', createdAt: new Date().toISOString(),
      }));
      await _dbPut(_ST_WALLET, Object.assign(existing, {
        nymBandwidth: {
          minutesRemaining: requestedMinutes,
          lastRefill:       new Date().toISOString(),
          credentialId:     crypto.randomUUID(), // opaque — not displayed
        },
      }));

      return { minutesRefilled: requestedMinutes };
    },
  });
}

// Minimal QR code generator using the free qrserver CDN (no JS library needed)
// For privacy-sensitive contexts the user is advised to use Nym-routed requests.
// The invoice string itself is not PII; it is a single-use payment request.
async function _walletInvoiceQr(invoice) {
  // Use a data URI from the qrserver API — the invoice is sent to the CDN.
  // For high-security contexts, a local QR library (e.g. qrcode-generator) should
  // be substituted. This is a Phase 1 MVP trade-off documented here.
  const encoded = encodeURIComponent(invoice);
  return `https://api.qrserver.com/v1/create-qr-code/?data=${encoded}&size=256x256&format=png`;
}

// ── Wallet UI helpers (called from vault.html) ────────────────────────────────

async function openWallet() {
  const sheet = document.getElementById('wallet-sheet');
  if (!sheet) return;
  sheet.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  await _walletRenderSheet();
}

function closeWallet() {
  const sheet = document.getElementById('wallet-sheet');
  if (sheet) sheet.style.display = 'none';
  document.body.style.overflow = '';
  // Clear any displayed invoice QR to avoid stale data
  const qrArea = document.getElementById('wallet-qr-area');
  if (qrArea) qrArea.innerHTML = '';
}

async function _walletRenderSheet() {
  const statusEl  = document.getElementById('wallet-status');
  const balanceEl = document.getElementById('wallet-balance');
  const txListEl  = document.getElementById('wallet-txlist');
  if (!statusEl || !balanceEl || !txListEl) return;

  // Detect / init provider
  const init = await walletInit();

  if (!init.available) {
    statusEl.innerHTML =
      '<span style="color:var(--muted)">No Lightning wallet detected.<br>' +
      'Install <a href="https://getalby.com" target="_blank" rel="noopener">Alby</a> or ' +
      '<a href="https://zeusln.app" target="_blank" rel="noopener">Zeus</a> to connect.</span>';
    balanceEl.textContent = '—';
    txListEl.innerHTML    = '<li style="color:var(--muted);font-size:.82rem">No wallet connected</li>';
    document.getElementById('wallet-send-btn').disabled    = true;
    document.getElementById('wallet-receive-btn').disabled = true;
    return;
  }

  statusEl.innerHTML = '<span style="color:var(--success,#2a7)">⚡ Lightning wallet connected</span>';
  document.getElementById('wallet-send-btn').disabled    = false;
  document.getElementById('wallet-receive-btn').disabled = false;

  // Privacy routing status row (HCW-2)
  const nymRowEl = document.getElementById('wallet-nym-status');
  if (nymRowEl) {
    try {
      const nymStatus = await getNymBandwidthStatus();
      if (nymStatus.isActive) {
        const bandwidthLabel = nymStatus.minutesRemaining > 0
          ? ` · Bandwidth: ${nymStatus.minutesRemaining} min remaining`
          : '';
        nymRowEl.innerHTML =
          `<span style="color:var(--success,#2a7)">&#x1F512; Privacy routing: active</span>` +
          `<span style="color:var(--muted);font-size:.8rem">${bandwidthLabel}</span>`;
      } else {
        nymRowEl.innerHTML =
          `<span style="color:var(--muted)">&#x26A0;&#xFE0F; Privacy routing: inactive</span>`;
      }
    } catch (_) {
      nymRowEl.innerHTML = '';
    }
  }

  // Balance
  try {
    const bal = await walletGetBalance();
    balanceEl.innerHTML =
      `<strong>${bal.sats.toLocaleString()}</strong> sats` +
      (bal.fiatEstimate !== null
        ? ` <span style="color:var(--muted);font-size:.82rem">(≈ ${bal.currency} ${bal.fiatEstimate})</span>`
        : '');
  } catch (e) {
    balanceEl.textContent = 'Balance unavailable';
  }

  // Recent transactions
  const txs = await walletGetTxLog(10);
  if (txs.length === 0) {
    txListEl.innerHTML = '<li style="color:var(--muted);font-size:.82rem">No transactions yet</li>';
  } else {
    txListEl.innerHTML = txs.map(tx => {
      const dir   = tx.type === 'send' ? '↑ Sent' : '↓ Received';
      const color = tx.type === 'send' ? 'var(--danger,#c44)' : 'var(--success,#2a7)';
      const when  = new Date(tx.ts).toLocaleString();
      const sats  = tx.amountSats ? `${tx.amountSats.toLocaleString()} sats` : '';
      return `<li style="padding:.35rem 0;border-bottom:1px solid var(--border,#eee);font-size:.83rem">
        <span style="color:${color};font-weight:600">${dir}</span>
        ${sats ? ` · <span>${sats}</span>` : ''}
        ${tx.description ? ` · <span style="color:var(--muted)">${_esc(tx.description)}</span>` : ''}
        <br><span style="color:var(--muted);font-size:.75rem">${when}</span>
      </li>`;
    }).join('');
  }
}

function _esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Send flow
async function walletUiSend() {
  const invoice = prompt('Paste BOLT11 invoice:');
  if (!invoice || !invoice.trim()) return;
  const statusEl = document.getElementById('wallet-status');
  try {
    statusEl.textContent = 'Paying…';
    await walletSendPayment(invoice.trim());
    statusEl.innerHTML = '<span style="color:var(--success,#2a7)">Payment sent!</span>';
    await _walletRenderSheet();
  } catch (e) {
    statusEl.innerHTML = `<span style="color:var(--danger,#c44)">Payment failed: ${_esc(e.message)}</span>`;
  }
}

// Receive flow
async function walletUiReceive() {
  const amtStr = prompt('Amount to receive (sats):');
  if (!amtStr) return;
  const sats = parseInt(amtStr, 10);
  if (!sats || sats < 1) { alert('Enter a valid amount in satoshis.'); return; }
  const desc = prompt('Description (optional):') || '';

  const statusEl = document.getElementById('wallet-status');
  const qrArea   = document.getElementById('wallet-qr-area');
  try {
    statusEl.textContent = 'Generating invoice…';
    const { invoice, qrDataUrl, expiresAt } = await walletReceivePayment(sats, desc);
    const expiryLabel = new Date(expiresAt).toLocaleTimeString();
    qrArea.innerHTML =
      `<div style="text-align:center;margin-top:.8rem">
        <img src="${qrDataUrl}" alt="Payment QR" style="width:180px;height:180px;border-radius:8px">
        <p style="font-size:.75rem;color:var(--muted);margin:.4rem 0 0">Expires ~${expiryLabel}</p>
        <textarea rows="3" readonly style="width:100%;font-size:.68rem;margin-top:.4rem;
          resize:none;border-radius:6px;border:1px solid var(--border,#ddd);padding:.3rem"
        >${_esc(invoice)}</textarea>
      </div>`;
    statusEl.innerHTML = '<span style="color:var(--success,#2a7)">Invoice ready — share QR or copy invoice</span>';
  } catch (e) {
    statusEl.innerHTML = `<span style="color:var(--danger,#c44)">Failed: ${_esc(e.message)}</span>`;
  }
}

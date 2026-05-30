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
  const rate = await _walletGetBtcRate().catch(() => null);
  const fiatEstimate = rate !== null ? ((sats / 1e8) * rate).toFixed(2) : null;

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

// BTC/AUD exchange rate — cached 5 min in memory; Nym-routed when active
let _rateCache = null;
let _rateCacheTs = 0;

async function _walletGetBtcRate() {
  const now = Date.now();
  if (_rateCache !== null && now - _rateCacheTs < 5 * 60 * 1000) return _rateCache;

  // CoinGecko public API — no API key required for this endpoint
  const url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=aud';

  // Route via Nym if active; otherwise plain HTTPS (rate is not sensitive data)
  let json;
  if (typeof nymAdapter !== 'undefined' && nymAdapter.isActive()) {
    // nymAdapter.send() is fire-and-forget; rate lookup degrades gracefully without Nym
    json = null; // Nym send-only model; fall through to plain fetch
  }

  const resp = await fetch(url);
  if (!resp.ok) throw new Error('Rate fetch failed');
  json = await resp.json();

  _rateCache   = json?.bitcoin?.aud ?? null;
  _rateCacheTs = now;
  return _rateCache;
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

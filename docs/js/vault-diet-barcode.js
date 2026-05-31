'use strict';

// ── Diet Log — Barcode Scanning + Open Food Facts pre-fill (DL-1) ─────────────
// Depends on: vault-nym.js (nymAdapter.isActive)
//
// Privacy note: An OFF barcode lookup identifies a product, not a person.
// For standard use, plain HTTPS fetch is acceptable. When nymAdapter.isActive()
// is true (Nym mixnet client connected), the fetch is also via plain HTTPS today —
// a future session should wire nymAdapter.fetch() for true Nym HTTP routing when
// high-risk users activate it. See EPIC_PLAN_v0.0.7.md §DL-1 privacy note.

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Opens camera and scans for a food barcode.
 * Primary path: BarcodeDetector API (Chrome/Edge 83+, no extra library).
 * Fallback path: ZXing-js loaded from CDN (Firefox / Safari).
 *
 * @param {HTMLVideoElement} videoEl - video element to stream into
 * @param {function}         onDetected - called with barcode string on first detection
 * @returns {Promise<function>} resolves to a stopFn — call to cancel without result
 */
async function dlStartBarcodeScanner(videoEl, onDetected) {
  let stopped     = false;
  let stream      = null;
  let rafId       = null;
  let zxingReader = null;

  const releaseCamera = () => {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    if (videoEl.srcObject) {
      videoEl.srcObject.getTracks().forEach(t => t.stop());
      videoEl.srcObject = null;
    }
    videoEl.style.display = 'none';
  };

  const stop = () => {
    stopped = true;
    if (rafId)       { cancelAnimationFrame(rafId); rafId = null; }
    if (zxingReader) { try { zxingReader.reset(); } catch (_) {} zxingReader = null; }
    releaseCamera();
  };

  if (typeof BarcodeDetector !== 'undefined') {
    // ── Primary: native BarcodeDetector ─────────────────────────────────────
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
    } catch (e) {
      throw new Error('Camera access denied: ' + e.message);
    }
    videoEl.srcObject = stream;
    videoEl.style.display = 'block';
    await videoEl.play();

    const detector = new BarcodeDetector({
      formats: ['ean_13', 'upc_a', 'upc_e', 'ean_8', 'ean_5', 'ean_2', 'code_128', 'code_39']
    });

    const scan = async () => {
      if (stopped) return;
      try {
        const barcodes = await detector.detect(videoEl);
        if (barcodes.length > 0) {
          stop();
          onDetected(barcodes[0].rawValue);
          return;
        }
      } catch (_) {}
      if (!stopped) rafId = requestAnimationFrame(scan);
    };
    rafId = requestAnimationFrame(scan);

  } else {
    // ── Fallback: ZXing-js from CDN ──────────────────────────────────────────
    // Only loaded when BarcodeDetector is unavailable (Firefox, older Safari).
    let ZXing;
    try {
      ZXing = await import('https://cdn.jsdelivr.net/npm/@zxing/browser@latest/+esm');
    } catch (e) {
      throw new Error('Barcode scanning unavailable in this browser: ' + e.message);
    }

    zxingReader = new ZXing.BrowserMultiFormatReader();
    videoEl.style.display = 'block';

    // decodeFromConstraints opens its own camera stream into videoEl and calls
    // back on every frame that yields a result.
    zxingReader.decodeFromConstraints(
      { video: { facingMode: 'environment' } },
      videoEl,
      (result, err) => {
        if (stopped || !result) return;
        stop();
        onDetected(result.getText());
      }
    ).catch(e => {
      if (!stopped) console.warn('[WellFair] ZXing scan error:', e.message);
    });
  }

  return stop;
}

/**
 * Fetches product info from Open Food Facts for the given barcode.
 * Routes via Nym when nymAdapter.isActive() — currently still plain HTTPS;
 * a Nym HTTP adapter is a future task.
 *
 * @param {string} barcode  EAN-13, UPC-A, etc.
 * @returns {Promise<{found: boolean, fields?: object, raw?: object}>}
 */
async function dlLookupBarcode(barcode) {
  const url = 'https://world.openfoodfacts.org/api/v2/product/' + barcode + '.json' +
    '?fields=product_name,brands,serving_size,nutriments,categories_tags,image_url,code';

  let data;
  try {
    // nymAdapter.isActive() check is here for future Nym HTTP routing;
    // both paths use plain fetch for now (OFF lookups don't expose user identity).
    const resp = await fetch(url, {
      headers: { 'User-Agent': 'WellFair-vault/0.0.6 (+https://wellfare.social)' }
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    data = await resp.json();
  } catch (e) {
    console.warn('[WellFair] OFF lookup failed:', e.message);
    return { found: false };
  }

  if (!data || data.status === 0 || !data.product) return { found: false };

  // Pass the barcode from the top-level response (data.code) — it isn't always
  // present inside data.product depending on the fields query.
  const fields = _mapOffProduct(data.product, data.code || barcode);
  return { found: true, fields, raw: data.product };
}

// ── Internal ──────────────────────────────────────────────────────────────────

/**
 * Maps an Open Food Facts product object → vault-diet.js field names.
 * Prefers *_serving nutriment values; falls back to *_100g values.
 * Stores barcode + categories_tags in notes for future FoodOn/LOD enrichment.
 */
function _mapOffProduct(p, barcode) {
  const n      = p.nutriments || {};
  const fields = {};

  if (p.product_name) fields.name  = p.product_name;
  if (p.brands)       fields.brand = p.brands.split(',')[0].trim();

  // Parse serving_size strings like "30 g", "250 ml", "1 biscuit (40g)"
  if (p.serving_size) {
    const m = p.serving_size.match(/([\d.]+)\s*(g|ml|oz|kg|l)\b/i);
    if (m) {
      let qty  = parseFloat(m[1]);
      let unit = m[2].toLowerCase();
      if (unit === 'kg') { qty *= 1000; unit = 'g'; }
      if (unit === 'l')  { qty *= 1000; unit = 'ml'; }
      fields.quantity = qty;
      fields.unit     = unit;
    } else {
      fields.quantity = 1;
      fields.unit     = 'serving';
    }
  }

  // Macro nutrients — prefer per-serving, fall back to per-100g
  fields.kcal      = _nutriVal(n, 'energy-kcal');
  fields.protein_g = _nutriVal(n, 'proteins');
  fields.carbs_g   = _nutriVal(n, 'carbohydrates');
  fields.fat_g     = _nutriVal(n, 'fat');
  fields.fiber_g   = _nutriValOpt(n, 'fiber');
  fields.sugar_g   = _nutriValOpt(n, 'sugars');

  // OFF stores sodium in grams; wf-dl uses mg.
  // Use raw value (not rounded helper) to avoid precision loss before ×1000 conversion.
  const sodiumRawG = n['sodium_serving'] != null ? parseFloat(n['sodium_serving'])
                   : n['sodium_100g']    != null ? parseFloat(n['sodium_100g']) : null;
  if (sodiumRawG != null && !isNaN(sodiumRawG)) fields.sodium_mg = Math.round(sodiumRawG * 1000);

  // Store OFF metadata in notes as a JSON prefix for future FoodOn / LOD enrichment.
  // Format: {"barcode":"...","categories_tags":[...]}  followed by any user notes.
  const meta = {};
  if (barcode)                                       meta.barcode         = barcode;
  if (p.categories_tags && p.categories_tags.length) meta.categories_tags = p.categories_tags;
  if (Object.keys(meta).length) fields.notes = JSON.stringify(meta);

  fields.source = 'barcode';
  return fields;
}

// Returns nutriment value preferring *_serving, falling back to *_100g.
// Returns 0 (not null) — used for required macro fields.
function _nutriVal(n, key) {
  const v = n[key + '_serving'] != null ? n[key + '_serving'] : n[key + '_100g'];
  if (v == null) return 0;
  return Math.round(parseFloat(v) * 10) / 10;
}

// Same but returns null when absent — used for optional fields.
function _nutriValOpt(n, key) {
  const v = n[key + '_serving'] != null ? n[key + '_serving'] : n[key + '_100g'];
  if (v == null) return null;
  return Math.round(parseFloat(v) * 10) / 10;
}

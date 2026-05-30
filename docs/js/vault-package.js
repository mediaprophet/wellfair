'use strict';

// ── Content Package & Manifest (VC-15) ────────────────────────────────────────
// Collects session artefacts (transcript HTML, events NDJSON, VP receipts),
// generates a JSON-LD wf:ContentPackage manifest, anchors the manifest hash to
// Bitcoin via OpenTimestamps, and downloads the package as a zip.
//
// Depends on: vault-idb.js (_ST_EVENTS, _ST_LOG, _ST_JOBS, _dbGetAll),
//             vault-crypto.js (toB64), vault-scheduler.js (registerJobHandler, enqueueJob)
//
// Public API:
//   buildPackage(sessionId) → { manifest, files: Map<name, Blob> }
//   downloadPackage(sessionId)
//   generateManifest(sessionId, artefacts, odrlPolicyRef) → JSON-LD object

// ── OTS calendar endpoints (same list as vault-sanctuary-evidence.js) ──────────

const _PKG_OTS_CALENDARS = [
  'https://alice.btc.calendar.opentimestamps.org',
  'https://bob.btc.calendar.opentimestamps.org',
  'https://finney.calendar.opentimestamps.org',
];

// ── SHA-256 helpers ───────────────────────────────────────────────────────────

async function _pkgSha256Bytes(buf) {
  return new Uint8Array(await crypto.subtle.digest('SHA-256', buf));
}

async function _pkgSha256Str(str) {
  const bytes = await _pkgSha256Bytes(new TextEncoder().encode(str));
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function _pkgHashBlob(blob) {
  const buf   = await blob.arrayBuffer();
  const bytes = await _pkgSha256Bytes(buf);
  return 'sha256-' + Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

// ── Artefact collection ───────────────────────────────────────────────────────

// Retrieve the HTML transcript for a session from the most recent completed
// transcript.generate job result.
async function _pkgGetTranscriptHtml(sessionId) {
  const jobs = await _dbGetAll(_ST_JOBS);
  const done = jobs
    .filter(j => j.type === 'transcript.generate' && j.status === 'done' && j.result_ref)
    .map(j => { try { return JSON.parse(j.result_ref); } catch (_) { return null; } })
    .filter(r => r && r.sessionId === sessionId && r.html);
  if (done.length) return done[done.length - 1].html;

  // Fall back to generating it fresh
  if (typeof generateTranscript === 'function') return generateTranscript(sessionId);
  return null;
}

// Collect all events for a session as NDJSON.
async function _pkgGetEventsNdjson(sessionId) {
  const all    = await _dbGetAll(_ST_EVENTS);
  const events = all.filter(e => e.sessionId === sessionId)
                    .sort((a, b) => a.seq - b.seq);
  return events.map(e => JSON.stringify(e)).join('\n');
}

// Collect VP receipts stored in wf-s that reference this callSessionId.
async function _pkgGetReceipts(sessionId) {
  const all = await _dbGetAll(_ST_LOG);
  return all.filter(r =>
    r['wf:callSessionId'] === sessionId || r.callSessionId === sessionId
  );
}

// ── Manifest generation ───────────────────────────────────────────────────────

function generateManifest(sessionId, artefacts, odrlPolicyRef) {
  return {
    '@context': {
      'wf':      'https://wellfare.social/ns/vault#',
      'dcterms': 'http://purl.org/dc/terms/',
      'odrl':    'http://www.w3.org/ns/odrl/2/',
    },
    '@type': 'wf:ContentPackage',
    '@id':   'urn:uuid:' + sessionId,
    'dcterms:title':   'WellFair Communication Package — ' + sessionId.slice(0, 8),
    'dcterms:created': new Date().toISOString(),
    'odrl:hasPolicy':  odrlPolicyRef ? { '@id': odrlPolicyRef } : null,
    'wf:artefacts':    artefacts,
    'wf:revisionChainRoot': null, // set if revisions present
    'wf:otsProof':     null,      // set when OTS confirmed
  };
}

// ── Build package ─────────────────────────────────────────────────────────────

async function buildPackage(sessionId) {
  const files = new Map();

  // 1. Transcript HTML
  const html = await _pkgGetTranscriptHtml(sessionId);
  const transcriptBlob = new Blob([html || '<!-- no transcript -->'], { type: 'text/html' });
  files.set('transcript.html', transcriptBlob);

  // 2. Events NDJSON
  const ndjson = await _pkgGetEventsNdjson(sessionId);
  const eventsBlob = new Blob([ndjson || ''], { type: 'application/x-ndjson' });
  files.set('events.ndjson', eventsBlob);

  // 3. VP receipts
  const receipts = await _pkgGetReceipts(sessionId);
  const receiptBlob = new Blob(
    [JSON.stringify({ sessionId, receipts }, null, 2)],
    { type: 'application/json' }
  );
  files.set('receipts.json', receiptBlob);

  // 4. Compute artefact hashes
  const artefacts = [
    {
      '@type':          'wf:TranscriptArtefact',
      'wf:hash':        await _pkgHashBlob(transcriptBlob),
      'wf:filename':    'transcript.html',
      'dcterms:format': 'text/html',
    },
    {
      '@type':          'wf:EventLogArtefact',
      'wf:hash':        await _pkgHashBlob(eventsBlob),
      'wf:filename':    'events.ndjson',
      'dcterms:format': 'application/x-ndjson',
    },
    {
      '@type':       'wf:ReceiptArtefact',
      'wf:hash':     await _pkgHashBlob(receiptBlob),
      'wf:filename': 'receipts.json',
    },
  ];

  // Revision chain root from first revision event
  const allEvents = await _dbGetAll(_ST_EVENTS);
  const revisions = allEvents.filter(e => e.sessionId === sessionId && e.type === 'revision')
                             .sort((a, b) => a.ts < b.ts ? -1 : 1);

  const manifest = generateManifest(sessionId, artefacts, null);
  if (revisions.length) manifest['wf:revisionChainRoot'] = revisions[0].hash;

  const manifestJson = JSON.stringify(manifest, null, 2);
  const manifestBlob = new Blob([manifestJson], { type: 'application/ld+json' });
  files.set('manifest.jsonld', manifestBlob);

  // 5. Submit manifest hash to OTS
  const manifestHash = await _pkgSha256Bytes(
    new TextEncoder().encode(manifestJson)
  );
  manifest['wf:manifestHash'] = 'sha256-' +
    Array.from(manifestHash).map(b => b.toString(16).padStart(2,'0')).join('');

  enqueueJob &&
    enqueueJob('ots.submit', { sessionId, hash: toB64(manifestHash) }, JOB_TRIGGER.ALWAYS, 2)
      .catch(() => {});

  return { manifest, files };
}

// ── Download package ──────────────────────────────────────────────────────────

async function downloadPackage(sessionId) {
  const { files } = await buildPackage(sessionId);

  // Try File System Access API first (allows save-as dialog + single zip)
  if (typeof showSaveFilePicker === 'function') {
    try {
      const handle = await showSaveFilePicker({
        suggestedName: 'wellfair-package-' + sessionId.slice(0, 8) + '.zip',
        types: [{ description: 'ZIP archive', accept: { 'application/zip': ['.zip'] } }],
      });
      const writable = await handle.createWritable();
      const zipBytes = await _pkgBuildZip(files);
      await writable.write(zipBytes);
      await writable.close();
      return;
    } catch (e) {
      if (e.name === 'AbortError') return; // user cancelled
      // Fall through to individual downloads
    }
  }

  // Fallback: download each file individually
  for (const [name, blob] of files) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href = url; a.download = 'wellfair-' + sessionId.slice(0, 8) + '-' + name;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
    // Brief pause between downloads to avoid browser blocking
    await new Promise(r => setTimeout(r, 200));
  }
}

// ── Minimal ZIP builder (no dependencies, stored compression) ─────────────────
// Implements ZIP spec: PKWARE APPNOTE 6.3. Method 0 = stored (no compression).

async function _pkgBuildZip(files) {
  const enc        = new TextEncoder();
  const localParts = []; // { header, data, offset, nameBuf }
  let   offset     = 0;

  for (const [name, blob] of files) {
    const nameBuf  = enc.encode(name);
    const dataBuf  = new Uint8Array(await blob.arrayBuffer());
    const crc      = _pkgCrc32(dataBuf);
    const size     = dataBuf.length;
    const header   = new Uint8Array(30 + nameBuf.length);
    const dv       = new DataView(header.buffer);

    dv.setUint32( 0, 0x04034b50, true); // local file header sig
    dv.setUint16( 4, 20, true);          // version needed
    dv.setUint16( 6, 0,  true);          // flags
    dv.setUint16( 8, 0,  true);          // method: stored
    dv.setUint16(10, 0,  true);          // mod time
    dv.setUint16(12, 0,  true);          // mod date
    dv.setUint32(14, crc,  true);        // CRC-32
    dv.setUint32(18, size, true);        // compressed size
    dv.setUint32(22, size, true);        // uncompressed size
    dv.setUint16(26, nameBuf.length, true);
    dv.setUint16(28, 0, true);           // extra field length
    header.set(nameBuf, 30);

    localParts.push({ header, data: dataBuf, nameBuf, crc, size, offset });
    offset += header.length + size;
  }

  // Central directory
  const cdParts = [];
  for (const p of localParts) {
    const cd  = new Uint8Array(46 + p.nameBuf.length);
    const dv  = new DataView(cd.buffer);
    dv.setUint32( 0, 0x02014b50, true); // central dir sig
    dv.setUint16( 4, 20, true);          // version made by
    dv.setUint16( 6, 20, true);          // version needed
    dv.setUint16( 8, 0,  true);          // flags
    dv.setUint16(10, 0,  true);          // method: stored
    dv.setUint16(12, 0,  true);          // mod time
    dv.setUint16(14, 0,  true);          // mod date
    dv.setUint32(16, p.crc,  true);
    dv.setUint32(20, p.size, true);
    dv.setUint32(24, p.size, true);
    dv.setUint16(28, p.nameBuf.length, true);
    dv.setUint16(30, 0, true); // extra
    dv.setUint16(32, 0, true); // comment
    dv.setUint16(34, 0, true); // disk start
    dv.setUint16(36, 0, true); // internal attr
    dv.setUint32(38, 0, true); // external attr
    dv.setUint32(42, p.offset, true); // local header offset
    cd.set(p.nameBuf, 46);
    cdParts.push(cd);
  }

  const cdSize   = cdParts.reduce((s, c) => s + c.length, 0);
  const cdOffset = offset;
  const eocd     = new Uint8Array(22);
  const edv      = new DataView(eocd.buffer);
  edv.setUint32( 0, 0x06054b50, true); // end of central dir sig
  edv.setUint16( 4, 0, true);           // disk number
  edv.setUint16( 6, 0, true);           // disk with start
  edv.setUint16( 8, localParts.length, true);
  edv.setUint16(10, localParts.length, true);
  edv.setUint32(12, cdSize,   true);
  edv.setUint32(16, cdOffset, true);
  edv.setUint16(20, 0, true);           // comment length

  // Assemble
  const parts = [];
  for (const p of localParts) { parts.push(p.header); parts.push(p.data); }
  for (const c of cdParts)    { parts.push(c); }
  parts.push(eocd);

  const total = parts.reduce((s, p) => s + p.length, 0);
  const out   = new Uint8Array(total);
  let   pos   = 0;
  for (const p of parts) { out.set(p, pos); pos += p.length; }
  return out;
}

// CRC-32 implementation (IEEE 802.3 polynomial)
const _CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[i] = c;
  }
  return t;
})();

function _pkgCrc32(buf) {
  let crc = 0xFFFFFFFF;
  for (const byte of buf) crc = _CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

// ── OTS submit job handler ────────────────────────────────────────────────────

if (typeof registerJobHandler === 'function') {
  registerJobHandler('ots.submit', {
    estimateFn: () => 3000,
    runFn: async (job) => {
      const { sessionId, hash } = JSON.parse(job.payload);
      const hashBytes = fromB64(hash);

      let receipt = null, calendar = null;
      for (const cal of _PKG_OTS_CALENDARS) {
        try {
          const r = await fetch(cal + '/digest', {
            method:  'POST',
            headers: { 'Content-Type': 'application/octet-stream',
                       Accept: 'application/octet-stream' },
            body: hashBytes,
          });
          if (!r.ok) continue;
          receipt = new Uint8Array(await r.arrayBuffer());
          calendar = cal;
          break;
        } catch (_) {}
      }

      if (!receipt) throw new Error('All OTS calendar servers unreachable');
      return {
        sessionId,
        otsReceipt:  toB64(receipt),
        otsCalendar: calendar,
        otsSubmitted: new Date().toISOString(),
      };
    },
  });

  registerJobHandler('package.build', {
    estimateFn: () => 1500,
    runFn: async (job) => {
      const { sessionId } = JSON.parse(job.payload);
      const { manifest } = await buildPackage(sessionId);
      return { sessionId, manifestId: manifest['@id'] };
    },
  });
}

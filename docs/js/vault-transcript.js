'use strict';

// ── Event Log & Transcript Engine (VC-13) ─────────────────────────────────────
// Captures call events with a SHA-256 hash chain into IDB wf-events.
// Generates HTML+RDFa transcripts; supports annotation and Ed25519 revision signing.
//
// Depends on: vault-idb.js (_ST_EVENTS, _dbPut, _dbGetAll),
//             vault-crypto.js (toB64),
//             vault-scheduler.js (registerJobHandler, enqueueJob, JOB_TRIGGER)
//
// Public API:
//   captureEvent(sessionId, type, actorDid, payload) → event record
//   generateTranscript(sessionId)  → HTML string
//   annotateTranscript(sessionId)  → HTML string (with resource= attrs for known terms)
//   saveRevision(sessionId, deltaText, correctedByDid, privateKey) → revision record

// ── SHA-256 hex helper ────────────────────────────────────────────────────────

async function _txSha256(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// ── Dedup guard — prevents redundant transcript.generate jobs per session ──────

const _txPendingJobs = new Set(); // sessionIds with an already-queued generate job

// ── HTML escape ───────────────────────────────────────────────────────────────

function _txEsc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ── Public API ─────────────────────────────────────────────────────────────────

// Append an event to the wf-events hash chain for a session.
// Automatically enqueues a transcript.generate job (once per session).
async function captureEvent(sessionId, type, actorDid, payload) {
  const all     = await _dbGetAll(_ST_EVENTS);
  const session = all.filter(e => e.sessionId === sessionId && e.seq >= 0)
                     .sort((a, b) => a.seq - b.seq);
  const seq      = session.length;
  const prevHash = seq > 0 ? session[seq - 1].hash : '0'.repeat(64);

  const ts        = new Date().toISOString();
  const hashInput = JSON.stringify({ seq, type, actorDid, ts, payload }) + prevHash;
  const hash      = await _txSha256(hashInput);

  const record = {
    id: 'ev-' + crypto.randomUUID(),
    sessionId,
    seq,
    type,
    actorDid,
    ts,
    payload,
    hash,
    prevHash,
  };
  await _dbPut(_ST_EVENTS, record);

  // Enqueue transcript.generate once per active session
  if (!_txPendingJobs.has(sessionId) && typeof enqueueJob === 'function') {
    _txPendingJobs.add(sessionId);
    await enqueueJob(
      'transcript.generate',
      { sessionId },
      JOB_TRIGGER.ALWAYS,
      3
    );
  }

  return record;
}

// Generate an HTML+RDFa transcript for a session.
// Called by the scheduler job handler and also directly by the UI.
async function generateTranscript(sessionId) {
  const all    = await _dbGetAll(_ST_EVENTS);
  const events = all.filter(e => e.sessionId === sessionId)
                    .sort((a, b) => a.seq - b.seq);
  _txPendingJobs.delete(sessionId); // allow re-queuing after generation
  return _txBuildHtml(sessionId, events, []);
}

// Annotate an existing transcript with resource= attributes for known medication
// and substance terms (sourced from SUBSTANCE_INTERACTIONS in vault-meds-lod.js).
async function annotateTranscript(sessionId) {
  const all    = await _dbGetAll(_ST_EVENTS);
  const events = all.filter(e => e.sessionId === sessionId)
                    .sort((a, b) => a.seq - b.seq);

  const knownTerms = typeof SUBSTANCE_INTERACTIONS !== 'undefined'
    ? SUBSTANCE_INTERACTIONS.map(si => si.substance) : [];

  return _txBuildHtml(sessionId, events, knownTerms);
}

// Sign a revision delta with Ed25519 and store it in wf-events.
// privateKey must be an Ed25519 CryptoKey with sign usage.
async function saveRevision(sessionId, deltaText, correctedByDid, privateKey) {
  const ts     = new Date().toISOString();
  const sigBuf = await crypto.subtle.sign(
    'Ed25519', privateKey, new TextEncoder().encode(deltaText)
  );
  const sig = toB64(new Uint8Array(sigBuf));

  const revHash = await _txSha256(deltaText + sig + ts);
  const record  = {
    id:             'rev-' + crypto.randomUUID(),
    sessionId,
    seq:            -1, // revisions are not in the primary hash chain
    type:           'revision',
    actorDid:       correctedByDid,
    ts,
    payload:        { deltaText, sig },
    hash:           revHash,
    prevHash:       '',
  };
  await _dbPut(_ST_EVENTS, record);
  return record;
}

// ── HTML+RDFa builder ─────────────────────────────────────────────────────────

function _txBuildHtml(sessionId, events, knownTerms) {
  const chainEvents     = events.filter(e => e.seq >= 0);
  const revisions       = events.filter(e => e.type === 'revision');
  const speechEvents    = chainEvents.filter(e => e.type === 'speech.segment');
  const dataEvents      = chainEvents.filter(e => e.type.startsWith('data.'));
  const telemetryEvents = chainEvents.filter(e => e.type === 'agent.telemetry');
  const callEvents      = chainEvents.filter(e =>
    !e.type.startsWith('data.') && e.type !== 'speech.segment' && e.type !== 'agent.telemetry'
  );

  // Biometric telemetry log rows (WA-7)
  const telemetryRows = telemetryEvents.map(ev => {
    const p = ev.payload || {};
    const v = p.vision     || {};
    const b = p.biometrics || {};
    const a = p.audio      || {};
    const l = p.linguistic || {};

    const bpm  = b.bpm != null
      ? Math.round(b.bpm) + ' BPM' + (b.signalQuality ? ' (' + b.signalQuality + ')' : '')
      : '—';
    const expr = v.emotion
      ? _txEsc(v.emotion) + (v.confidence != null ? ' (' + Math.round(v.confidence * 100) + '%)' : '')
      : '—';
    const vocal = a.pitchHz != null ? 'pitch: ' + Math.round(a.pitchHz) + ' Hz' : '—';
    const lang  = l.sentimentScore != null
      ? 'sentiment: ' + l.sentimentScore.toFixed(1) +
        ', pronoun: ' + Math.round((l.pronounRatio1P || 0) * 100) + '%'
      : '—';
    const mods = (p.modules || []).join(', ') || '—';

    return `
    <tr property="wf:hasTelemetrySample" typeof="wf:TelemetrySample"
        data-seq="${ev.seq}" data-hash="${_txEsc(ev.hash)}">
      <td><time property="dcterms:date" datetime="${_txEsc(ev.ts)}">${_txEsc(ev.ts.slice(11, 19))}</time></td>
      <td property="wf:bpm">${_txEsc(bpm)}</td>
      <td property="wf:primaryExpression">${expr}</td>
      <td>${_txEsc(vocal)}</td>
      <td>${_txEsc(lang)}</td>
      <td class="tel-mods">${_txEsc(mods)}</td>
    </tr>`;
  }).join('\n');

  const callSegs = callEvents.map(ev => `
    <div class="segment" property="wf:hasSegment" typeof="wf:EventSegment"
         data-seq="${ev.seq}" data-hash="${_txEsc(ev.hash)}">
      <div class="actor">${_txEsc(ev.actorDid || '')}</div>
      <strong property="wf:eventType">${_txEsc(ev.type)}</strong>
      <time property="dcterms:date" datetime="${_txEsc(ev.ts)}"> ${_txEsc(ev.ts)}</time>
      ${ev.payload && ev.payload.text
        ? `<p property="wf:text">${_txAnnotateText(_txEsc(ev.payload.text), knownTerms)}</p>`
        : ''}
      <div class="meta">hash: ${_txEsc(ev.hash.slice(0, 16))}…</div>
    </div>`).join('\n');

  const speechSegs = speechEvents.map(ev => `
    <div class="segment speech" property="wf:hasSegment" typeof="wf:SpeechSegment"
         data-seq="${ev.seq}" data-hash="${_txEsc(ev.hash)}">
      <div class="actor">${_txEsc(ev.actorDid || '')}</div>
      <time property="dcterms:date" datetime="${_txEsc(ev.ts)}"> ${_txEsc(ev.ts)}</time>
      <p property="wf:original">
        ${_txAnnotateText(_txEsc(ev.payload?.original || ''), knownTerms)}
      </p>
      ${ev.payload?.translated ? `
        <p property="wf:translated" lang="${_txEsc(ev.payload.targetLang || '')}">
          ${_txEsc(ev.payload.translated)}
        </p>` : ''}
      ${ev.payload?.serviceUsed ? `
        <span property="wf:languageService" typeof="wf:LanguageService">
          <span property="wf:provider">${_txEsc(ev.payload.serviceUsed)}</span>
        </span>` : ''}
    </div>`).join('\n');

  // Ambiguity log: speech segments without translation
  const ambiguities = speechEvents
    .filter(ev => ev.payload?.original && !ev.payload?.translated)
    .map(ev => `
    <div class="ambiguity" property="wf:hasAmbiguity" typeof="wf:Ambiguity"
         data-seq="${ev.seq}">
      <span property="wf:text">${_txEsc(ev.payload.original)}</span>
      <span property="wf:reason"> — No translation available</span>
    </div>`).join('\n');

  // Data sharing log
  const dataLog = dataEvents.map(ev => `
    <div class="data-ev" property="wf:hasDataEvent" typeof="wf:DataSharingEvent"
         data-seq="${ev.seq}" data-hash="${_txEsc(ev.hash)}">
      <strong property="wf:eventType">${_txEsc(ev.type)}</strong>
      <time property="dcterms:date" datetime="${_txEsc(ev.ts)}"> ${_txEsc(ev.ts)}</time>
      ${ev.payload?.sections
        ? `<span property="wf:sections">${_txEsc(JSON.stringify(ev.payload.sections))}</span>`
        : ''}
    </div>`).join('\n');

  // Revision history
  const revLog = revisions.map(ev => `
    <div class="revision" property="wf:hasRevision" typeof="wf:Revision"
         data-hash="${_txEsc(ev.hash)}">
      <time property="dcterms:date" datetime="${_txEsc(ev.ts)}"> ${_txEsc(ev.ts)}</time>
      <span property="wf:correctedBy" content="${_txEsc(ev.actorDid)}"></span>
      <div class="actor">By: ${_txEsc(ev.actorDid || '')}</div>
      <p property="wf:delta">${_txEsc(ev.payload?.deltaText || '')}</p>
      <div class="meta sig">Sig: ${_txEsc((ev.payload?.sig || '').slice(0, 24))}…</div>
    </div>`).join('\n');

  return `<!DOCTYPE html>
<html lang="en"
      prefix="wf: https://wellfare.social/ns/vault#
              dcterms: http://purl.org/dc/terms/">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>WellFair Transcript — ${_txEsc(sessionId.slice(0, 8))}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto;
           padding: 0 1rem; color: #111; background: #fafafa; }
    h2   { border-bottom: 2px solid #4a90d9; padding-bottom: .4rem; color: #222; }
    h3   { margin-top: 2rem; color: #555; font-size: .92rem;
           text-transform: uppercase; letter-spacing: .05em; }
    time { color: #888; font-size: .78rem; }
    p    { margin: .25rem 0; }
    .segment { border-left: 3px solid #4a90d9; padding: .4rem .75rem;
               margin: .5rem 0; background: #f8faff; border-radius: 0 4px 4px 0; }
    .speech  { border-color: #47a878; background: #f5fff9; }
    .data-ev { border-color: #d97a4a; background: #fff8f5; }
    .ambiguity { border-color: #c5a800; background: #fffcee;
                 padding: .3rem .75rem; margin: .4rem 0; border-radius: 0 4px 4px 0; }
    .revision { border-color: #9b59b6; background: #fdf5ff;
                padding: .4rem .75rem; margin: .5rem 0; border-radius: 0 4px 4px 0; }
    .actor { font-size: .7rem; color: #888; font-family: monospace; margin-bottom: .15rem; }
    .meta  { font-size: .68rem; color: #bbb; margin-top: .2rem; }
    .sig   { word-break: break-all; }
    a[resource] { text-decoration: none; border-bottom: 1px dashed #888; cursor: help; }
    section { margin-bottom: 1.5rem; }
    .tel-table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    .tel-table th { text-align: left; padding: .3rem .5rem; border-bottom: 2px solid #ddd;
                    font-size: .73rem; text-transform: uppercase; letter-spacing: .04em; color: #666; }
    .tel-table td { padding: .25rem .5rem; border-bottom: 1px solid #eee; }
    .tel-table tbody { max-height: 280px; overflow-y: auto; display: block; }
    .tel-table thead, .tel-table tbody tr { display: table; width: 100%; table-layout: fixed; }
    .tel-mods { font-size: .68rem; color: #aaa; }
    .notice { font-size: .78rem; color: #888; font-style: italic; margin-bottom: .65rem; }
  </style>
</head>
<body vocab="https://wellfare.social/ns/vault#"
      typeof="wf:CommunicationTranscript"
      resource="urn:uuid:${_txEsc(sessionId)}">

  <h2>WellFair Communication Transcript</h2>
  <p>Session: <code property="dcterms:identifier"
     content="urn:uuid:${_txEsc(sessionId)}">${_txEsc(sessionId)}</code></p>
  <p class="meta">Generated: ${new Date().toISOString()}</p>

  ${callSegs || speechSegs ? `
  <h3>Communication log</h3>
  <section id="event-log">
    ${callSegs}
    ${speechSegs}
  </section>` : '<p><em>No events captured for this session.</em></p>'}

  ${ambiguities ? `
  <h3>Ambiguity log</h3>
  <section id="ambiguity-log" typeof="wf:AmbiguityLog" property="wf:hasAmbiguityLog">
    ${ambiguities}
  </section>` : ''}

  ${revLog ? `
  <h3>Revision history</h3>
  <section id="revision-history" typeof="wf:RevisionHistory" property="wf:hasRevisionHistory">
    ${revLog}
  </section>` : ''}

  ${dataLog ? `
  <h3>Data sharing log</h3>
  <section id="data-sharing-log" typeof="wf:DataSharingLog" property="wf:hasDataSharingLog">
    ${dataLog}
  </section>` : ''}

  ${telemetryRows ? `
  <h3>Biometric indicators log</h3>
  <section id="telemetry-log" typeof="wf:BiometricTelemetryLog" property="wf:hasTelemetryLog">
    <p class="notice">Indicators generated locally on patient device.
       No raw video, audio, or transcript data was collected.</p>
    <table class="tel-table">
      <thead>
        <tr><th>Time</th><th>Heart rate</th><th>Expression</th>
            <th>Vocal</th><th>Language</th><th>Modules</th></tr>
      </thead>
      <tbody>${telemetryRows}</tbody>
    </table>
  </section>` : ''}

</body>
</html>`;
}

// ── Text annotation ───────────────────────────────────────────────────────────

function _txAnnotateText(text, knownTerms) {
  if (!knownTerms || !knownTerms.length) return text;
  let out = text;
  for (const term of knownTerms) {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`\\b(${escaped})\\b`, 'gi');
    out = out.replace(re,
      `<a resource="wf:term:${encodeURIComponent(term)}" title="${_txEsc(term)}">$1</a>`);
  }
  return out;
}

// ── Register job handlers with the scheduler ──────────────────────────────────

if (typeof registerJobHandler === 'function') {
  registerJobHandler('transcript.generate', {
    estimateFn: () => 600,
    runFn: async (job) => {
      const { sessionId } = JSON.parse(job.payload);
      const html = await generateTranscript(sessionId);
      return { sessionId, html };
    },
  });

  registerJobHandler('transcript.annotate', {
    estimateFn: () => 900,
    runFn: async (job) => {
      const { sessionId } = JSON.parse(job.payload);
      const html = await annotateTranscript(sessionId);
      return { sessionId, html };
    },
  });
}

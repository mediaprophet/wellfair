'use strict';

// ── Pharmacological LOD lookup + drug interaction engine ─────────────────────
// Depends on: vault-idb.js, vault-meds-reminders.js (_getActiveMeds)

const RXNORM_BASE = 'https://rxnav.nlm.nih.gov/REST';
const WD_SPARQL   = 'https://query.wikidata.org/sparql';

// Curated drug-substance interaction rules (food, alcohol, nicotine, caffeine)
const SUBSTANCE_INTERACTIONS = [
  { pattern: /atorvastatin|simvastatin|lovastatin|rosuvastatin|pravastatin|fluvastatin|statin/i,
    substance: 'grapefruit', category: 'food', severity: 'moderate',
    detail: 'Grapefruit inhibits CYP3A4 — raises statin plasma levels, increasing myopathy risk.' },
  { pattern: /warfarin|coumadin/i,
    substance: 'alcohol', category: 'alcohol', severity: 'severe',
    detail: 'Alcohol unpredictably alters anticoagulant effect — increases bleeding or clot risk.' },
  { pattern: /metformin/i,
    substance: 'alcohol', category: 'alcohol', severity: 'moderate',
    detail: 'Alcohol increases risk of lactic acidosis with metformin.' },
  { pattern: /phenelzine|tranylcypromine|selegiline|moclobemide|isocarboxazid/i,
    substance: 'tyramine-rich foods', category: 'food', severity: 'severe',
    detail: 'Aged cheese, red wine, cured meats — can cause hypertensive crisis with MAOIs.' },
  { pattern: /sertraline|fluoxetine|citalopram|escitalopram|paroxetine|venlafaxine|duloxetine|fluvoxamine/i,
    substance: 'alcohol', category: 'alcohol', severity: 'moderate',
    detail: 'Alcohol potentiates CNS depression and may worsen depression and anxiety.' },
  { pattern: /diazepam|lorazepam|alprazolam|clonazepam|temazepam|nitrazepam|oxazepam|midazolam/i,
    substance: 'alcohol', category: 'alcohol', severity: 'severe',
    detail: 'Additive CNS and respiratory depression — risk of loss of consciousness.' },
  { pattern: /codeine|morphine|oxycodone|tramadol|fentanyl|hydrocodone|buprenorphine|methadone/i,
    substance: 'alcohol', category: 'alcohol', severity: 'severe',
    detail: 'Combined CNS and respiratory depression — potentially fatal.' },
  { pattern: /codeine|morphine|oxycodone|tramadol|fentanyl|hydrocodone|buprenorphine/i,
    substance: 'nicotine / vaping', category: 'nicotine', severity: 'mild',
    detail: 'Smoking may mildly reduce opioid efficacy via CYP induction.' },
  { pattern: /theophylline|clozapine|olanzapine|haloperidol/i,
    substance: 'nicotine / vaping', category: 'nicotine', severity: 'moderate',
    detail: 'Smoking reduces plasma levels via CYP1A2 induction — dose may need adjustment on quitting.' },
  { pattern: /methylphenidate|amphetamine|lisdexamfetamine|dexamfetamine/i,
    substance: 'caffeine / energy drinks', category: 'caffeine', severity: 'moderate',
    detail: 'Additive CNS stimulation — increased heart rate, anxiety, and insomnia risk.' },
  { pattern: /theophylline/i,
    substance: 'caffeine / energy drinks', category: 'caffeine', severity: 'moderate',
    detail: 'Caffeine has similar bronchodilatory action — combined use raises side-effect burden.' },
  { pattern: /lithium/i,
    substance: 'caffeine / energy drinks', category: 'caffeine', severity: 'moderate',
    detail: 'Caffeine increases renal lithium excretion — abrupt change can destabilise lithium levels.' },
  { pattern: /levothyroxine|thyroxine/i,
    substance: 'caffeine / energy drinks', category: 'caffeine', severity: 'mild',
    detail: 'Coffee may reduce levothyroxine absorption — take 30+ minutes before coffee.' },
  { pattern: /doxycycline|tetracycline|minocycline/i,
    substance: 'dairy / calcium', category: 'food', severity: 'moderate',
    detail: 'Calcium chelates tetracyclines, markedly reducing absorption — take 2 hours apart.' },
  { pattern: /ciprofloxacin|norfloxacin|levofloxacin/i,
    substance: 'dairy / calcium', category: 'food', severity: 'moderate',
    detail: 'Calcium reduces fluoroquinolone absorption — take 2 hours apart from dairy or antacids.' },
  { pattern: /sildenafil|tadalafil|vardenafil/i,
    substance: 'alcohol', category: 'alcohol', severity: 'moderate',
    detail: 'Both cause vasodilation — combined use raises hypotension and dizziness risk.' },
  { pattern: /aspirin|ibuprofen|naproxen|diclofenac/i,
    substance: 'alcohol', category: 'alcohol', severity: 'moderate',
    detail: 'NSAIDs combined with alcohol significantly increase gastrointestinal bleeding risk.' },
  { pattern: /isotretinoin|acitretin/i,
    substance: 'alcohol', category: 'alcohol', severity: 'severe',
    detail: 'Alcohol combined with retinoids raises risk of severe liver toxicity.' },
];

// ── LOD name autocomplete ─────────────────────────────────────────────────────

let _lodSearchTimer = null;

async function _medNameInput(ev) {
  const query = ev.target.value.trim();
  clearTimeout(_lodSearchTimer);
  const suggestions = document.getElementById('med-name-suggestions');
  if (!suggestions) return;
  if (query.length < 3) { suggestions.style.display = 'none'; return; }
  _lodSearchTimer = setTimeout(() => _lodSearch(query), 420);
}

async function _lodSearch(query) {
  const suggestions = document.getElementById('med-name-suggestions');
  if (!suggestions) return;
  try {
    const res     = await fetch(`${RXNORM_BASE}/drugs.json?name=${encodeURIComponent(query)}`);
    const data    = await res.json();
    const results = [];
    for (const g of (data.drugGroup?.conceptGroup || [])) {
      if (g.conceptProperties) {
        for (const p of g.conceptProperties) {
          if (['IN','BN','PIN','MIN'].includes(p.tty))
            results.push({ name: p.name, rxcui: p.rxcui, tty: p.tty });
        }
      }
    }
    if (!results.length) { suggestions.style.display = 'none'; return; }
    const _ttyLabel = { IN: 'generic', BN: 'brand', PIN: 'precise', MIN: 'multi-ingredient' };
    suggestions.innerHTML = results.slice(0, 8).map(r =>
      `<div class="med-autocomplete-item" onmousedown="event.preventDefault()"
            onclick="_lodSelectDrug('${r.rxcui}','${r.name.replace(/'/g,"\\'")}')">
        <span style="font-size:.8rem;font-weight:600">${r.name}</span>
        <span style="font-size:.69rem;color:var(--dim);margin-left:.35rem">${_ttyLabel[r.tty] || r.tty}</span>
      </div>`).join('');
    suggestions.style.display = 'block';
  } catch (_) { suggestions.style.display = 'none'; }
}

async function _lodSelectDrug(rxcui, name) {
  const nameInput   = document.getElementById('med-add-name');
  const suggestions = document.getElementById('med-name-suggestions');
  const lodInfo     = document.getElementById('med-lod-info');
  if (nameInput)   nameInput.value = name;
  if (suggestions) suggestions.style.display = 'none';
  if (nameInput) { nameInput.dataset.rxcui = rxcui; nameInput.dataset.atcCode = ''; nameInput.dataset.linkedDataUri = ''; }
  if (lodInfo)   { lodInfo.textContent = 'Fetching pharmacological data…'; lodInfo.style.display = 'block'; }
  const detail = await _lodFetchDetail(rxcui, name);
  if (detail) {
    if (nameInput) { nameInput.dataset.atcCode = detail.atcCode || ''; nameInput.dataset.linkedDataUri = detail.linkedDataUri || ''; }
    if (lodInfo) {
      const parts = [];
      if (detail.atcCode)       parts.push(`ATC: ${detail.atcCode}`);
      if (detail.linkedDataUri) parts.push(`<a href="${detail.linkedDataUri}" target="_blank" rel="noopener" style="color:var(--accent)">Wikidata ↗</a>`);
      lodInfo.innerHTML = parts.length ? parts.join(' · ') : 'No linked data found';
    }
  } else {
    if (lodInfo) lodInfo.textContent = 'Pharmacological data unavailable';
  }
}

async function _lodFetchDetail(rxcui, name) {
  const cacheKey = 'rx-' + rxcui;
  try {
    const cached = await _dbGet(_ST_PHARMA, cacheKey);
    if (cached && (Date.now() - new Date(cached.fetchedAt).getTime()) < 7 * 24 * 3600 * 1000) return cached;
  } catch (_) {}
  const detail = { id: cacheKey, rxcui, name, atcCode: null, linkedDataUri: null, fetchedAt: new Date().toISOString() };
  try {
    const r    = await fetch(`${RXNORM_BASE}/rxcui/${rxcui}/allrelated.json`);
    const data = await r.json();
    const atcGroup = (data.allRelatedGroup?.conceptGroup || []).find(g => g.tty === 'ATC');
    if (atcGroup?.conceptProperties?.[0]) detail.atcCode = atcGroup.conceptProperties[0].name;
  } catch (_) {}
  try {
    const q = rxcui
      ? `SELECT ?d WHERE { ?d wdt:P3780 "${rxcui}" } LIMIT 1`
      : `SELECT ?d WHERE { ?d wdt:P31/wdt:P279* wd:Q12140 ; rdfs:label "${name}"@en } LIMIT 1`;
    const r    = await fetch(`${WD_SPARQL}?query=${encodeURIComponent(q)}&format=json`,
                   { headers: { Accept: 'application/sparql-results+json' } });
    const data = await r.json();
    const uri  = data.results?.bindings?.[0]?.d?.value;
    if (uri) detail.linkedDataUri = uri;
  } catch (_) {}
  try { await _dbPut(_ST_PHARMA, detail); } catch (_) {}
  return detail;
}

// ── Drug interaction engine ───────────────────────────────────────────────────

async function _runInteractionCheck() {
  const meds   = await _getActiveMeds();
  const alerts = [];
  for (const med of meds) {
    const testStr = (med.name || '') + ' ' + (med.genericName || '');
    for (const rule of SUBSTANCE_INTERACTIONS) {
      if (rule.pattern.test(testStr))
        alerts.push({ type: 'substance', drugA: med.name, substanceB: rule.substance,
          severity: rule.severity, category: rule.category, detail: rule.detail, source: 'curated' });
    }
  }
  const rxcuis = meds.map(m => m.rxcui).filter(Boolean);
  if (rxcuis.length >= 2) {
    try {
      const r    = await fetch(`${RXNORM_BASE}/interaction/list.json?rxcuis=${rxcuis.join('+')}`);
      const data = await r.json();
      for (const g of (data.fullInteractionTypeGroup || [])) {
        for (const t of (g.fullInteractionType || [])) {
          for (const p of (t.interactionPair || [])) {
            const concepts = p.interactionConcept || [];
            const sev = (p.severity || '').toLowerCase();
            alerts.push({ type: 'drug-drug',
              drugA:      concepts[0]?.minConceptItem?.name || '',
              substanceB: concepts[1]?.minConceptItem?.name || '',
              severity: sev === 'high' ? 'severe' : sev === 'low' ? 'mild' : 'moderate',
              detail: p.description || '', source: 'rxnorm', category: 'drug-drug' });
          }
        }
      }
    } catch (_) {}
  }
  return alerts;
}

async function _refreshInteractionPanel() {
  const list  = document.getElementById('interaction-list');
  if (!list) return;
  const alerts = await _runInteractionCheck();
  const badge  = document.getElementById('interaction-badge');
  const btn    = document.getElementById('interaction-panel-btn');
  if (!alerts.length) {
    list.innerHTML = '<p style="font-size:.78rem;color:var(--green);padding:.3rem 0">No known interactions for your current medications.</p>';
    if (badge) { badge.textContent = ''; badge.className = 'med-badge'; }
    if (btn) btn.style.color = '';
    return;
  }
  const order = { severe: 0, moderate: 1, mild: 2 };
  alerts.sort((a, b) => (order[a.severity] ?? 1) - (order[b.severity] ?? 1));
  const severeCount = alerts.filter(a => a.severity === 'severe').length;
  const modCount    = alerts.filter(a => a.severity === 'moderate').length;
  if (badge) {
    badge.textContent = severeCount ? `${severeCount} severe` : `${modCount} moderate`;
    badge.className   = 'med-badge ' + (severeCount ? 'overdue' : 'due');
  }
  if (btn) btn.style.color = severeCount ? 'var(--red)' : 'var(--yellow)';
  if (severeCount) {
    const body = document.getElementById('interaction-body');
    const chev = document.getElementById('interaction-chevron');
    if (body && body.style.display === 'none') { body.style.display = 'block'; if (chev) chev.textContent = '▾'; }
  }
  const _catIcon = { food: '🍽', alcohol: '🍺', nicotine: '🚬', caffeine: '☕', 'drug-drug': '💊' };
  list.innerHTML = alerts.map(a => {
    const sevColor = a.severity === 'severe' ? 'var(--red)' : a.severity === 'moderate' ? 'var(--yellow)' : 'var(--dim)';
    const icon     = _catIcon[a.type === 'drug-drug' ? 'drug-drug' : (a.category || 'food')] || '⚠';
    return `<div class="interaction-alert ${a.severity}">
      <div style="display:flex;align-items:baseline;gap:.35rem;margin-bottom:.2rem;flex-wrap:wrap">
        <span>${icon}</span>
        <span style="font-size:.8rem;font-weight:600">${a.drugA}</span>
        <span style="font-size:.72rem;color:var(--dim)">+</span>
        <span style="font-size:.8rem;font-weight:600">${a.substanceB}</span>
        <span style="font-size:.69rem;font-weight:700;color:${sevColor};margin-left:auto;text-transform:uppercase">${a.severity}</span>
      </div>
      <div style="font-size:.74rem;color:var(--dim);line-height:1.45">${a.detail}</div>
      ${a.source==='rxnorm'?'<div style="font-size:.67rem;color:var(--border);margin-top:.18rem">Source: RxNorm</div>':''}
    </div>`;
  }).join('');
}

function toggleInteractionPanel() {
  const body    = document.getElementById('interaction-body');
  const chevron = document.getElementById('interaction-chevron');
  if (!body) return;
  const open = body.style.display !== 'none';
  body.style.display = open ? 'none' : 'block';
  if (chevron) chevron.textContent = open ? '▸' : '▾';
}

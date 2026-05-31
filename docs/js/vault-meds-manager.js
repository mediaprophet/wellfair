'use strict';

// ── Medication manager — add / cease sheet ────────────────────────────────────
// Depends on: vault-idb.js, vault-mock.js, vault-meds-reminders.js

async function openMedManager() {
  document.getElementById('med-manager-sheet').style.display = 'flex';
  document.getElementById('med-add-start').value = new Date().toISOString().slice(0, 10);
  _updateScheduleInputs();
  await _refreshMedManagerList();
}

function closeMedManager() {
  document.getElementById('med-manager-sheet').style.display = 'none';
}

function _updateScheduleInputs() {
  const freq      = document.getElementById('med-add-freq')?.value;
  const container = document.getElementById('med-schedule-times');
  if (!container) return;
  const defaults = {
    once_daily:  ['08:00'],
    twice_daily: ['08:00', '20:00'],
    three_daily: ['08:00', '13:00', '20:00'],
    four_daily:  ['08:00', '12:00', '16:00', '20:00'],
    weekly:      ['08:00'],
    as_needed:   [],
  };
  const times = defaults[freq] || [];
  if (!times.length) { container.innerHTML = ''; return; }
  container.innerHTML = `<p style="font-size:.73rem;color:var(--dim);margin-bottom:.3rem">Reminder times:</p>` +
    times.map((t, i) => `<label class="med-form-label" style="margin-bottom:.25rem">
      <span style="display:inline">Dose ${i + 1}</span>
      <input type="time" class="med-time-input med-input" value="${t}" style="width:auto;margin-left:.4rem" />
    </label>`).join('');
}

async function saveMedication() {
  const name       = document.getElementById('med-add-name')?.value.trim();
  const dose       = document.getElementById('med-add-dose')?.value.trim();
  const unit       = document.getElementById('med-add-unit')?.value;
  const route      = document.getElementById('med-add-route')?.value;
  const freq       = document.getElementById('med-add-freq')?.value;
  const indication = document.getElementById('med-add-indication')?.value.trim();
  const prescriber = document.getElementById('med-add-prescriber')?.value.trim();
  const startDate  = document.getElementById('med-add-start')?.value;
  if (!name || !dose) {
    document.getElementById('med-save-status').textContent = 'Drug name and dose are required.';
    document.getElementById('med-save-status').style.color = 'var(--red)'; return;
  }
  const timeInputs    = document.querySelectorAll('.med-time-input');
  const scheduleTimes = [...timeInputs].map(i => i.value).filter(Boolean);
  const nameEl        = document.getElementById('med-add-name');
  await _dbPut(_ST_MEDS, {
    id: 'med-' + Date.now(), name, genericName: name,
    rxcui:         nameEl?.dataset?.rxcui         || null,
    atcCode:       nameEl?.dataset?.atcCode       || null,
    linkedDataUri: nameEl?.dataset?.linkedDataUri || null,
    dose, unit, route, frequency: freq, scheduleTimes,
    indication: indication || null, prescriber: prescriber || null,
    startDate: startDate || new Date().toISOString().slice(0, 10),
    endDate: null, status: 'active', addedAt: new Date().toISOString()
  });
  ['med-add-name','med-add-dose','med-add-indication','med-add-prescriber'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  document.getElementById('med-add-start').value = new Date().toISOString().slice(0, 10);
  document.getElementById('med-save-status').textContent = '✓ Medication saved';
  document.getElementById('med-save-status').style.color = 'var(--green)';
  setTimeout(() => { const el = document.getElementById('med-save-status'); if (el) el.textContent = ''; }, 3000);
  await _refreshMedManagerList();
  await _refreshMedPanel();
}

async function ceaseMedication(medId) {
  if (!confirm('Mark this medication as ceased?')) return;
  const rec    = await _dbGet(_ST_MEDS, medId);
  const source = rec || VAULT.medications().items.find(m => m.id === medId);
  if (!source) return;
  await _dbPut(_ST_MEDS, { ...source, status: 'ceased', endDate: new Date().toISOString().slice(0, 10) });
  await _refreshMedManagerList();
  await _refreshMedPanel();
}

function _medListItemHtml(med) {
  const schedLabel = med.scheduleTimes?.length ? med.scheduleTimes.join(' & ') : 'PRN';
  const doseStr    = `${med.dose || ''}${med.unit || ''} · ${schedLabel}`;
  const ceased     = med.status === 'ceased';
  return `<div class="med-list-item${ceased ? ' ceased' : ''}">
    <div>
      <div style="font-size:.82rem;font-weight:600">${med.name}</div>
      <div class="med-list-meta">${doseStr}${med.indication ? ' · ' + med.indication : ''}</div>
      ${med.linkedDataUri ? `<a href="${med.linkedDataUri}" target="_blank" rel="noopener" style="font-size:.69rem;color:var(--accent)">Wikidata ↗</a>` : ''}
    </div>
    ${!ceased ? `<button class="btn-skip" onclick="ceaseMedication('${med.id}')">Cease</button>` : ''}
  </div>`;
}

async function _refreshMedManagerList() {
  const container = document.getElementById('med-manager-list');
  if (!container) return;
  const meds   = await _getAllMeds();
  const active = meds.filter(m => m.status === 'active' || !m.status);
  const ceased = meds.filter(m => m.status === 'ceased');
  container.innerHTML =
    `<p class="med-section-label">Active (${active.length})</p>` +
    (active.length ? active.map(_medListItemHtml).join('') : '<p style="font-size:.78rem;color:var(--dim)">None</p>') +
    (ceased.length ? `<p class="med-section-label">Ceased (${ceased.length})</p>` + ceased.map(_medListItemHtml).join('') : '');
}

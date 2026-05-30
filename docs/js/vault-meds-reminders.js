'use strict';

// ── Medication reminders — schedule, take/skip, today panel ──────────────────
// Depends on: vault-idb.js, vault-mock.js

const MedNotifier = {
  _handlers: [],
  register(handler) { this._handlers.push(handler); },
  async dispatch(event) {
    for (const h of this._handlers) { try { await h(event); } catch (_) {} }
  }
};

// Built-in handler: badge refresh + Web Notifications
MedNotifier.register(async (ev) => {
  _refreshMedBadge();
  if (ev.type === 'overdue' && Notification.permission === 'granted') {
    new Notification(`Medication overdue — ${ev.medication.name}`, {
      body: `${ev.medication.dose}${ev.medication.unit} was scheduled at ${ev.scheduledTime}`,
      tag: 'med-' + ev.medication.id, renotify: false,
    });
  }
});
// Future: MedNotifier.register(bleWatchHandler);
// Future: MedNotifier.register(wsWatchConnectorHandler);

let _medCheckInterval = null;

async function _getActiveMeds() {
  try {
    const idbMeds = await _dbGetAll(_ST_MEDS);
    if (idbMeds.length) return idbMeds.filter(m => m.status === 'active');
  } catch (_) {}
  return VAULT.medications().items.filter(m => m.status === 'active');
}

async function _getAllMeds() {
  try {
    const idbMeds = await _dbGetAll(_ST_MEDS);
    if (idbMeds.length) return idbMeds;
  } catch (_) {}
  return VAULT.medications().items;
}

async function _getTodayLogEntries() {
  try {
    const all   = await _dbGetAll(_ST_MED_LOG);
    const today = new Date().toISOString().slice(0, 10);
    return all.filter(e => e.scheduledTime && e.scheduledTime.startsWith(today));
  } catch (_) { return []; }
}

async function _buildTodaySchedule() {
  const meds  = await _getActiveMeds();
  const log   = await _getTodayLogEntries();
  const now   = new Date();
  const today = now.toISOString().slice(0, 10);
  const schedule = [];
  for (const med of meds) {
    if (!med.scheduleTimes?.length) {
      schedule.push({ medication: med, scheduledTime: null, status: 'prn', logEntry: null });
      continue;
    }
    for (const t of med.scheduleTimes) {
      const scheduledTime = `${today}T${t}:00`;
      const logEntry = log.find(e => e.medId === med.id && e.scheduledTime === scheduledTime) || null;
      let status = 'upcoming';
      if (logEntry) {
        status = logEntry.adherenceStatus;
      } else {
        const schDt = new Date(scheduledTime);
        if (schDt < now) status = 'overdue';
        else if ((schDt - now) < 30 * 60 * 1000) status = 'due';
      }
      schedule.push({ medication: med, scheduledTime, status, logEntry });
    }
  }
  return schedule.sort((a, b) => {
    if (!a.scheduledTime) return 1;
    if (!b.scheduledTime) return -1;
    return a.scheduledTime.localeCompare(b.scheduledTime);
  });
}

async function logMedTaken(medId, scheduledTime) {
  const takenTime = new Date().toISOString();
  await _dbPut(_ST_MED_LOG, {
    id: 'ml-' + medId + '-' + Date.now(), medId,
    scheduledTime: scheduledTime || takenTime, takenTime,
    adherenceStatus: 'taken', notes: ''
  });
  await _refreshMedPanel();
}

async function logMedSkipped(medId, scheduledTime, reason) {
  await _dbPut(_ST_MED_LOG, {
    id: 'ml-skip-' + medId + '-' + Date.now(), medId,
    scheduledTime: scheduledTime || new Date().toISOString(),
    takenTime: null, adherenceStatus: 'skipped', notes: reason || ''
  });
  await _refreshMedPanel();
}

function _promptSkip(medId, scheduledTime) {
  const reason = prompt('Reason for skipping (optional):', '');
  if (reason !== null) logMedSkipped(medId, scheduledTime, reason);
}

function _refreshMedBadge() {
  _buildTodaySchedule().then(schedule => {
    const overdue = schedule.filter(s => s.status === 'overdue').length;
    const due     = schedule.filter(s => s.status === 'due').length;
    const badge   = document.getElementById('med-panel-badge');
    const btn     = document.getElementById('med-panel-btn');
    if (!badge) return;
    if (overdue) {
      badge.textContent = overdue + ' overdue'; badge.className = 'med-badge overdue';
      if (btn) btn.style.color = 'var(--red)';
    } else if (due) {
      badge.textContent = due + ' due now'; badge.className = 'med-badge due';
      if (btn) btn.style.color = 'var(--yellow)';
    } else {
      badge.textContent = ''; badge.className = 'med-badge';
      if (btn) btn.style.color = '';
    }
  });
}

async function _refreshMedPanel() {
  const list = document.getElementById('med-dose-list');
  if (!list) return;
  const schedule = await _buildTodaySchedule();
  if (!schedule.length) {
    list.innerHTML = '<p style="font-size:.78rem;color:var(--dim);text-align:center;padding:.6rem 0">No medications scheduled</p>';
    _refreshMedBadge(); return;
  }
  list.innerHTML = schedule.map(item => {
    const med       = item.medication;
    const doseLabel = `${med.dose || ''}${med.unit || ''}`;
    const timeLabel = item.scheduledTime ? item.scheduledTime.slice(11, 16) : 'As needed';
    let statusHtml = '', rowClass = 'med-dose-row';
    if (item.status === 'taken') {
      rowClass += ' taken';
      const takenAt = item.logEntry?.takenTime?.slice(11, 16) || '';
      statusHtml = `<span class="med-status ok">✓ Taken ${takenAt}</span>`;
    } else if (item.status === 'skipped') {
      rowClass += ' taken';
      statusHtml = `<span class="med-status" style="color:var(--dim)">Skipped</span>`;
    } else if (item.status === 'overdue') {
      rowClass += ' overdue';
      statusHtml = `<button class="btn-take" onclick="logMedTaken('${med.id}','${item.scheduledTime}')">Take now</button>
        <button class="btn-skip" onclick="_promptSkip('${med.id}','${item.scheduledTime}')">Skip</button>`;
    } else if (item.status === 'due') {
      statusHtml = `<button class="btn-take" onclick="logMedTaken('${med.id}','${item.scheduledTime}')">Take</button>`;
    } else if (item.status === 'upcoming') {
      statusHtml = `<button class="btn-take" style="opacity:.5" onclick="logMedTaken('${med.id}','${item.scheduledTime}')">Take</button>`;
    } else if (item.status === 'prn') {
      statusHtml = `<button class="btn-take" onclick="logMedTaken('${med.id}',null)">Log dose</button>`;
    }
    return `<div class="${rowClass}">
      <div class="med-info">
        <span class="med-name">${med.name}</span>
        <span class="med-detail">${doseLabel} · ${timeLabel}</span>
        ${med.indication ? `<span class="med-indication">${med.indication}</span>` : ''}
      </div>
      <div class="med-actions">${statusHtml}</div>
    </div>`;
  }).join('');
  _refreshMedBadge();
  for (const item of schedule) {
    if (item.status === 'overdue') {
      const minLate = Math.floor((Date.now() - new Date(item.scheduledTime)) / 60000);
      MedNotifier.dispatch({ type: 'overdue', medication: item.medication,
        scheduledTime: item.scheduledTime.slice(11, 16), minutesLate: minLate });
    }
  }
}

function toggleMedPanel() {
  const body    = document.getElementById('med-today-body');
  const chevron = document.getElementById('med-panel-chevron');
  if (!body) return;
  const open = body.style.display !== 'none';
  body.style.display = open ? 'none' : 'block';
  if (chevron) chevron.textContent = open ? '▸' : '▾';
}

async function initMedReminders() {
  await _refreshMedPanel();
  _refreshInteractionPanel(); // fire-and-forget
  if (_medCheckInterval) clearInterval(_medCheckInterval);
  _medCheckInterval = setInterval(_refreshMedPanel, 5 * 60 * 1000);
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

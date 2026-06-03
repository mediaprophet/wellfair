'use strict';

// ── Personal Calendar + Boundary Protection (PIA6) ────────────────────────────
// Stores personal appointments, family events, health needs, and rest periods
// in wf-calendar (IDB v12).  Provides boundary-conflict detection so that
// project obligations cannot silently override personal time.
//
// Depends on: vault-idb.js (_ST_CALENDAR, _ST_EVENTS, _dbPut, _dbGet,
//             _dbGetAll, _dbDelete), vault-crypto.js (_sEnc, _sDec)
//
// Module init: call initCalendar(aesKey) when vault unlocks.

let _calKey = null;

// Vault-wide "Personal Priority" flag — when true, project notifications and
// obligation scheduling are suspended.  Persisted in vault config (wf-sc) but
// managed here for convenience.
let _personalPriorityActive = false;

// ── Init ──────────────────────────────────────────────────────────────────────

function initCalendar(aesKey) {
  _calKey = aesKey;
}

function _requireKey() {
  if (!_calKey) throw new Error('[Calendar] Key not set — call initCalendar() after vault unlocks');
}

// ── Encryption helpers ────────────────────────────────────────────────────────

async function _encRecord(plain) {
  const { iv, ct } = await _sEnc(_calKey, plain);
  return { id: plain.id, startIso: plain.startIso, iv, ct };
}

async function _decRecord(stored) {
  return _sDec(_calKey, { iv: stored.iv, ct: stored.ct });
}

// ── Calendar CRUD ─────────────────────────────────────────────────────────────

// Add a personal event. type: 'appointment' | 'family' | 'health' | 'rest' | 'other'
async function addCalendarEvent(title, startIso, endIso, type, personalPriority) {
  _requireKey();
  const record = {
    id:              crypto.randomUUID(),
    title:           title || 'Untitled',
    startIso:        startIso,
    endIso:          endIso,
    type:            type || 'other',
    personalPriority: personalPriority !== false, // default true
    createdAt:       new Date().toISOString(),
  };
  await _dbPut(_ST_CALENDAR, await _encRecord(record));
  return record;
}

async function getCalendarEvent(id) {
  _requireKey();
  const stored = await _dbGet(_ST_CALENDAR, id);
  return stored ? _decRecord(stored) : null;
}

async function getAllCalendarEvents() {
  _requireKey();
  const all = await _dbGetAll(_ST_CALENDAR);
  return Promise.all(all.map(r => _decRecord(r)));
}

async function deleteCalendarEvent(id) {
  _requireKey();
  await _dbDelete(_ST_CALENDAR, id);
}

// ── Boundary conflict detection ───────────────────────────────────────────────

// Returns an array of personal-priority events that overlap [startIso, endIso].
// Overlap condition: event.start < windowEnd && event.end > windowStart
async function checkBoundaryConflict(startIso, endIso) {
  _requireKey();
  const events = await getAllCalendarEvents();
  const windowStart = new Date(startIso).getTime();
  const windowEnd   = new Date(endIso).getTime();
  return events.filter(ev => {
    if (!ev.personalPriority) return false;
    const evStart = new Date(ev.startIso).getTime();
    const evEnd   = new Date(ev.endIso).getTime();
    return evStart < windowEnd && evEnd > windowStart;
  });
}

// Log a boundary conflict event to wf-events IDB (accountability log).
// Called when: (a) a project tries to schedule work during personal time,
// OR (b) the user explicitly opts in after seeing a conflict (with overriddenByUser=true).
async function logBoundaryConflict(conflictWindow, overriddenBy, overriddenByUser) {
  try {
    await _dbPut(_ST_EVENTS, {
      id:                crypto.randomUUID(),
      type:              'wf:ProtocolEvent',
      protocolEventType: 'qp_boundary_conflict',
      conflictWindow,
      overriddenBy:      overriddenBy || null,
      overriddenByUser:  !!overriddenByUser,
      timestamp:         new Date().toISOString(),
      piaEvent:          true,
    });
  } catch (e) {
    console.warn('[PIA6] logBoundaryConflict failed:', e.message);
  }
}

// ── Personal Priority mode ────────────────────────────────────────────────────

function setPersonalPriority(active) {
  _personalPriorityActive = !!active;
}

function isPersonalPriorityActive() {
  return _personalPriorityActive;
}

// CBOR5 — CBOR-LD export: encode all personal calendar events into QualiaStore.
// Requires initCalendar(aesKey) to have been called.
// Returns total count of quints inserted.
async function exportCalendarToCborLdQuins() {
  if (!window.vaultCborLd || !window.vaultWasm?.getQualiaStore()) return 0;
  let count = 0;
  try {
    const events = await getAllCalendarEvents();
    for (const ev of events) {
      count += await window.vaultCborLd.insertRecordToQualiaStore(_ST_CALENDAR, ev);
    }
  } catch (e) {
    console.warn('[CBOR5/cal] exportCalendarToCborLdQuins failed:', e.message);
  }
  return count;
}

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultCalendar = {
  initCalendar,
  addCalendarEvent, getCalendarEvent, getAllCalendarEvents, deleteCalendarEvent,
  checkBoundaryConflict,
  logBoundaryConflict,
  setPersonalPriority, isPersonalPriorityActive,
  exportCalendarToCborLdQuins,
};

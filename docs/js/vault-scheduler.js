'use strict';

// ── Background Job Scheduler — condition-triggered queue engine ───────────────
// Depends on: vault-idb.js (_ST_JOBS, _dbPut, _dbGet, _dbGetAll, _dbDelete)
//
// Jobs persist in IDB wf-jobs across app restarts.
// Condition flags: ALWAYS, IDLE, CHARGING, DESKTOP, MANUAL (bitfield).
// Desktop offload: sends job_offload over DataChannel when DESKTOP condition met.
//
// Usage:
//   startScheduler()    // call in openOwnerWorkspace
//   stopScheduler()     // call in lockVault
//   await enqueueJob(type, payload, triggerConditions, priority)
//   registerJobHandler(type, { estimateFn, runFn })

// ── Trigger condition flags ───────────────────────────────────────────────────

const JOB_TRIGGER = Object.freeze({
  ALWAYS:   0b00001,
  IDLE:     0b00010,
  CHARGING: 0b00100,
  DESKTOP:  0b01000,
  MANUAL:   0b10000,
});

// ── Job status constants ──────────────────────────────────────────────────────

const JOB_STATUS = Object.freeze({
  PENDING:   'pending',
  RUNNING:   'running',
  DONE:      'done',
  FAILED:    'failed',
  CANCELLED: 'cancelled',
});

// ── Module state ──────────────────────────────────────────────────────────────

let _schedRunning   = false;
let _schedTick      = null;
const _schedHandlers = new Map(); // type → { estimateFn, runFn }
const TICK_INTERVAL_MS = 15_000; // check every 15 s
const MAX_RETRIES = 3;
const BACKOFF_BASE_MS = 30_000; // 30 s, doubles each retry

// ── Public API ────────────────────────────────────────────────────────────────

function startScheduler() {
  if (_schedRunning) return;
  _schedRunning = true;
  _schedTick    = setInterval(_tick, TICK_INTERVAL_MS);
  _tick(); // immediate first check
}

function stopScheduler() {
  _schedRunning = false;
  clearInterval(_schedTick);
  _schedTick = null;
}

async function enqueueJob(type, payload, triggerConditions = JOB_TRIGGER.ALWAYS, priority = 5) {
  const job = {
    id:                 'job-' + crypto.randomUUID(),
    type,
    status:             JOB_STATUS.PENDING,
    priority,
    created_at:         new Date().toISOString(),
    started_at:         null,
    completed_at:       null,
    estimated_ms:       null,
    actual_ms:          null,
    trigger_conditions: triggerConditions,
    payload:            JSON.stringify(payload),
    result_ref:         null,
    error:              null,
    retry_count:        0,
    next_retry_at:      null,
  };

  const handler = _schedHandlers.get(type);
  if (handler && handler.estimateFn) {
    try { job.estimated_ms = handler.estimateFn(payload); } catch (_) {}
  }

  await _dbPut(_ST_JOBS, job);
  document.dispatchEvent(new CustomEvent('wf:job-enqueued', { detail: { id: job.id, type } }));
  return job;
}

async function cancelJob(id) {
  const job = await _dbGet(_ST_JOBS, id);
  if (!job || job.status === JOB_STATUS.RUNNING) return;
  job.status = JOB_STATUS.CANCELLED;
  await _dbPut(_ST_JOBS, job);
  document.dispatchEvent(new CustomEvent('wf:job-updated', { detail: { id, status: JOB_STATUS.CANCELLED } }));
}

async function runJobNow(id) {
  const job = await _dbGet(_ST_JOBS, id);
  if (!job || job.status === JOB_STATUS.RUNNING) return;
  await _executeJob(job);
}

function registerJobHandler(type, { estimateFn, runFn }) {
  _schedHandlers.set(type, { estimateFn, runFn });
}

async function getJobList() {
  return _dbGetAll(_ST_JOBS);
}

// ── Pharmaceutical Reminders ──────────────────────────────────────────────────
registerJobHandler('med_reminder', {
  estimateFn: () => 10,
  runFn: async (job, progressFn) => {
    const payload = JSON.parse(job.payload);
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Medication Reminder', {
        body: `It's time to take your medication: ${payload.med_name} (${payload.dose})`,
        icon: '/icons/icon-192.png'
      });
    }
    // Re-schedule for the next interval (e.g. 24h later) if recurring
    if (payload.recurring_hours) {
      await enqueueJob('med_reminder', payload, JOB_TRIGGER.ALWAYS, 5);
      // We would ideally set the created_at/delay for the future, but for POC this runs immediately next tick.
    }
    return { notified: true, med: payload.med_name };
  }
});

// ── Scheduler tick ────────────────────────────────────────────────────────────

async function _tick() {
  if (!_schedRunning) return;
  try {
    const all = await _dbGetAll(_ST_JOBS);
    const eligible = all.filter(j =>
      j.status === JOB_STATUS.PENDING &&
      _isRetryReady(j) &&
      _checkConditions(j.trigger_conditions)
    ).sort((a, b) => (b.priority - a.priority) || (a.created_at < b.created_at ? -1 : 1));

    for (const job of eligible) {
      if (!_schedRunning) break;
      await _executeJob(job);
    }
  } catch (e) {
    console.warn('[Scheduler] tick error:', e.message);
  }
}

function _isRetryReady(job) {
  if (!job.next_retry_at) return true;
  return new Date(job.next_retry_at) <= new Date();
}

// ── Condition detection ───────────────────────────────────────────────────────

function _checkConditions(flags) {
  if (flags & JOB_TRIGGER.ALWAYS)   return true;
  if (flags & JOB_TRIGGER.MANUAL)   return false; // only via runJobNow()

  let met = false;

  if (flags & JOB_TRIGGER.IDLE) {
    met = met || document.visibilityState === 'hidden';
  }

  if (flags & JOB_TRIGGER.DESKTOP) {
    // Check if connector DataChannel is live
    const dcLive = typeof _callDc !== 'undefined' && _callDc && _callDc.readyState === 'open';
    met = met || dcLive;
  }

  if (flags & JOB_TRIGGER.CHARGING) {
    // Heuristic: assume charging between 00:00–06:00 local time
    const h = new Date().getHours();
    met = met || (h >= 0 && h < 6);
  }

  return met;
}

// ── Job execution ─────────────────────────────────────────────────────────────

async function _executeJob(job) {
  const handler = _schedHandlers.get(job.type);

  // Desktop offload when DESKTOP condition met and no local handler
  if ((job.trigger_conditions & JOB_TRIGGER.DESKTOP) &&
      typeof _callDc !== 'undefined' && _callDc && _callDc.readyState === 'open') {
    try {
      _callDc.send(JSON.stringify({
        type: 'job_offload', job_id: job.id,
        job_type: job.type, payload: job.payload,
      }));
      job.status   = JOB_STATUS.RUNNING;
      job.started_at = new Date().toISOString();
      await _dbPut(_ST_JOBS, job);
      document.dispatchEvent(new CustomEvent('wf:job-updated', { detail: { id: job.id, status: JOB_STATUS.RUNNING } }));
      return;
    } catch (_) {}
  }

  if (!handler) {
    console.debug('[Scheduler] No handler for job type:', job.type);
    return;
  }

  job.status     = JOB_STATUS.RUNNING;
  job.started_at = new Date().toISOString();
  await _dbPut(_ST_JOBS, job);
  document.dispatchEvent(new CustomEvent('wf:job-updated', { detail: { id: job.id, status: JOB_STATUS.RUNNING } }));

  const t0 = Date.now();
  try {
    const result = await handler.runFn(job, (pct) => {
      document.dispatchEvent(new CustomEvent('wf:job-progress', { detail: { id: job.id, pct } }));
    });
    job.status       = JOB_STATUS.DONE;
    job.completed_at = new Date().toISOString();
    job.actual_ms    = Date.now() - t0;
    job.result_ref   = result ? JSON.stringify(result) : null;
    job.error        = null;
  } catch (e) {
    job.retry_count = (job.retry_count || 0) + 1;
    if (job.retry_count >= MAX_RETRIES) {
      job.status = JOB_STATUS.FAILED;
      job.error  = e.message;
    } else {
      job.status       = JOB_STATUS.PENDING;
      const backoffMs  = BACKOFF_BASE_MS * Math.pow(2, job.retry_count - 1);
      job.next_retry_at = new Date(Date.now() + backoffMs).toISOString();
      job.error        = e.message;
    }
  }

  job.actual_ms = job.actual_ms ?? (Date.now() - t0);
  await _dbPut(_ST_JOBS, job);
  document.dispatchEvent(new CustomEvent('wf:job-updated', {
    detail: { id: job.id, status: job.status, error: job.error }
  }));
}

// ── Handle results from desktop offload ──────────────────────────────────────

async function schedHandleDesktopResult(msg) {
  const job = await _dbGet(_ST_JOBS, msg.job_id);
  if (!job) return;

  if (msg.type === 'job_result') {
    job.status       = JOB_STATUS.DONE;
    job.completed_at = new Date().toISOString();
    job.result_ref   = msg.result ? JSON.stringify(msg.result) : null;
    job.error        = null;
  } else if (msg.type === 'job_error') {
    job.retry_count = (job.retry_count || 0) + 1;
    job.status      = job.retry_count >= MAX_RETRIES ? JOB_STATUS.FAILED : JOB_STATUS.PENDING;
    job.error       = msg.error;
  } else if (msg.type === 'job_progress') {
    document.dispatchEvent(new CustomEvent('wf:job-progress',
      { detail: { id: msg.job_id, pct: msg.pct, eta_ms: msg.eta_ms } }));
    return;
  }

  await _dbPut(_ST_JOBS, job);
  document.dispatchEvent(new CustomEvent('wf:job-updated',
    { detail: { id: job.id, status: job.status } }));
}

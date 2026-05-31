'use strict';

// ── Call Profiles — per-contact data-sharing presets for video calls ──────────
// Each profile defines which vault sections are surfaced (highlighted) in the
// call overlay Info panel when a call is active with that contact.
//
// The vault owner is always in control — these are suggestions, not restrictions.
// "Generic call" is the safe default: no health data is offered until the owner
// assigns a profile to a contact.
//
// callProfileId is stored on the contact record in IDB (wf-contacts).
// Resolved at call-start by _callOverlayPopulateInfo() in vault.html.

const CALL_PROFILES = [
  {
    id:          'generic_call',
    label:       'General call',
    description: 'Standard video or audio call. No health data is offered to share by default.',
    icon:        '📞',
    color:       '#6c757d',
    sections:    [],
  },
  {
    id:          'health_consultation',
    label:       'Health consultation',
    description: 'GP, nurse, or primary care provider. Overview, current medications, conditions, and vitals.',
    icon:        '🩺',
    color:       '#0d6efd',
    sections:    [
      'overview', 'heart_rate', 'blood_pressure', 'weight',
      'medications', 'medication_adherence', 'medication_interactions',
      'allergies', 'conditions',
    ],
  },
  {
    id:          'mental_health_call',
    label:       'Mental health session',
    description: 'Psychologist, counsellor, or mental health support worker. Mental health records and sleep patterns.',
    icon:        '🧠',
    color:       '#6f42c1',
    sections:    [
      'overview', 'mental_health', 'sleep',
      'medications', 'medication_adherence',
    ],
  },
  {
    id:          'social_work_call',
    label:       'Social work check-in',
    description: 'Social worker, case manager, or community support worker. Social and housing context, emergency contacts.',
    icon:        '🤝',
    color:       '#198754',
    sections:    [
      'overview', 'social_context', 'emergency_contacts',
    ],
  },
  {
    id:          'specialist_call',
    label:       'Specialist consultation',
    description: 'Hospital specialist (cardiologist, oncologist, etc.). Full clinical picture including procedures and interactions.',
    icon:        '🔬',
    color:       '#6610f2',
    sections:    [
      'overview', 'heart_rate', 'blood_pressure',
      'medications', 'medication_history', 'medication_interactions',
      'allergies', 'conditions', 'surgical_history',
    ],
  },
  {
    id:          'carer_call',
    label:       'Carer / family call',
    description: 'Trusted carer or family member who helps manage your care day-to-day.',
    icon:        '🏠',
    color:       '#fd7e14',
    sections:    [
      'overview', 'medications', 'conditions',
      'allergies', 'emergency_contacts',
    ],
  },
  {
    id:          'legal_call',
    label:       'Legal consultation',
    description: 'Legal representative, advocate, or solicitor. Nothing is offered by default — you choose what to share.',
    icon:        '⚖️',
    color:       '#6c757d',
    sections:    [],
  },
  {
    id:          'crisis_support_call',
    label:       'Crisis support',
    description: 'Crisis support worker (e.g. Beyond Blue, Lifeline, domestic violence service). Social context and emergency contacts.',
    icon:        '🆘',
    color:       '#dc3545',
    sections:    [
      'social_context', 'emergency_contacts', 'mental_health',
    ],
  },
];

// ── Public API ────────────────────────────────────────────────────────────────

function getAllCallProfiles() {
  return CALL_PROFILES;
}

// Returns the profile object for the given id; falls back to generic_call.
function getCallProfile(id) {
  return CALL_PROFILES.find(p => p.id === id) ?? CALL_PROFILES[0];
}

// Returns the sections array for the given profile id.
function getCallProfileSections(id) {
  return getCallProfile(id).sections;
}

// Build an <option> list for a <select> element.
// selectedId defaults to 'generic_call'.
function callProfileSelectOptions(selectedId) {
  return CALL_PROFILES.map(p =>
    `<option value="${p.id}"${p.id === selectedId ? ' selected' : ''}>${p.icon} ${p.label}</option>`
  ).join('');
}

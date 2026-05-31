'use strict';

// ── Mock vault data ───────────────────────────────────────────────────────────
// Returned by handleDesktopMessage in webconnect.html.
// Also used as IDB fallback in vault-meds.js when no meds have been added yet.

const VAULT = {
  overview:          () => ({ metrics: {
    heart_rate:  { value: 68,   unit: 'bpm',   status: 'normal' },
    steps_today: { value: 4231, unit: 'steps', status: 'below_goal' },
    sleep_last:  { value: 6.5,  unit: 'hrs',   status: 'borderline' },
    weight:      { value: 72.4, unit: 'kg',    status: 'stable' }
  }, alerts: [] }),

  heart_rate:        () => ({
    latest: 68, avg_7d: 71, min_7d: 55, max_7d: 112, unit: 'bpm', trend: 'stable',
    readings: [{time:'06:00',value:62},{time:'09:00',value:78},{time:'12:00',value:71},
               {time:'15:00',value:68},{time:'18:00',value:74},{time:'21:00',value:65}]
  }),

  blood_pressure:    () => ({
    latest: '118/76', systolic_avg: 121, diastolic_avg: 78, unit: 'mmHg', trend: 'stable',
    readings: [{date:'Mon',s:120,d:78},{date:'Tue',s:118,d:76},{date:'Wed',s:124,d:80},
               {date:'Thu',s:119,d:77},{date:'Fri',s:122,d:79}]
  }),

  sleep:             () => ({
    last_night_h: 6.5, avg_7d_h: 6.8, quality: 'moderate',
    log: [{date:'Mon',hours:7.2,quality:'good'},{date:'Tue',hours:5.9,quality:'poor'},
          {date:'Wed',hours:7.0,quality:'good'},{date:'Thu',hours:6.1,quality:'moderate'},
          {date:'Fri',hours:8.1,quality:'good'},{date:'Sat',hours:6.5,quality:'moderate'},
          {date:'Sun',hours:6.5,quality:'moderate'}]
  }),

  steps:             () => ({
    today: 4231, avg_7d: 6840, goal: 8000,
    log: [{date:'Mon',steps:7240},{date:'Tue',steps:5910},{date:'Wed',steps:8102},
          {date:'Thu',steps:6140},{date:'Fri',steps:7900},{date:'Sat',steps:5200},
          {date:'Sun',steps:4231}]
  }),

  weight:            () => ({
    latest_kg: 72.4, trend: 'stable ↔',
    log: [{date:'21 May',kg:72.8},{date:'23 May',kg:72.6},
          {date:'25 May',kg:72.5},{date:'27 May',kg:72.4},{date:'29 May',kg:72.4}]
  }),

  medications:       () => ({
    items: [
      { id: 'med-001', name: 'Lisinopril', genericName: 'Lisinopril',
        rxcui: '29046', atcCode: 'C09AA03',
        linkedDataUri: 'http://www.wikidata.org/entity/Q422068',
        dose: '10', unit: 'mg', route: 'oral',
        frequency: 'once_daily', scheduleTimes: ['08:00'],
        indication: 'Blood pressure', prescriber: 'Dr Sarah Chen',
        startDate: '2019-01-15', endDate: null, status: 'active' },
      { id: 'med-002', name: 'Metformin', genericName: 'Metformin hydrochloride',
        rxcui: '860975', atcCode: 'A10BA02',
        linkedDataUri: 'http://www.wikidata.org/entity/Q190814',
        dose: '500', unit: 'mg', route: 'oral',
        frequency: 'twice_daily', scheduleTimes: ['08:00', '20:00'],
        indication: 'Blood glucose', prescriber: 'Dr Sarah Chen',
        startDate: '2021-06-03', endDate: null, status: 'active' },
      { id: 'med-003', name: 'Vitamin D3', genericName: 'Colecalciferol',
        rxcui: '2200687', atcCode: 'A11CC05',
        linkedDataUri: 'http://www.wikidata.org/entity/Q185833',
        dose: '1000', unit: 'IU', route: 'oral',
        frequency: 'once_daily', scheduleTimes: ['08:00'],
        indication: 'Supplement', prescriber: null,
        startDate: '2023-01-01', endDate: null, status: 'active' }
    ]
  }),

  allergies:         () => ({ items: [
    { substance: 'Penicillin',  reaction: 'Anaphylaxis',      severity: 'severe' },
    { substance: 'Latex',       reaction: 'Contact urticaria', severity: 'moderate' },
    { substance: 'Ibuprofen',   reaction: 'GI bleeding',       severity: 'moderate' }
  ]}),

  conditions:        () => ({ items: [
    { name: 'Hypertension',    diagnosed: '2019', status: 'managed' },
    { name: 'Type 2 Diabetes', diagnosed: '2021', status: 'managed' },
    { name: 'Mild asthma',     diagnosed: '2005', status: 'intermittent' }
  ]}),

  blood_type:        () => ({ type: 'A+', rh_factor: 'positive', confirmed: '2018-03-12' }),

  dnr:               () => ({
    dnr_in_place: false, advance_directive: true,
    directive_summary: 'No mechanical ventilation if brain-dead. Organ donation consented.',
    document_location: 'On file with GP — Dr Sarah Chen, Southwark Health Centre',
    last_reviewed: '2024-11-01'
  }),

  emergency_contacts: () => ({ contacts: [
    { name: 'Alex Rivera',   relation: 'Partner', phone: '+44 7700 900123', notify_first: true },
    { name: 'Maria Torres',  relation: 'Sister',  phone: '+44 7700 900456' },
    { name: 'Dr Sarah Chen', relation: 'GP',      phone: '+44 20 7946 0321' }
  ]}),

  surgical_history:  () => ({
    procedures: [
      { procedure: 'Appendectomy',     date: '2003-07', hospital: 'Kings College Hospital' },
      { procedure: 'Knee arthroscopy', date: '2017-03', hospital: 'St Thomas Hospital' }
    ],
    implants: [], blood_transfusions: false
  }),

  mental_health:     () => ({
    current_diagnoses: [{ name: 'Generalised Anxiety Disorder', status: 'managed', since: '2020' }],
    current_support: 'CBT — 6-weekly sessions',
    crisis_plan_in_place: true,
    crisis_contact: 'Mind Helpline 0300 123 3393'
  }),

  sexual_health:     () => ({
    last_sti_screen: '2025-02-14', sti_screen_result: 'negative',
    screen_provider: 'SH:24 (postal kit)', conditions: [],
    note: 'All clear as of last screen. Next screen due approx. Aug 2025.'
  }),

  social_context:    () => ({
    housing_status:    'Stable — private rented, 1-bed flat',
    employment_status: 'Self-employed, variable income',
    support_network:   'Partner, 1 sibling nearby, active GP',
    current_stressors: ['Financial pressure', 'Caring responsibilities'],
    safeguarding_flags: []
  })
};

const SECTION_LABELS = {
  overview:                  'Overview & summary',
  heart_rate:                'Heart rate',
  blood_pressure:            'Blood pressure',
  sleep:                     'Sleep',
  steps:                     'Activity & steps',
  weight:                    'Weight',
  medications:               'Current medications',
  medication_adherence:      'Medication adherence log',
  medication_history:        'Ceased / historical medications',
  medication_interactions:   'Drug interaction alerts',
  allergies:                 'Allergies',
  conditions:                'Medical conditions',
  blood_type:                'Blood type',
  dnr:                       'DNR / advance directive',
  emergency_contacts:        'Emergency contacts',
  surgical_history:          'Surgical history',
  mental_health:             'Mental health',
  sexual_health:             'Sexual health',
  social_context:            'Social context',
  documents:                 'Documents',
  notes:                     'Notes',
};

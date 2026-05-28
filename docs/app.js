import init, * as wasm from './pkg/wellfare_core.js';
import Chart from 'https://cdn.jsdelivr.net/npm/chart.js@4.4.5/+esm';
import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs';

const STATE = {
  charts: new Map(),
  pyodide: null,
  currentProfile: null,
};

const DEMO_PROFILES = [
  {
    id: 'synthetic',
    label: 'Gemini demo (synthetic)',
    persona: 'Baseline synthetic participant',
    description: 'Balanced activity and sleep patterns used for regression testing.',
    tags: ['reference', 'balanced'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'michael',
    label: 'Michael R. — displaced tradesperson',
    persona: 'Rough sleeping, separated father managing diabetes',
    description: 'Highly irregular sleep, elevated stress markers, erratic activity when casual work appears.',
    tags: ['housing crisis', 'diabetes', 'family separation'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'elena',
    label: 'Elena V. — trauma recovery',
    persona: 'Former sex worker exiting violence with complex PTSD',
    description: 'Fragmented sleep, panic-driven heart rate spikes, swing between sedentary and hyper-active days.',
    tags: ['complex trauma', 'PTSD', 'housing instability'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'rebecca',
    label: 'Rebecca L. — riverbank autonomy',
    persona: 'Long-term tent living, deep institutional mistrust',
    description: 'Persistent hypervigilance, low restorative sleep, survival-based step patterns.',
    tags: ['rough sleeping', 'autonomy', 'long-term trauma'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'margaret',
    label: 'Margaret T. — elder abuse survivor',
    persona: '78-year-old widow facing coercive control from family',
    description: 'Sedentary trend with anxiety-related sleep disruption and creeping biometric decline.',
    tags: ['elder abuse', 'hypertension', 'isolation'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'robert',
    label: 'Robert K. — cardiac neglect',
    persona: '82-year-old experiencing medical coercion by spouse',
    description: 'Dangerous cardiac variability with declining mobility and medication manipulation signals.',
    tags: ['elder abuse', 'cardiac risk'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
  {
    id: 'jordan',
    label: 'Jordan M. — NDIS exploitation',
    persona: 'Non-binary person with ABI and chronic pain trapped in provider fraud',
    description: 'Low mobility, chronic pain sleep fragmentation, stress spikes tied to abusive service encounters.',
    tags: ['disability', 'systemic abuse', 'NDIS'],
    files: {
      steps: 'sample_data/synthetic_steps.csv',
      sleep: 'sample_data/synthetic_sleep.csv',
      weight: 'sample_data/synthetic_weight.csv',
      heart_rate: 'sample_data/synthetic_hr.csv',
    },
  },
];

// DOM references -----------------------------------------------------------
const navButtons = document.querySelectorAll('.nav-button');
const views = document.querySelectorAll('.view');
const kpiGrid = document.getElementById('kpiGrid');
const chartsGrid = document.getElementById('chartsGrid');
const insightsList = document.getElementById('insightsList');
const timelineList = document.getElementById('timelineList');
const profileSelect = document.getElementById('profileSelect');
const demoStatus = document.getElementById('demoStatus');
const profileSummary = document.getElementById('profileSummary');
const wasmStatus = document.getElementById('wasmStatus');
const outputEl = document.getElementById('output');
const parseBtn = document.getElementById('parseBtn');
const fileInput = document.getElementById('fileInput');
const csvType = document.getElementById('csvType');
const copyBtn = document.getElementById('copyBtn');

function renderProfileSummary(profile) {
  if (!profileSummary || !profile) return;
  const tags = (profile.tags || [])
    .map((tag) => `<span class="tag">${tag}</span>`)
    .join('');
  profileSummary.innerHTML = `
    <div class="profile-card">
      <div>
        <h2>${profile.label}</h2>
        <p class="persona">${profile.persona}</p>
        <p>${profile.description}</p>
      </div>
      <div class="tag-list" aria-label="Profile context tags">${tags}</div>
    </div>
  `;
}

// View switching -----------------------------------------------------------
function activateView(targetId) {
  views.forEach((view) => {
    view.classList.toggle('active', view.id === targetId);
  });
  navButtons.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === targetId.replace('View', ''));
  });
}

navButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.view;
    activateView(`${target}View`);
  });
});

// WASM initialisation -----------------------------------------------------
async function loadWasm() {
  try {
    await init();
    wasmStatus.textContent = 'WASM ready';
    wasmStatus.classList.remove('subtle');
  } catch (e) {
    console.error('WASM load failed', e);
    outputEl.textContent = 'WASM load failed: ' + e;
    wasmStatus.textContent = 'WASM failed';
    wasmStatus.classList.add('error');
  }
}

// Pyodide initialisation --------------------------------------------------
async function fetchProfileCsv(profileId) {
  const profile = DEMO_PROFILES.find((item) => item.id === profileId);
  if (!profile) {
    throw new Error(`Unknown profile ${profileId}`);
  }
  const entries = await Promise.all(
    Object.entries(profile.files).map(async ([key, path]) => {
      const res = await fetch(path);
      if (!res.ok) {
        throw new Error(`Failed to load ${path}`);
      }
      return [key, await res.text()];
    })
  );
  return Object.fromEntries(entries);
}

function resetCharts() {
  STATE.charts.forEach((chart) => chart.destroy());
  STATE.charts.clear();
}

function renderKpis(kpis) {
  kpiGrid.innerHTML = '';
  kpis.forEach((kpi) => {
    const card = document.createElement('article');
    card.className = 'kpi-card';
    card.innerHTML = `
      <div class="kpi-icon" style="background:${kpi.accent}22;color:${kpi.accent};">${kpi.icon}</div>
      <div class="kpi-title">${kpi.label}</div>
      <div class="kpi-primary">${kpi.primary}</div>
      <div class="kpi-secondary">${kpi.secondary}</div>
    `;
    card.setAttribute('role', 'listitem');
    kpiGrid.appendChild(card);
  });
}

function renderCharts(charts) {
  resetCharts();
  chartsGrid.innerHTML = '';
  Object.entries(charts).forEach(([key, data]) => {
    const card = document.createElement('article');
    card.className = 'chart-card';
    card.innerHTML = `
      <div class="chart-header">
        <h3 class="chart-title">${key.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}</h3>
        <span class="chart-unit">${data.unit}</span>
      </div>
      <canvas class="chart-canvas" aria-label="${key} chart" role="img"></canvas>
    `;
    const canvas = card.querySelector('canvas');
    chartsGrid.appendChild(card);
    const chart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {
            data: data.values,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.18)',
            tension: 0.35,
            fill: true,
            pointRadius: 3,
            pointBackgroundColor: '#1d4ed8',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          x: {
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(148,163,184,0.18)' },
          },
          y: {
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(148,163,184,0.12)' },
          },
        },
      },
    });
    STATE.charts.set(key, chart);
  });
}

function renderInsights(insights) {
  insightsList.innerHTML = '';
  if (!insights || insights.length === 0) {
    const li = document.createElement('li');
    li.textContent = 'Insights will appear here once enough data is available.';
    insightsList.appendChild(li);
    return;
  }
  insights.forEach((text) => {
    const li = document.createElement('li');
    li.textContent = text;
    insightsList.appendChild(li);
  });
}

function renderTimeline(timeline) {
  timelineList.innerHTML = '';
  if (!timeline || timeline.length === 0) {
    const empty = document.createElement('p');
    empty.textContent = 'No timeline events available for this range.';
    timelineList.appendChild(empty);
    return;
  }
  timeline.forEach((event) => {
    const item = document.createElement('article');
    item.className = 'timeline-item';
    item.innerHTML = `
      <span class="meta">
        <strong>${event.date}</strong>
        <span>${event.category}</span>
      </span>
      <span class="title">${event.title}</span>
      <p>${event.description}</p>
    `;
    timelineList.appendChild(item);
  });
}

async function renderProfile(profileId) {
  if (!STATE.pyodide) return;
  demoStatus.textContent = 'Loading demo data…';
  demoStatus.classList.remove('error');
  try {
    const csvMap = await fetchProfileCsv(profileId);
    STATE.pyodide.globals.set('CSV_MAP', csvMap);
    STATE.pyodide.globals.set('PROFILE_ID', profileId);
    const result = await STATE.pyodide.runPythonAsync('build_demo_dashboard(CSV_MAP.to_py(), PROFILE_ID)');
    const dashboard = result.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
    result.destroy();
    STATE.currentProfile = profileId;
    const profileMeta = DEMO_PROFILES.find((item) => item.id === profileId);
    renderProfileSummary(profileMeta);
    renderKpis(dashboard.kpis || []);
    renderCharts(dashboard.charts || {});
    renderInsights(dashboard.insights || []);
    renderTimeline(dashboard.timeline || []);
    demoStatus.textContent = 'Demo ready';
  } catch (error) {
    console.error(error);
    demoStatus.textContent = 'Demo failed to load';
    demoStatus.classList.add('error');
    if (profileSummary) {
      profileSummary.innerHTML = '<p class="error">Unable to render persona overview.</p>';
    }
    kpiGrid.innerHTML = '<p class="error">Failed to load demo profile.</p>';
  }
}

async function initPyodideRuntime() {
  try {
    demoStatus.textContent = 'Fetching Pyodide…';
    const pyodide = await loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/' });
    demoStatus.textContent = 'Loading Python packages…';
    await pyodide.loadPackage(['pandas']);
    const script = await fetch('pyodide/wellfair_demo.py');
    await pyodide.runPython(await script.text());
    STATE.pyodide = pyodide;
    profileSelect.innerHTML = DEMO_PROFILES.map(
      (profile) => `<option value="${profile.id}">${profile.label}</option>`
    ).join('');
    profileSelect.addEventListener('change', (event) => {
      renderProfile(event.target.value);
    });
    const defaultProfileId = DEMO_PROFILES[0]?.id;
    if (defaultProfileId) {
      await renderProfile(defaultProfileId);
    }
  } catch (error) {
    console.error(error);
    demoStatus.textContent = 'Pyodide failed';
    demoStatus.classList.add('error');
    kpiGrid.innerHTML = '<p class="error">Python runtime could not be initialised.</p>';
  }
}

// CSV → RDF converter -----------------------------------------------------
parseBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    outputEl.textContent = 'No file selected';
    return;
  }
  outputEl.textContent = 'Processing…';
  wasmStatus.textContent = 'WASM running…';
  try {
    const text = await file.text();
    const type = csvType.value;
    let result;
    switch (type) {
      case 'weight':
        result = wasm.weight_turtle_from_csv(text);
        break;
      case 'sleep':
        result = wasm.sleep_turtle_from_csv(text);
        break;
      case 'hr':
        result = wasm.heart_rate_turtle_from_csv(text);
        break;
      case 'steps':
        result = wasm.steps_turtle_from_csv(text);
        break;
      default:
        throw new Error('Unsupported dataset type');
    }
    const out = await result;
    outputEl.textContent = out;
    wasmStatus.textContent = 'Conversion complete';
  } catch (error) {
    console.error(error);
    outputEl.textContent = 'Error: ' + error;
    wasmStatus.textContent = 'Conversion failed';
  }
});

copyBtn.addEventListener('click', async () => {
  if (!outputEl.textContent || outputEl.textContent === '(no output)') return;
  try {
    await navigator.clipboard.writeText(outputEl.textContent);
    copyBtn.textContent = 'Copied!';
    setTimeout(() => {
      copyBtn.textContent = 'Copy';
    }, 2000);
  } catch (error) {
    console.warn('Clipboard unsupported', error);
  }
});

// PWA + SW handling -------------------------------------------------------
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('sw.js')
      .then((reg) => {
        console.log('ServiceWorker registered', reg.scope);
      })
      .catch((err) => {
        console.warn('ServiceWorker registration failed:', err);
      });
  });
}

let deferredPrompt = null;
const installBtn = document.getElementById('installBtn');

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredPrompt = event;
  if (installBtn) {
    installBtn.hidden = false;
  }
});

installBtn?.addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installBtn.hidden = true;
});

const updateBanner = document.getElementById('updateBanner');
const reloadBtn = document.getElementById('reloadBtn');

function showUpdate() {
  if (updateBanner) updateBanner.hidden = false;
}

reloadBtn?.addEventListener('click', async () => {
  const reg = await navigator.serviceWorker.getRegistration();
  if (reg && reg.waiting) {
    reg.waiting.postMessage({ type: 'SKIP_WAITING' });
  }
  setTimeout(() => location.reload(), 800);
});

navigator.serviceWorker?.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SW_UPDATED') {
    showUpdate();
  }
});

if (navigator.serviceWorker) {
  navigator.serviceWorker.getRegistration().then((reg) => {
    if (reg && reg.waiting) showUpdate();
  });
}

// Boot sequence -----------------------------------------------------------
activateView('dashboardView');
loadWasm();
initPyodideRuntime();

import init, * as wasm from './pkg/wellfare_core.js';

async function loadWasm() {
  try {
    await init();
    console.log('WASM initialized');
  } catch (e) {
    console.error('WASM load failed', e);
    document.getElementById('output').textContent = 'WASM load failed: ' + e;
  }
}

loadWasm();

// Register service worker to enable PWA installability and offline caching of app assets.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/docs/sw.js').then(reg => {
      console.log('ServiceWorker registered', reg.scope);
    }).catch(err => {
      console.warn('ServiceWorker registration failed:', err);
    });
  });
}

// PWA install prompt handling
let deferredPrompt = null;
const installBtn = document.getElementById('installBtn');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (installBtn) {
    installBtn.style.display = 'inline-block';
  }
});

if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log('PWA install outcome:', outcome);
    deferredPrompt = null;
    installBtn.style.display = 'none';
  });
}

// Update-notification flow: show banner when a new SW is waiting
const updateBanner = document.getElementById('updateBanner');
const reloadBtn = document.getElementById('reloadBtn');

function showUpdate() {
  if (updateBanner) updateBanner.style.display = 'block';
}

reloadBtn && reloadBtn.addEventListener('click', async () => {
  // Send skipWaiting to the waiting SW then reload
  const reg = await navigator.serviceWorker.getRegistration();
  if (reg && reg.waiting) {
    reg.waiting.postMessage({ type: 'SKIP_WAITING' });
  }
  setTimeout(() => location.reload(true), 1000);
});

navigator.serviceWorker && navigator.serviceWorker.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'SW_UPDATED') {
    showUpdate();
  }
});

// Also check for waiting SW on load
if (navigator.serviceWorker) {
  navigator.serviceWorker.getRegistration().then(reg => {
    if (reg && reg.waiting) showUpdate();
  });
}

const fileInput = document.getElementById('fileInput');
const parseBtn = document.getElementById('parseBtn');
const output = document.getElementById('output');
const csvType = document.getElementById('csvType');

parseBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    output.textContent = 'No file selected';
    return;
  }
  const text = await file.text();
  const type = csvType.value;
  try {
    let result;
    if (type === 'weight') {
      result = wasm.weight_turtle_from_csv(text);
    } else if (type === 'sleep') {
      result = wasm.sleep_turtle_from_csv(text);
    } else if (type === 'hr') {
      result = wasm.heart_rate_turtle_from_csv(text);
    } else if (type === 'steps') {
      result = wasm.steps_turtle_from_csv(text);
    }
    // result may be a string or a Promise depending on wasm-pack output
    const out = await result;
    output.textContent = out;
  } catch (e) {
    output.textContent = 'Error: ' + e;
  }
});

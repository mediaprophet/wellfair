const CACHE_VERSION = 'v26';
const CACHE_NAME = `wellfair-${CACHE_VERSION}`;
const ASSETS = [
  'index.html',
  'app.html',
  'style.css',
  'app.js',
  'pyodide/wellfair_demo.py',
  'sample_data/synthetic_steps.csv',
  'sample_data/synthetic_sleep.csv',
  'sample_data/synthetic_weight.csv',
  'sample_data/synthetic_hr.csv',
  'manifest.webmanifest',
  'icons/icon-192.svg',
  'icons/icon-512.svg',
  // Package system
  'package-download-ui.js',
  'packages/index.js',
  'packages/registry.json',
  'packages/capabilities.js',
  'packages/package-manager.js',
  'packages/pkg-prolog-wasm.js',
  'packages/pkg-llm-mediapipe.js',
];

// Large binary packages (WASM, models) are NOT pre-cached by the SW.
// They are fetched on-demand and stored in OPFS by the PackageManager.
// The SW must NOT intercept OPFS reads — OPFS is accessed directly by the page.

// Nym Wasm requires SharedArrayBuffer, which needs cross-origin isolation.
// Inject COOP/COEP on every same-origin response so crossOriginIsolated = true.
function withCrossOriginIsolation(response) {
  const h = new Headers(response.headers);
  h.set('Cross-Origin-Opener-Policy', 'same-origin');
  h.set('Cross-Origin-Embedder-Policy', 'require-corp');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: h,
  });
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

// Notify clients when a new service worker has taken control (useful to show update UI)
self.addEventListener('activate', event => {
  event.waitUntil(
    (async () => {
      const all = await self.clients.matchAll({ includeUncontrolled: true });
      for (const client of all) {
        client.postMessage({ type: 'SW_UPDATED' });
      }
    })()
  );
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return withCrossOriginIsolation(cached);
  const response = await fetch(request);
  if (response && response.ok && response.type !== 'opaque') {
    const copy = response.clone();
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, copy);
  }
  return response ? withCrossOriginIsolation(response) : response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const copy = response.clone();
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, copy);
    }
    return response ? withCrossOriginIsolation(response) : response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return withCrossOriginIsolation(cached);
    const fallback = await caches.match('index.html');
    return fallback ? withCrossOriginIsolation(fallback) : fallback;
  }
}

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin === location.origin) {
    // Network-first for HTML documents to ensure updates; cache-first for static assets including wasm/pkg
    if (url.pathname.endsWith('.html') || url.pathname.endsWith('/')) {
      event.respondWith(networkFirst(event.request));
    } else {
      event.respondWith(cacheFirst(event.request));
    }
  }
});

// Listen for messages from the page (e.g., SKIP_WAITING)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

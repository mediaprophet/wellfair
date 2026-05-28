const CACHE_VERSION = 'v2';
const CACHE_NAME = `health-to-solid-${CACHE_VERSION}`;
const ASSETS = [
  '/docs/index.html',
  '/docs/app.html',
  '/docs/style.css',
  '/docs/app.js',
  '/docs/manifest.webmanifest',
  '/docs/icons/icon-192.svg',
  '/docs/icons/icon-512.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok && response.type !== 'opaque') {
    const copy = response.clone();
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, copy);
  }
  return response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const copy = response.clone();
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, copy);
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return caches.match('/docs/index.html');
  }
}

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin === location.origin && url.pathname.startsWith('/docs/')) {
    // Network-first for HTML documents to ensure updates; cache-first for static assets including wasm/pkg
    if (url.pathname.endsWith('.html') || url.pathname === '/docs/') {
      event.respondWith(networkFirst(event.request));
    } else {
      event.respondWith(cacheFirst(event.request));
    }
  }
});

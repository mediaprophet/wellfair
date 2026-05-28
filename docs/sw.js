const CACHE_NAME = 'health-to-solid-v1';
const ASSETS = [
  '/docs/',
  '/docs/index.html',
  '/docs/app.html',
  '/docs/style.css',
  '/docs/app.js',
  '/docs/pkg/wellfare_core.js',
  '/docs/pkg/wellfare_core_bg.wasm'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // Only cache GET requests for our docs assets; ignore others (file uploads are local and won't be intercepted)
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin === location.origin && url.pathname.startsWith('/docs/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(resp => {
          // Don't cache responses that are opaque or not ok
          if (!resp || resp.status !== 200 || resp.type === 'opaque') return resp;
          const copy = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return resp;
        }).catch(() => caches.match('/docs/index.html'));
      })
    );
  }
});

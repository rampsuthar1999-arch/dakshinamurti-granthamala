// Offline support: app shell is network-first; book data and page scans are cache-first
// (they are cached as you read, so previously opened prakaraṇas/pages work offline).
const SHELL = 'dg-shell-v2', DATA = 'dg-data-v1';
const SHELL_FILES = ['./', 'index.html', 'app.js', 'style.css', 'icon.svg', 'icon-192.png', 'icon-512.png', 'manifest.webmanifest', 'data/library.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => ![SHELL, DATA].includes(k)).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.origin === location.origin && /\/data\//.test(url.pathname) && !url.pathname.endsWith('library.json')) {
    // text: serve cached copy instantly, refresh in background so corrections reach readers
    e.respondWith(caches.open(DATA).then(async c => {
      const hit = await c.match(e.request);
      const net = fetch(e.request).then(res => { if (res.ok) c.put(e.request, res.clone()); return res; }).catch(() => hit);
      if (hit) { e.waitUntil(net); return hit; }
      return net;
    }));
  } else if (url.origin === location.origin && /\/pages\//.test(url.pathname)) {
    e.respondWith(caches.open(DATA).then(async c => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      const res = await fetch(e.request);
      if (res.ok) c.put(e.request, res.clone());
      return res;
    }));
  } else if (url.origin === location.origin || url.host.endsWith('fonts.googleapis.com') || url.host.endsWith('fonts.gstatic.com')) {
    e.respondWith(fetch(e.request).then(res => {
      if (res.ok) caches.open(SHELL).then(c => c.put(e.request, res.clone()));
      return res;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match('index.html'))));
  }
});

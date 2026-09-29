const CACHE_NAME = "kaspintar-ai-v1";
const STATIC_ASSETS = [
  "/",
  "/static/index.html",
  "/static/manifest.json",
  "/static/css/custom.css",
  "/static/js/api.js",
  "/static/js/auth.js",
  "/static/js/charts.js",
  "/static/js/app.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn("ServiceWorker pre-cache warning:", err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Pass through API and non-GET requests directly to network
  if (event.request.url.includes("/api/") || event.request.method !== "GET") {
    return;
  }

  // Network-first with cache fallback for static app assets
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

/* Excavationpro Listen — network-first HTML so deploys are not stuck in cache */
const CACHE = "excavationpro-listen-shell-v4-network";
const SHELL = [
  "./manifest-listen.webmanifest",
  "./assets/listen-icon-512.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(SHELL).catch(() => undefined))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;

  // Never cache HF audio
  if (
    url.hostname.includes("huggingface.co") ||
    url.pathname.includes("/stream/")
  ) {
    return;
  }

  // HTML always network-first (fixes stuck broken deploys)
  const isHTML =
    e.request.mode === "navigate" ||
    url.pathname.endsWith(".html") ||
    url.pathname.endsWith("/");

  if (isHTML) {
    e.respondWith(
      fetch(e.request)
        .then((res) => res)
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Other same-origin assets: network-first, cache fallback
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res && res.ok && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});

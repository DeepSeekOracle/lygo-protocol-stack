/* Excavationpro Listen SW — network-first HTML so deploys are not stuck on broken shells.
 * Signature: Δ9Φ963-LISTEN-SW-v5-network
 * Never caches Hugging Face audio. Plugin JS is network-first too.
 */
const CACHE = "excavationpro-listen-shell-v5-network";
const SHELL = [
  "./manifest-listen.webmanifest",
  "./assets/listen-icon-512.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

function isHtml(req, url) {
  const accept = req.headers.get("accept") || "";
  return (
    req.mode === "navigate" ||
    url.pathname.endsWith(".html") ||
    accept.includes("text/html")
  );
}

function isPluginOrSw(url) {
  return (
    url.pathname.includes("listen-plugins/") ||
    url.pathname.endsWith("sw-listen.js") ||
    url.pathname.includes("play-listing.js")
  );
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // Never touch cross-origin audio (HF streams)
  if (
    url.hostname.includes("huggingface.co") ||
    url.pathname.includes("/stream/") ||
    url.pathname.endsWith(".mp3")
  ) {
    return;
  }

  // HTML + plugins: network-first (fixes stuck broken deploys)
  if (url.origin === self.location.origin && (isHtml(req, url) || isPluginOrSw(url))) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          // Do not put HTML into long-lived shell cache (always revalidate)
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match("./excavationpro-listen.html")))
    );
    return;
  }

  // Same-origin static: stale-while-revalidate light
  if (url.origin === self.location.origin) {
    e.respondWith(
      caches.match(req).then((hit) => {
        const net = fetch(req)
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(req, copy));
            }
            return res;
          })
          .catch(() => hit);
        return hit || net;
      })
    );
  }
});

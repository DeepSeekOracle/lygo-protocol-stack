from pathlib import Path
import re, json

listen = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html")
plugin = Path(r"I:/E Drive/Excavationpro/listen-plugins/play-listing.js")
sw = Path(r"I:/E Drive/Excavationpro/sw-listen.js")
manifest = Path(r"I:/E Drive/Excavationpro/manifest-listen.webmanifest")
ads = Path(r"I:/E Drive/Excavationpro/ads.txt")

h = listen.read_text(encoding="utf-8", errors="replace")
js = plugin.read_text(encoding="utf-8")
swc = sw.read_text(encoding="utf-8")

print("=== FILE SIZES ===")
for p in [listen, plugin, sw, manifest, ads]:
    print(f"  {p.name}: {p.stat().st_size if p.exists() else 'MISSING'}")

print("\n=== HEAD / ADSENSE ===")
head = h.split("</head>")[0] if "</head>" in h else h[:5000]
print("meta adsense", "google-adsense-account" in head and "ca-pub-0646320966060599" in head)
print("script adsense head", "adsbygoogle.js?client=ca-pub-0646320966060599" in head)
print("canonical", re.search(r'rel="canonical"[^>]+href="([^"]+)"', h).group(1) if re.search(r'rel="canonical"', h) else None)

print("\n=== PLAYER CORE ===")
checks = [
    ("audio#audio", 'id="audio"' in h),
    ("function playIndex", "function playIndex" in h),
    ("LYGO_LISTEN export", "LYGO_LISTEN_EXPORT" in h or "window.LYGO_LISTEN" in h),
    ("play-listing mount", 'id="play-listing-mount"' in h),
    ("play-listing v4", "play-listing.js?v=4" in h),
    ("sw-listen v5", "sw-listen.js?v=5" in h),
    ("wave-canvas", 'id="wave-canvas"' in h),
    ("initSafeWaveform", "initSafeWaveform" in h),
    ("createMediaElementSource live", "createMediaElementSource" in h and "no createMediaElementSource" not in h),
    ("MES only in comment", "createMediaElementSource" in h),
]
for name, ok in checks:
    print(f"  {'OK' if ok else '!!'} {name}: {ok}")

# MediaElementSource only in safe comment?
for m in re.finditer(r".{0,60}createMediaElementSource.{0,60}", h):
    s = m.group(0).replace("\n", " ")
    print("  MES ctx:", s[:140])

print("\n=== BOOT PLAYLIST ===")
m = re.search(r'<script id="boot"[^>]*>(.*?)</script>', h, re.S)
if not m:
    print("  !! no boot json")
else:
    boot = json.loads(m.group(1))
    pl = boot.get("playlist") or boot
    tracks = pl.get("tracks") or []
    print("  tracks", len(tracks))
    with_url = sum(1 for t in tracks if t.get("stream_url"))
    print("  with stream_url", with_url)
    flat = shard = other = 0
    for t in tracks:
        u = t.get("stream_url") or ""
        if re.search(r"/stream/[0-9a-f]{2}/[0-9a-f]{64}\.mp3", u):
            shard += 1
        elif re.search(r"/stream/[0-9a-f]{64}\.mp3", u):
            flat += 1
        else:
            other += 1
    print("  flat", flat, "shard", shard, "other", other)
    if tracks:
        print("  sample0", (tracks[0].get("title") or "")[:50])
        print("  url0", (tracks[0].get("stream_url") or "")[:100])

print("\n=== PLUGIN ===")
print("  MIN_SEC", re.search(r"MIN_SEC\s*=\s*(\d+)", js).group(1) if re.search(r"MIN_SEC", js) else "?")
print("  writeQueue", "writeQueue" in js or "enqueueCount" in js)
print("  drainQueue", "drainQueue" in js)
print("  getCurrent", "getCurrent" in js)
print("  silent drop writing", "if (writing) return Promise.resolve()" in js)
print("  BLOB id", "019f7611" in js)

print("\n=== SW ===")
print("  CACHE", re.search(r'CACHE\s*=\s*["\']([^"\']+)', swc).group(1) if re.search(r"CACHE\s*=", swc) else "?")
print("  network-first html", "network-first" in swc.lower() or "isHtml" in swc)
print("  HF skip", "huggingface" in swc)

print("\n=== DUPLICATE / RISK ===")
print("  playIndex defs", len(re.findall(r"function playIndex", h)))
print("  window.playIndex", "window.playIndex" in h)
print("  crossOrigin", "crossOrigin" in h or "crossorigin" in h.lower())
# multiple LYGO_LISTEN
print("  LYGO_LISTEN assigns", len(re.findall(r"window\.LYGO_LISTEN\s*=", h)))
# script order
for i, line in enumerate(h.splitlines(), 1):
    if "play-listing.js" in line or "LYGO_LISTEN" in line or "initSafeWaveform" in line or "sw-listen" in line:
        if any(x in line for x in ["play-listing", "LYGO_LISTEN_EXPORT", "initSafeWaveform", "sw-listen", "serviceWorker"]):
            print(f"  L{i}: {line.strip()[:100]}")

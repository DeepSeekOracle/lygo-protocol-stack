import re
import urllib.request

u = "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html"
req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
print("len", len(body))
for ln in body.splitlines():
    if "<title>" in ln or "<h1>" in ln:
        print(ln.strip()[:160])
checks = [
    "Live Immutable Ledger",
    "Public live catalog",
    "store restriction",
    "DistroKid ban",
    "How to use after",
    "Missing from catalog",
    "Live Feed",
    "ISRC Ledger",
    "Live Radio",
]
for s in checks:
    print(f"{s!r}: {s in body}")
m = re.search(r'class="sub">(.*?)</p>', body)
if m:
    print("sub:", m.group(1)[:220])

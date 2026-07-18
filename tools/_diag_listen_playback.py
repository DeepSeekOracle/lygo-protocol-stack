#!/usr/bin/env python3
import json
import re
import urllib.request

url = "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=45) as r:
    html = r.read().decode("utf-8", "replace")
print("live len", len(html))
m = re.search(
    r'<script id="boot" type="application/json">(.*?)</script>', html, re.S
)
if not m:
    print("NO BOOT")
else:
    data = json.loads(m.group(1))
    tracks = (data.get("playlist") or {}).get("tracks") or []
    print("tracks", len(tracks))
    ok_url = 0
    for t in tracks[:5]:
        su = t.get("stream_url")
        print(" sample", (t.get("title") or "")[:50], "url?", bool(su))
        if not su:
            continue
        try:
            req2 = urllib.request.Request(
                su, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-100"}
            )
            with urllib.request.urlopen(req2, timeout=30) as r2:
                print("  stream", r2.status, r2.headers.get("content-type"), len(r2.read()))
                ok_url += 1
        except Exception as e:
            print("  stream FAIL", e)
    print("ok samples", ok_url)

# count wrappers / danger patterns
for s in [
    "createMediaElementSource",
    "window.playIndex",
    "function playIndex",
    "LYGO GLOBAL PLAYS",
    "LISTEN PORTAL v3",
    "v2 ENHANCEMENTS",
]:
    print(s, html.count(s))

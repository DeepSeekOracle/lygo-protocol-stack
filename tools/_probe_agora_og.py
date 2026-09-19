#!/usr/bin/env python3
from pathlib import Path
import urllib.request

p = Path(r"I:\E Drive\lygo-protocol-stack\docs\assets\og-agent-agora.jpg")
b = p.read_bytes()
print("bytes", len(b))
print("SOF0 baseline", b.find(bytes([0xFF, 0xC0])), "SOF2 progressive", b.find(bytes([0xFF, 0xC2])))
print("APP0 JFIF", b.find(b"JFIF"), "APP1 EXIF", b.find(b"Exif"), "ICC", b.find(b"ICC_PROFILE"))

for ua in (
    "Twitterbot/1.0",
    "facebookexternalhit/1.1",
    "Slackbot-LinkExpanding 1.0",
):
    req = urllib.request.Request(
        "https://deepseekoracle.github.io/lygo-protocol-stack/assets/og-agent-agora.jpg",
        headers={"User-Agent": ua},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(ua, r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length"))
    except Exception as e:
        print(ua, "FAIL", e)

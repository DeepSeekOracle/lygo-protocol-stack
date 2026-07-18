#!/usr/bin/env python3
"""Build docs/bpmfinder.ca-root deploy package (index.html + AdSense root files)."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "LYGO_BPM_Finder.html"
OUT = ROOT / "docs" / "bpmfinder.ca-root"


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    html = SRC.read_text(encoding="utf-8")
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "404.html").write_text(html, encoding="utf-8")
    (OUT / "CNAME").write_text("bpmfinder.ca\n", encoding="utf-8")

    privacy = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Policy — BPMfinder.ca</title>
<link rel="canonical" href="https://bpmfinder.ca/privacy.html">
<meta name="google-adsense-account" content="ca-pub-0646320966060599">
<meta name="robots" content="index,follow">
</head>
<body style="font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#111">
<h1>Privacy Policy — BPMfinder.ca</h1>
<p><strong>Last updated:</strong> 2026-07-18</p>
<p><strong>BPMfinder.ca</strong> is a free browser-based BPM / tempo detector operated in connection with Excavationpro / LYGO projects.</p>
<h2>Audio processing</h2>
<p>Audio you choose to analyze is processed <em>locally in your browser</em> (Web Audio). We do not require an account. Files are not uploaded to our servers solely for BPM detection in the default tool.</p>
<h2>Cookies and advertising</h2>
<p>We may use cookies and similar technologies for optional advertising (including Google AdSense) and essential site function. Google and other ad partners may collect device and browser information according to their policies. You can control cookies via your browser settings.</p>
<p>Google's policies: <a href="https://policies.google.com/technologies/ads">Advertising</a> · <a href="https://policies.google.com/privacy">Privacy</a></p>
<h2>Contact</h2>
<p>Steward links: <a href="https://excavationpro.ca">excavationpro.ca</a> ·
<a href="https://www.paypal.com/paypalme/ExcavationPro">PayPal.me/ExcavationPro</a> ·
<a href="https://deepseekoracle.github.io/Excavationpro/eternalhaven.html">Eternal Haven</a></p>
<p><a href="/">Back to Free BPM Finder</a></p>
</body>
</html>
"""
    (OUT / "privacy.html").write_text(privacy, encoding="utf-8")

    # ensure ads.txt / robots / sitemap exist (keep existing if present)
    ads = OUT / "ads.txt"
    if not ads.exists() or "pub-0646320966060599" not in ads.read_text(encoding="utf-8"):
        ads.write_text("google.com, pub-0646320966060599, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")

    robots = OUT / "robots.txt"
    robots.write_text(
        """User-agent: *
Allow: /

Sitemap: https://bpmfinder.ca/sitemap.xml
""",
        encoding="utf-8",
    )

    (OUT / "sitemap.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bpmfinder.ca/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://bpmfinder.ca/privacy.html</loc>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
""",
        encoding="utf-8",
    )

    readme = OUT / "README.md"
    readme.write_text(
        """# bpmfinder.ca deploy root

Full site package for **https://bpmfinder.ca/** (AdSense + Search Console).

## Files

| File | Role |
|------|------|
| `index.html` | Free BPM Finder app (homepage) |
| `privacy.html` | Privacy policy (AdSense expects this) |
| `ads.txt` | `pub-0646320966060599` |
| `robots.txt` / `sitemap.xml` | Crawl |
| `CNAME` | GitHub Pages custom domain |

## Fix AdSense “Site down or unavailable”

1. Point DNS at a host that actually serves these files (not GoDaddy “coming soon”).
2. Recommended: GitHub Pages repo with this folder as site root (see `docs/ADSENSE_BPMFINDER_FIX.md`).
3. Confirm **https://bpmfinder.ca/** returns HTTP 200 with real HTML.
4. Confirm **https://bpmfinder.ca/ads.txt** is plain text with your pub id.
5. Only then click **I confirm I have fixed the issues** in AdSense.

Do **not** request review while the domain times out or parks.
""",
        encoding="utf-8",
    )

    print("Built", OUT)
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:16} {p.stat().st_size:8d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

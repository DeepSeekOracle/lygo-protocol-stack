# bpmfinder.ca deploy root

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

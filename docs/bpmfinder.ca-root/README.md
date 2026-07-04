# bpmfinder.ca site root files

Copy these to the **document root** of https://bpmfinder.ca/ (where the BPM HTML is served):

| File | Purpose |
|------|---------|
| `robots.txt` | Allow crawlers; points to sitemap |
| `sitemap.xml` | Single-URL sitemap for the free BPM finder |
| `ads.txt` | Google AdSense seller declaration |

The BPM page itself lives in repo `docs/LYGO_BPM_Finder.html` (materialized to Excavationpro `LYGOBPMFinder.html`). Ensure the live host serves that page at `/` or redirect to it with canonical `https://bpmfinder.ca/`.
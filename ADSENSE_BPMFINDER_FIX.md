# Fix AdSense for bpmfinder.ca — “Site down or unavailable”

## Diagnosis (2026-07-18)

| Check | Result |
|-------|--------|
| `https://bpmfinder.ca/` | **DOWN / timeout** |
| `www.bpmfinder.ca` | **DNS missing** |
| DNS A records | `15.197.142.173`, `3.33.152.147` (GoDaddy parking / forwarding — not a live site) |
| Working mirrors | `https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html` |
| | `https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html` |

AdSense is correct: **the domain you submitted is not serving a site.**  
Do **not** click “I confirm I have fixed the issues” until `https://bpmfinder.ca/` loads the BPM tool.

---

## Goal

```text
https://bpmfinder.ca/           → Free BPM Finder (index.html)
https://bpmfinder.ca/ads.txt    → google.com, pub-0646320966060599, DIRECT, ...
https://bpmfinder.ca/privacy.html
https://bpmfinder.ca/robots.txt
https://bpmfinder.ca/sitemap.xml
```

Deploy package (already in repo):

`docs/bpmfinder.ca-root/`  
(regenerate anytime: `python tools/build_bpmfinder_ca_root.py`)

---

## Recommended fix: GitHub Pages + custom domain

### A. Create a tiny public repo (cleanest)

1. GitHub → new repo **`bpmfinder`** (public), owner **DeepSeekOracle**.
2. Upload **everything inside** `docs/bpmfinder.ca-root/` to the **root** of that repo  
   (`index.html`, `ads.txt`, `privacy.html`, `robots.txt`, `sitemap.xml`, `CNAME`, `404.html`).
3. Repo → **Settings → Pages**:
   - Source: **Deploy from a branch**
   - Branch: `main` / `/ (root)`
4. Custom domain: **`bpmfinder.ca`**
5. Enable **Enforce HTTPS** after DNS works.

### B. GoDaddy DNS (replace parking)

In GoDaddy → **bpmfinder.ca** → DNS → delete parking/forwarding that points to:

- `15.197.142.173`
- `3.33.152.147`

**For apex `bpmfinder.ca` (GitHub Pages):**

| Type | Name | Value | TTL |
|------|------|--------|-----|
| **A** | `@` | `185.199.108.153` | 600 |
| **A** | `@` | `185.199.109.153` | 600 |
| **A** | `@` | `185.199.110.153` | 600 |
| **A** | `@` | `185.199.111.153` | 600 |
| **CNAME** | `www` | `deepseekoracle.github.io` | 600 |

Also add GitHub’s verification TXT if Pages shows one (Domain settings).

Wait 15–60 minutes (sometimes longer). Test:

```text
https://bpmfinder.ca/
https://bpmfinder.ca/ads.txt
https://bpmfinder.ca/privacy.html
```

All must return **200**, not park/timeout.

### C. Optional: Cloudflare (often better than GoDaddy DNS)

1. Add site in Cloudflare (free).  
2. Change nameservers at GoDaddy to Cloudflare.  
3. Same A/CNAME records → GitHub Pages.  
4. SSL: Full (strict) once cert is issued.

---

## AdSense checklist (after site is up)

1. **Ownership**  
   - Search Console property `https://bpmfinder.ca/` verified, **or**  
   - AdSense meta/tag already in `index.html` (`ca-pub-0646320966060599`).
2. **ads.txt** at exact URL:  
   `https://bpmfinder.ca/ads.txt`  
   Content:
   ```text
   google.com, pub-0646320966060599, DIRECT, f08c47fec0942fa0
   ```
3. **Content**  
   - Working tool + visible text (FAQ already on the page).  
   - Privacy page linked (footer / policy).  
   - No “coming soon” only.
4. **Wait** until Google can crawl successfully (often 24–72h after DNS).
5. Then click **I confirm I have fixed the issues**.

---

## Temporary (not enough for AdSense)

Redirecting bpmfinder.ca → github.io **without** hosting real content on the domain often fails AdSense review. Host the real `index.html` on the domain.

---

## Until DNS is fixed

Share the working tool:

- https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html  
- https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html  

Do **not** resubmit AdSense on those URLs if the application is for **bpmfinder.ca**.

---

## Quick commands

```bash
cd lygo-protocol-stack
python tools/materialize_bpm_finder_pages.py
python tools/build_bpmfinder_ca_root.py
# then upload docs/bpmfinder.ca-root/* to the bpmfinder GitHub Pages root
```

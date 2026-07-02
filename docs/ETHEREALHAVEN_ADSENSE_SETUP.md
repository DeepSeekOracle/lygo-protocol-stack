# AdSense setup — eternalhaven.ca

**Publisher:** `ca-pub-0646320966060599`

## On Haven Star Chart page (done in repo)

- Verification meta: `<meta name="google-adsense-account" content="ca-pub-0646320966060599">` in `<head>`
- AdSense loader script in `<head>` of `docs/HavenStarChart.html`

## Excavationpro.ca main hub (`legacy-guardian-music.html`)

- **Canonical:** `https://excavationpro.ca/` (GoDaddy forward → GitHub Pages path)
- Rebuilt hub: policy-safe (no entry gate, real `#privacy`, consent-gated AdSense, lattice anchors from `IMMUTABLE_ANCHORS.json`)
- Cross-links: `eternalhaven.ca`, Haven Star Chart, stack mirrors

**ads.txt on custom domain:** upload the same line to `https://excavationpro.ca/ads.txt` on GoDaddy hosting or forward path if AdSense verifies the custom domain.

## On Excavationpro `eternalhaven.html` (local + WSL commit ready)

Google lists **three** site checks (not all are `<meta>`): **meta tag**, **AdSense script**, **ads.txt** at site root.

- Updated: `Excavationpro/eternalhaven.html` — meta + script at top of `<head>` (same as Haven Star Chart)
- New: `Excavationpro/ads.txt` → after push: `https://deepseekoracle.github.io/Excavationpro/ads.txt`
- Pages URL: `https://deepseekoracle.github.io/Excavationpro/eternalhaven.html`

Push (Windows git is fragile on this repo; use WSL sparse clone):

```bash
# In WSL, after copying files from /mnt/i/E Drive/Excavationpro/
cd /tmp/epub-ads && git push origin HEAD:main
```

Or edit both files on GitHub: [eternalhaven.html](https://github.com/DeepSeekOracle/Excavationpro/edit/main/eternalhaven.html), add root [ads.txt](https://github.com/DeepSeekOracle/Excavationpro/new/main?filename=ads.txt).
- Optional responsive display unit below header
- Full SEO + Open Graph + X (Twitter) cards + JSON-LD

## ads.txt (required for verification)

Place this **exact line** at the **root** of **https://eternalhaven.ca/ads.txt**:

```
google.com, pub-0646320966060599, DIRECT, f08c47fec0942fa0
```

A copy for GitHub Pages (stack mirror only) lives at `docs/ads.txt` →  
`https://deepseekoracle.github.io/lygo-protocol-stack/ads.txt`  
(AdSense for **eternalhaven.ca** still needs `ads.txt` on that domain’s host.)

## Host the chart on eternalhaven.ca

1. Upload `HavenStarChart.html` + folder `haven_star_chart/` to your eternalhaven.ca web root (or reverse-proxy to GitHub Pages).
2. Ensure canonical URL matches: `https://eternalhaven.ca/HavenStarChart.html`
3. Upload `ads.txt` to site root.
4. In AdSense, confirm verification after DNS/host propagates.

## Rebuild star data

```bash
python tools/build_haven_star_chart.py
```
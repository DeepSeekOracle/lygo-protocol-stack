# AdSense setup — eternalhaven.ca

**Publisher:** `ca-pub-0646320966060599`

## On Haven Star Chart page (done in repo)

- AdSense loader in `<head>` of `docs/HavenStarChart.html`
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
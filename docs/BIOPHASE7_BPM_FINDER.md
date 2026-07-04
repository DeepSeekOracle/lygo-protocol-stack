# Biophase7 → LYGO BPM Finder

**Provenance:** `LYRA SYSTEM RETORE/FINAL RESTORE/ALL SEALS/220+/New folder/2026Biophase7/Design a LYGO Online BPM finder and.txt`  
**Public URL:** https://bpmfinder.ca/  
**Repo page:** [`LYGO_BPM_Finder.html`](LYGO_BPM_Finder.html) (GitHub Pages mirror)  
**Excavationpro mirror:** `LYGOBPMFinder.html` (sync via `tools/materialize_bpm_finder_pages.py`)

## Design choices (honest scope)

| Original blueprint | LYGO delivery |
|------------------|---------------|
| pleco-xa / @uln/impulse | **[bpm-detective](https://www.npmjs.com/package/bpm-detective)** via jsDelivr ESM |
| P0/P1/P3 + Kernel Eggs on audio | **Skipped** — no lattice value on raw audio BPM; privacy-first client tool |
| HF librosa backend | **Optional** — operators can add a HF Space tab later; not required for v1 |
| Mic / live stream primary | **File upload primary** — tap tempo covers manual override |

## SEO & discoverability

- **Primary canonical:** https://bpmfinder.ca/ (all mirrors point here)
- **On-page copy:** visible H2/H3 + FAQ block targeting “free BPM finder”, “online tempo detector”, MP3/WAV/FLAC
- **Structured data:** `WebSite`, `WebApplication` (`isAccessibleForFree`), `Organization`, `BreadcrumbList`, `FAQPage` (`@graph` JSON-LD)
- **Social:** Open Graph + Twitter/X cards; `og:locale`, image dimensions
- **Crawl hints:** `index, follow` + `googlebot` / `bingbot`; `hreflang` en + x-default
- **Sitemaps:** `docs/sitemap.xml`, `Excavationpro/sitemap.xml` (bpmfinder.ca priority 1.0, weekly)
- **Custom domain root** (upload to bpmfinder.ca host): `docs/bpmfinder.ca-root/robots.txt`, `sitemap.xml`, `ads.txt`
- **Hub internal links** (keyword anchors): `eternalhaven.html`, `index.html`, `main.html`, Haven Star Chart, legacy Guardian music, LYGORESONANCE, stack `docs/index.html`

### Search Console (operator)

1. Add property **https://bpmfinder.ca/** in [Google Search Console](https://search.google.com/search-console).
2. Verify via DNS or HTML tag on the live host.
3. Submit **https://bpmfinder.ca/sitemap.xml** (from `bpmfinder.ca-root`).
4. Optional: Bing Webmaster Tools — same sitemap URL.
5. Request indexing for the homepage after major SEO updates.

Regenerate pages after prototype edits:

```bash
python tools/materialize_bpm_finder_pages.py
```

## Features shipped

- Web Audio decode → `detect(AudioBuffer)`
- Multi-window **confidence** heuristic (agreement across track segments)
- **÷2 / ×2** octave correction
- **Tap tempo** fallback
- **Waveform** + beat-grid overlay on the same buffer

## Public URLs

| Surface | URL |
|---------|-----|
| **bpmfinder.ca** (primary) | https://bpmfinder.ca/ |
| GitHub Pages (stack `/docs`) | https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html |
| Excavationpro mirror | https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html |

## Sync

```bash
cd lygo-protocol-stack
python tools/sync_excavationpro_bpm_finder.py
python tools/apply_excavationpro_adsense_policy.py
```

## Optional backend (operators)

```python
import librosa

def detect_bpm(path):
    y, sr = librosa.load(path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)
```

Use only when you need server-side formats or batch jobs; the public tool stays browser-only by default.
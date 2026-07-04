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

- Per-surface **canonical**, **Open Graph**, **Twitter/X Card**, and **schema.org WebApplication** JSON-LD
- `index, follow` robots + keyword meta aimed at “BPM finder” / “tempo detector” queries
- **`docs/sitemap.xml`** + **`docs/robots.txt`** (stack Pages); **`Excavationpro/sitemap.xml`** + **`robots.txt`**
- Hub links: `eternalhaven.html`, `index.html`, `main.html`, Haven Star Chart, legacy Guardian music, LYGORESONANCE footer

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
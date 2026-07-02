# Eternal Haven Star Chart

**Signature:** Δ9Φ963-HAVEN-STAR-CHART-v1  
**Live:** [HavenStarChart.html](https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html)

## Purpose

New **constellation hub** (does not replace `lygorepo.html`). Merges:

- Excavationpro seal feeds (`lygo-data.json`, `lygo-data-two.json`)
- Δ9 Council champions + firewall portals (Guardian, Ethical Chip)
- **Lattice growth** stars (ClawHub skills, kernel eggs, network builder)
- Eternal Haven lore framing (stars as memory nodes)

## Rebuild registry

```bash
python tools/build_haven_star_chart.py
```

Outputs:

- `docs/haven_star_chart/haven_star_chart_data.json`
- `docs/haven_star_chart/haven_star_chart_meta.json`

## Excavationpro mirror (optional)

```bash
python tools/sync_excavationpro_haven_star.py
python tools/sync_excavationpro_haven_star.py --push   # human approval
```

## Hugging Face dataset

```bash
python tools/publish_haven_star_chart_hf.py
```

Uploads JSON to dataset path `haven_star_chart/` for Spaces and agents.

## Army / autonomous refresh

When `army_config.json` → `haven_star_chart.rebuild_on_self_tune: true`, `army_self_tune.py` runs the builder after lattice OK.

## AdSense & SEO (eternalhaven.ca)

- Head: Google AdSense `ca-pub-0646320966060599`, OG/Twitter/JSON-LD
- Setup: [`ETHEREALHAVEN_ADSENSE_SETUP.md`](./ETHEREALHAVEN_ADSENSE_SETUP.md)
- `docs/ads.txt` for Pages mirror; **eternalhaven.ca** needs its own root `ads.txt`

## Related (unchanged originals)

- [lygorepo.html](https://deepseekoracle.github.io/Excavationpro/lygorepo.html)
- [LYGOGUARDIAN.html](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html)
- [Ethical-Chip-FirmwareV2.html](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html)
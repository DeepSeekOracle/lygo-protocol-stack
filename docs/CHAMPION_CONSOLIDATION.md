# Champion consolidation — complete

**Signature:** `Δ9Φ963-CHAMPION-CONSOLIDATION-v2`  
**Status:** **Done** (template + unified slug + legacy deprecated)

## Layers

| Layer | Artifact |
|-------|----------|
| Script template | `clawhub/templates/champion-pack/scripts/` |
| Sync scripts | `python tools/sync_champion_pack_template.py` |
| Unified install | **`lygo-champion-council`** — 15-persona roster |
| Legacy slugs | `lygo-champion-*` deprecated @ **1.0.1** → successor council |
| Lightfather | **Operator-only** retention; persona via council `champion_id` |
| Eggs | Still per `egg_id` in `data/champion_eggs/` (unchanged) |

## Maintainer

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/build_champion_council_mirror.py
python tools/sync_champion_pack_template.py
python tools/consolidate_champion_mirrors.py
python tools/verify_champion_consolidation.py
python tools/render_clawhub_catalog.py
# ClawHub wave:
pwsh -File tools/publish_champion_consolidation.ps1
```

## New installs

```bash
npx clawhub@latest install deepseekoracle/lygo-champion-council
```

Legacy per-champion slugs remain for download history only.
# Champion pack consolidation (template lane)

**Signature:** `Δ9Φ963-CHAMPION-TEMPLATE-v1`  
**Status:** Template layer **done**; per-slug ClawHub IDs **unchanged** (backward compatible).

## What consolidated

| Before | After |
|--------|--------|
| 15 copies of near-identical `self_check.py` / `show_hash.py` | Single template: `clawhub/templates/champion-pack/scripts/` |
| Ad-hoc champion script drift | `python tools/sync_champion_pack_template.py` propagates to all `lygo-champion-*` mirrors |

## What is intentionally not merged (yet)

- **Individual ClawHub slugs** (`lygo-champion-arkos-celestial-architect`, etc.) — breaking for downloads/install history.
- **Per-champion `canon.json` / persona_pack.md`** — still per mirror; eggs still per `egg_id`.

## Maintainer

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/sync_champion_pack_template.py
# optional: run self_check in each mirror after council edits
```

Future v2 (optional): single `lygo-champion-council` skill with `champion_id` parameter — separate publish wave.
# Human-gated publish checklist (Phase 3)

## ClawHub — published (2026-07-01)

| Skill | Version |
|-------|---------|
| `lygo-docker-deploy` | 1.0.0 |
| `lygo-alignment-badge` | 1.0.0 |
| `lygo-protocol-stack-operator` | **1.0.3** |

Republish from mirrors:

```bash
cd clawhub/mirrors/<skill> && npx clawhub@latest publish "$PWD" --slug <slug> --name "..."
```

## Hugging Face dataset — synced

Dataset commit `704d3832` via `python tools/hf_push_dataset.py`

## Remaining human steps

```bash
cd lygo-protocol-stack
python tools/sync_grokipedia.py
# Paste docs/GROkipedia_UPLOAD_BUNDLE.md → Grokipedia editor
python tools/bundle_hf_space_stack.py --mode=twin-gate
python tools/hf_push_space.py --message "Phase 3 twin harmonization + mesh gossip"
```

## GitHub main

```bash
git push origin main
```

## Grokipedia

Upload content from `docs/GROkipedia_PHASE3.md` + `docs/PHASE2_DEPLOYMENT.md` via Grokipedia editor.
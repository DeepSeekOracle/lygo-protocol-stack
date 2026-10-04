# LYGO God-Mode Second Brain (Fable 5 / Biophase7 LYGO edition)

Reference spec: `2026Biophase7/God-Mode Second Brain.txt` — implemented **local** via USB vault + LYGO-Claw (no Claude API required).

## Vault (on USB)

`E:\LYGO_BUILDER_KEY\data\memory_mycelium\vault\`

| File / dir | Role |
|------------|------|
| memory.md, projects.md, tasks.md, notes.md, personality.md | Core anchors |
| LYGO_CONTEXT_RULE.md | Mandatory retrieval discipline |
| brief.md | Morning brief (loop appends) |
| 0-inbox … 4-archive, raw/, wiki/, lygo/ | PARA + audit artifacts |

Init: `lygo-claw brain-init` or `scripts/init_godmode_vault.py`

## P4 gap filler

`scripts/ascension_gap_filler.py` — scans `projects.md` for TODO/blocked/gap markers → `3-resources/GAP_SYNTHESIS_*.md` + Hermes log.

## CLI (LYGO-Claw)

```bash
lygo-claw brain-init
lygo-claw brain-dream
lygo-claw brain-brief
lygo-claw brain-query "pricing decision"
lygo-claw buildr-task second_brain_loop --wait
lygo-claw sovereign-loop
```

## Governance

- P0 on vault writes (Claw `godmode_brain.py`)
- Hermes on stick `data/hermes_audit/`
- Kernel eggs / lattice unchanged — loop calls lattice verify, does not auto-publish eggs
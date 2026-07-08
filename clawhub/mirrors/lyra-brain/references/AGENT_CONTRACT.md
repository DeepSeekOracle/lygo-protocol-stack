# LYRA 3-Brain — agent contract

## Must

1. **Additive only** — no destructive overwrite of vault/graph without explicit user consent.
2. **P0/Oath** — every `grow()` is validated; gated nodes stay flagged, not hidden.
3. **Snip discipline** — completed work → dated md + optional grow; not wall-of-text in graph.
4. **Real data** — log actual URLs, post IDs, merkle roots, file paths that exist.
5. **Cross-link stack** — reference `lygo-protocol-stack-operator`, `lyra-openclaw`, `lygo-ollama-army` when ops touch lattice/army/Moltx.

## Must not

1. Auto-publish GitHub/HF/ClawHub/social (unless user explicitly asks).
2. Put secrets in SKILL, memory, or grow text.
3. Claim ALIGNED without `verify_lattice_alignment.py` when stating lattice health.

## When to load this skill

- User asks to remember session, log memory, 3-brain, recall, grow, daily log.
- After multi-step LYGO/Moltx/Discord/hub work — **close with snips**.
- Before long compaction — write snips first.

## Recall modes (`brain_recall`)

- `balanced` (default), `library`, `outer`, `working` — see SKILL.md.
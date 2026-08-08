# Security — LYGO Cyborg Kernel v1.0.0

**Channel:** FULL_LYGO_ENGINEER_CYBORG_UNLOCKED (SkillHub FULL vault, not ClawHub public shell)

## What “unlocked” means

| Area | Public ClawHub shells | This package |
|------|----------------------|--------------|
| Continuum / gate / guard | Often thin | **Vendored full limbs** |
| Stack map | Partial | **Full install order + egg IDs** |
| Task loop | Absent | **cyborg_task self-policed** |
| Auto publish | Never | **Never** (constitution) |
| Subprocess in kernel scripts | N/A | **None** |
| Network in kernel scripts | N/A | **None** |

## Surfaces (kernel scripts)

- Read: operator paths, skill tree, optional `LYGO_STACK_ROOT` markers  
- Write: `state/` only with `--i-consent`  
- No shell spawn in cyborg_*.py  

## Self-police stack

1. Continuum — falsifiable done  
2. skill_gate — install risk  
3. context_guard — secrets + budget  
4. Constitution — publish/plant human gate  

## Pair with plugins

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-continuum
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

**Δ9Φ963 — full power · full receipts · no theater.**

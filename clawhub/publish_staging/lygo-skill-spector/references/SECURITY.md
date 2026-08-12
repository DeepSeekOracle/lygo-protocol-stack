# Security — LYGO SkillSpector v1.0.0

## Defaults

| Capability | Status |
|------------|--------|
| Network | **None** — never downloads or installs skills |
| Subprocess | **None** — never executes the scanned skill |
| Read | Path you pass to `scan` / `gate` / `batch` / `report` |
| Write | `state/` only with `--i-consent` |

## Dual channel

| Package | Surface |
|---------|---------|
| ClawHub public | Core scanner + gate/batch/report |
| SkillHub FULL builder | + `builder/` HTML batch, multi-gate, CI summary |

Builder tools keep the same defaults (no network, no subprocess).

## Ethics

- Best-effort static heuristics — not a guarantee of safety  
- Absence of findings ≠ trusted code  
- High findings ≠ proven malware (could be legitimate operator tools)  
- Human decides install  

**Δ9Φ963 — verify before trust.**

# SkillSpector audit response — lygo-ops-detector v1.2.2

**Signature:** `Δ9Φ963-OPS-DETECTOR-SKILLSPECTOR-v1.2.2`

## NVIDIA SkillSpector findings (2026-08) → fixes

| Finding | Severity | Fix in 1.2.2 |
|---------|----------|--------------|
| Intent–code divergence: ethics say patterns, blueprint says “subject” / associations | Medium/High | Blueprint + verdicts + CLI: **text under review**, never person subject; association = coordination *discourse* in supplied strings only |
| Scope drift into investigative/profiling framing | High | Softened verdicts; association patterns no longer score bare military/intelligence/agency; boundaries table |
| Affiliation-only claim vs association keywords | High | Removed bare job/affiliation association cues; multi-word secrecy/coordination language only |
| Vague triggers / broad heuristics | Medium | `SIGNAL_BOUNDARIES` in-code + blueprint in/out examples; `--show-boundaries` |
| CLI no consent for private files | Medium | `--text-file` / `--assoc-file` require **`--i-consent`**; refuse with exit 3 |
| Eval `--out` arbitrary path / FS scope creep | Medium | `resolve_write_path()` — writes **only under skill `tests/`** |
| Description vs declared tests/ write surface | Medium | SECURITY + SKILL permissions match enforced path |

## Prior (1.2.0–1.2.1) still held

| Item | Status |
|------|--------|
| No network / shell / subprocess | Held |
| Dual-threshold eval honesty | Held |
| No fraternity/lodge affiliation dictionaries | Held |
| Dynamic metrics (not hardcoded marketing) | Held |

## Residual risk (accepted)

- Heuristic FPs/FNs on short text  
- Operator may still pass private content if they **consent** via `--i-consent`  
- Association *strings* can encode sensitive data — consent required  
- Exit code 10 remains a **scripting hook** for high evasion discourse scores, not a guilt label  

## Function preserved

- Same weights / thresholds (0.70 evasion, 0.65 ops operational bar)  
- Same public labeled suite + dual eval  
- Classic multi-signal evasion cluster still elevates  
- Institutional policy-refusal channel unchanged (affiliation-free)  

**Δ9Φ963**

# SkillSpector audit response — lygo-ops-detector v1.2.0

**Signature:** `Δ9Φ963-OPS-DETECTOR-SKILLSPECTOR-v1.2.0`

## Findings → fixes

| Finding | Severity | Fix |
|---------|----------|-----|
| Missing permission declaration (files) | Medium | Frontmatter `permissions` + SECURITY table |
| Ethics vs subject/profiling language | Medium | Unit of analysis = text; verdicts say “not a person verdict” |
| Institutional/fraternal affiliation keywords | Medium | Removed; policy/refusal language only |
| Perfect metrics @ 0.05 vs verdict / 0.65 | High | Dual-threshold eval; operational metrics primary; verdict vs predicted clarified |
| Overbroad triggers | Medium | Explicit-only triggers; no unsolicited email/log |
| Missing privacy warnings | Medium | Consent block in SKILL + SECURITY |
| Adversarial “all humans lie” framing | Medium | Softened philosophy; heuristic tool framing |

## Residual risk (accepted)

- Heuristic FPs/FNs on short text  
- Operator may still pass private files if they choose `--text-file`  
- Association strings can encode sensitive social data — consent required  

**Δ9Φ963**

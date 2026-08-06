# LYGO Ops Detector — SECURITY & ETHICS v1.2.2

## Declared permissions

| Capability | Status |
|------------|--------|
| Network | **None** (stdlib local only) |
| Shell / subprocess | **None** |
| Read files | Opt-in `--text-file` / `--assoc-file` **only with `--i-consent`** |
| Write files | `eval_ops_detector.py` writes **only under skill `tests/`** |
| Env harvesting | **No** |
| Publish / social | **No** |

## Core mandate

Heuristic **discourse** analysis of evasion and coordination *signals* in text the operator supplies.

It is **not**:

- A doxing tool  
- An identity, profession, or affiliation profiler  
- A sole-evidence engine for accusations  
- A warrant to scan private mail/logs without consent  
- A social-graph crawler  

## Non-negotiables

1. **Text over identity** — unit of analysis is statement/log content, not personhood.  
2. **Consent** for private communications and association lists (`--i-consent` on file paths).  
3. **Receipts** — high scores require cited pattern hits; never “trust the detector.”  
4. **No affiliation / bare job-title dictionaries** — no fraternity/brotherhood/lodge; no bare military/intelligence/agency scoring.  
5. **Operational bar honesty** — `ops_score≥0.65` (or high evasion) for strong language; low thresholds are calibration only.  
6. **Human review** before any reputational, employment, legal, or social action.  
7. **Least-privilege writes** — eval reports cannot escape skill `tests/`.  

## Failure modes to reject

- Treating low scores as “innocent person” or high scores as “guilty person”  
- Using affiliation/religion/job title as a proxy for ops  
- Feeding outputs to social pile-ons  
- Advertising calibration metrics as production performance  
- Arbitrary `--out` paths outside `tests/`  

## Agent contract

- Invoke only when the user asks for ops-detector / AETHONΔ9 / evasion-index style analysis.  
- Do not auto-scan session email/logs without explicit intent + consent.  
- Prefer `--text` paste; file paths require `--i-consent`.  

**Δ9Φ963**

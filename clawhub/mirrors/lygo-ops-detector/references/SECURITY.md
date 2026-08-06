# LYGO Ops Detector — SECURITY & ETHICS v1.2.0

## Declared permissions

| Capability | Status |
|------------|--------|
| Network | **None** (stdlib local only) |
| Shell / subprocess | **None** |
| Read files | Opt-in CLI `--text-file` / `--assoc-file` only |
| Write files | `tests/last_eval_report.json` when eval is run |
| Env harvesting | **No** |
| Publish / social | **No** |

## Core mandate

Heuristic **discourse** analysis of evasion and coordination *signals* in text the operator supplies.

It is **not**:

- A doxing tool  
- An identity or affiliation profiler  
- A sole-evidence engine for accusations  
- A warrant to scan private mail/logs without consent  

## Non-negotiables

1. **Text over identity** — unit of analysis is statement/log content, not personhood.  
2. **Consent** for private communications and association lists.  
3. **Receipts** — high scores require cited pattern hits; never “trust the detector.”  
4. **No affiliation dictionaries** (v1.2+) — no fraternity/brotherhood/lodge keyword scoring.  
5. **Operational bar honesty** — `ops_score>=0.65` (or high evasion) for strong language; low thresholds are calibration only.  
6. **Human review** before any reputational, employment, legal, or social action.  

## Failure modes to reject

- Treating low scores as “innocent person” or high scores as “guilty person”  
- Using affiliation/religion/group membership as a proxy for ops  
- Feeding outputs to social pile-ons  
- Advertising calibration metrics as production performance  

## Lightfather directive (v1.2)

Prefer rigor and primary sources over narrative.  
Heuristic scores are **weak evidence of discourse patterns**, not character judgments.

**Δ9Φ963**

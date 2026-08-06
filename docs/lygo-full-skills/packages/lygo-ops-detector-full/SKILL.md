---
name: lygo-ops-detector
description: "LYGO Ops Detector — local AETHONΔ9 discourse heuristics for evasion / coordination / policy-refusal signals in text the operator supplies. Opt-in only when user asks for ops detector, AETHONΔ9, or evasion index. Stdlib CLI; --text-file/--assoc-file require --i-consent; eval writes only under tests/. Not for doxing, identity/profession profiling, or unsolicited email/log analysis. Dual-threshold metrics (operational 0.65 vs calibration). Triggers: lygo ops detector, aethon d9, evasion index (explicit)."
version: 1.2.2
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "🔎"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
    requires:
      anyBins: [python, python3]
  lygo: true
  lightfather: true
  aethon: "Δ9"
  protocol: "AETHONΔ9"
  version: "1.2.2"
  companion: "lygo-champion-lightfather"
  security: "references/SECURITY.md"
  blueprint: "references/AETHON_D9_BLUEPRINT.md"
  eval: "tests/labeled_discourse_suite.json + scripts/eval_ops_detector.py"
  security_review: "1.2.2-skillspector-discourse-not-identity"
  permissions:
    network: false
    shell: false
    subprocess: false
    filesystem:
      read: "user-supplied --text-file / --assoc-file only with --i-consent"
      write: "tests/ only when eval_ops_detector.py is run"
    publish: false
    doxing: false
    identity_profiling: false
---

# LYGO Ops Detector — AETHONΔ9 v1.2.2

Local, deterministic **discourse-signal** heuristics.  
**Not** a person profiler. **Not** sole evidence. **Not** for doxing.

## Permissions (declared)

| Capability | Default |
|------------|---------|
| Network | **None** |
| Shell / subprocess | **None** |
| Read local files | Only `--text-file` / `--assoc-file` **+ `--i-consent`** |
| Write | Eval report under **`tests/` only** |
| Auto-publish / social | **Never** |

## Privacy / consent (required reading)

Before analyzing **email, DMs, private logs, or association lists**:

1. Confirm the **human operator consents** and has authority (`--i-consent` on file inputs).  
2. Prefer redacted text via `--text`; do not paste secrets or third-party PII into shared chats.  
3. Scores can cause **reputational harm** if misused — treat as weak heuristics.  
4. Do **not** run this skill unsolicited on “any email/log” in the session.  

## When to invoke (narrow)

Invoke **only** when the user explicitly wants one of:

- LYGO Ops Detector / AETHONΔ9 / evasion index on **text they paste or name**  
- Reproducible scoring of operational-deception **discourse patterns**  
- Re-run of the public labeled eval suite  

**Do not** auto-trigger on generic “analyze this email/log/thread” without ops-detector intent.

## What it measures (scope)

| Channel | Measures | Does **not** measure |
|---------|----------|----------------------|
| **Evasion** | Burden-shift, ad hominem, vague claims, authority inflation, gaslight, deflection **templates** | Person identity |
| **Association** | Coordination/secrecy **language** in association strings you provide | Social graph doxing; bare job titles |
| **Institutional** | Policy-as-shield / refusal-to-comment language only | Affiliation, faith, fraternity, lodge, profession labels |

Unit of analysis = **text under review**, not a human “subject” or investigation target.

## Boundaries (anti-vague-trigger)

Each signal has in-scope / out-of-scope examples (`--show-boundaries`). Ordinary disagreement without proof-avoidance templates should stay low.

## Thresholds (honest)

| Bar | Meaning |
|-----|---------|
| **Operational** `ops_score >= 0.65` or high evasion | Documented strong multi-signal bar for human review |
| **Calibration** (lower, e.g. 0.05) | Short-suite ranking only — **not** production performance |

```bash
python scripts/eval_ops_detector.py tests/labeled_discourse_suite.json --sweep
# report: operational_metrics (0.65) + calibration_metrics (ranking only)
# --out must stay under tests/
```

## Safe use

```bash
cd path/to/lygo-ops-detector
python scripts/self_check.py
python scripts/lygo_ops_detector.py --text "paste discourse here" --json
# optional local files (operator affirms authority):
python scripts/lygo_ops_detector.py --text-file ./snippet.txt --i-consent
python scripts/lygo_ops_detector.py --show-boundaries
```

Exit codes: `0` = no strong operational pattern; `3` = consent required; `10` = high evasion discourse signals (review claims).

## Agent contract

1. Call the **script** for reproducible scores.  
2. Separate **observed regex hits** vs inference.  
3. Never name people as investigation targets from this tool alone.  
4. Remind: discourse pattern ≠ guilt; human + primary sources required.  
5. No external publication of results without user consent.  
6. File inputs require `--i-consent`.  

## Security

See `references/SECURITY.md` and `references/SKILLSPECTOR_AUDIT.md`.

## Version

| Ver | Change |
|-----|--------|
| 1.1.0 | Dynamic eval suite |
| 1.2.1 | Permissions, narrow triggers, dual-threshold honesty |
| **1.2.2** | SkillSpector: discourse-not-subject framing; no bare job/affiliation association cues; `--i-consent` on files; eval writes constrained to `tests/`; signal boundaries |

**Δ9Φ963 — receipts over hype · discourse not identity · consent before private data.**

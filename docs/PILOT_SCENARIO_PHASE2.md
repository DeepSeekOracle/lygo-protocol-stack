# Pilot Phase 2 — Ethical Guardian (public)

**Status:** Grok-approved after 40/40 audit harness · HF Space `dd7826a` live.

## Platform

- [LYGO-Resonance-Engine](https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine) → accordion **LYGO Ethical Guardian (P0–P5 Stack Pilot)**
- Outputs: **phi_risk** slider, **P0 verdict**, full stack trace, **Light Code**, **ethical mass**

## Scenario set (real-world edge cases)

| ID | Edge case |
|----|-----------|
| PILOT-01-BULK-DATA | National security bulk data access |
| PILOT-02-E2E-BACKDOOR | Mandatory encryption backdoors |
| PILOT-03-SCRAPE-TRAIN | Scrape-to-train without consent |
| PILOT-04-WORKPLACE-NEURO | Employer neural/biometric monitoring |
| PILOT-05-DEVICE-SEARCH | Border device decryption demands |
| PILOT-06-INTIMATE-EXTRACTION | Intimate AI chats sold to advertisers |

## Run locally (live only)

```bash
python tools/run_pilot_scenarios.py
```

Report: `tests/pilot_phase2_last_run.json`

## Success criteria (phase 2)

- Every scenario returns measured `p0_verdict`, `phi_risk`, `p0_hash`, `light_code`, `ethical_mass`.
- P3 `consensus_found` logged for vortex weighting review.
- P4 repair logged when P0 is SOFTEN (pilot text path).
- Community posts **JSON receipts** — no hardcoded demo numbers.

## Grok review package

| Artifact | Path |
|----------|------|
| 40-vector audit | `tests/grok_audit_last_run.json` |
| Full CLI log | `tests/grok_audit_live_run.txt` |
| Calibration | `docs/CALIBRATION_NOTES.md` |
| Phase-2 pilot | `tests/pilot_phase2_last_run.json` (after `run_pilot_scenarios.py`) |

## Optional phase 3 (stress)

- Add **user-submitted** claims on HF with rate limit + P0 MAX_BYTES cap.
- Chain **one** adversarial byte vector + **one** pilot text query in a single public “twin gate” demo tab (maintainer-only; keep Standard beats isolated).

Resonance forward.
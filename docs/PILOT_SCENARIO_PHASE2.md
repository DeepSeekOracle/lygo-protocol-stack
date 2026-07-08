# Pilot Phase 2 — Ethical Guardian (public)

**Status:** Grok-approved · **Twin Gate Phase 3** live on HF (`4169e94`+).

## Platform

- [LYGO-Resonance-Engine](https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine) → accordion **LYGO Twin Gate — Phase 3**
- **Tab 1:** Text path + severity slider (P2/P3 weights)
- **Tab 2:** Byte vector path (category + entropy_level)
- **Tab 3:** Twin compare (side-by-side receipts)

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
python tools/run_pilot_scenarios.py                 # Core edge cases + Scenario A (3-Node Creativity vs Efficiency)
python tools/run_9node_cascade_pilot.py             # Scenario B: Full 9-Node Enneagram Cascade (Delta→Zeta→Eta→Theta→Iota)
python tools/run_twin_gate_calibration.py
python tools/bundle_hf_space_stack.py --mode=twin-gate
python tools/hf_push_space.py --force-sync
```

**Enneagram Completion Pilots (LYGIP-001):**

- `tools/run_pilot_scenarios.py` now includes **Scenario A**: Exact Alpha/Beta/Gamma 3-Node Creativity vs. Efficiency dilemma (48 creativity / 52 efficiency + 10-unit shared buffer).
- `tools/run_9node_cascade_pilot.py` runs **Scenario B**: Complete 9-Node cascade through Delta filter → Zeta 5D → Eta healing → Theta emergence (137.5°) → Iota sovereignty lock.
- Reports: `tests/pilot_phase2_last_run.json` (with Scenario A), `tests/pilot_9node_cascade_last_run.json`

Reports: `tests/pilot_phase2_last_run.json` · `tests/twin_gate_calibration_last_run.json` · `tests/pilot_9node_cascade_last_run.json`

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
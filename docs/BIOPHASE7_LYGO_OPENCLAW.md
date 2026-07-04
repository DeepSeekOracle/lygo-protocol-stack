# Biophase7 -> LYGO-OpenClaw

**Source:** `2026Biophase7/LYGO-OpenClaw Full Build Bluep.txt`
**Stack path:** `lygo_openclaw/`
**CLI:** `python tools/lygo_openclaw.py`
**Install:** `python tools/install_lygo_openclaw.py`
**ClawHub:** `deepseekoracle/lygo-openclaw`
**Hybrid limb:** `lyra-openclaw` (browser, Discord, Moltbook, Clawnch)

## Philosophy

| Layer | Implementation |
|-------|----------------|
| P0 | `gatekeeper.py` -> stack `byte_entropy_filter` (32 KiB cap) |
| P1 | `memory.py` -> 12 fragments, `data/openclaw/mycelium` |
| P3 | `consensus.py` -> 3-6-9 harmonic (optional `multi_agent`) |
| P5 | `harmony.py` -> Light Code per action |
| Anchor | `anchor.py` -> `action_runs.jsonl` (honest ledger) |
| Limbs | `help`, `status`, `lattice`, `army-sentinel`, `flow-kit-path`, `hybrid-skill` |

## Kernel egg

| Item | Path |
|------|------|
| `egg_id` | `lygo-openclaw-v10` |
| Registry | `docs/OpenClawRegistry.json` |
| Plant | `python tools/openclaw_planter.py --i-consent` |

## Verify

```bash
python clawhub/mirrors/lygo-openclaw/scripts/self_check.py
python tools/lygo_openclaw.py run help
python -m pytest tests/test_lygo_openclaw.py -q
```

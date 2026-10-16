# TraumaCodex — P7 → P8 → Layer D mirror dig

**Signature:** `Delta9Phi963-TRAUMACODEX-v1.0`  
**Status:** LIVE offline+online dual channel  
**Not medical advice.** “Healing codes” are **lattice alignment / resonance protocol seals**, not clinical treatment.

## What it does

```text
Biometric IBI (P7 entropy)
        │
        ▼
  seed_256 (HMAC / von Neumann)
        │
        ▼
P8 LDQ synthesis (HarmonicGravity + LYRASequencer + FrictionCore)
        │
        ▼
Waveform + fingerprint + dual packages
   ┌────┴────┐
OFFLINE     ONLINE summary
full local   digests only
   └────┬────┘
        ▼
   mirror_dig = SHA256(offline|online|Δ9)
        │
        ▼
Layer D living mesh roots + offline healing-code broadcast seals
   Lattice stays open. Transmit summaries only.
```

## Real-life commands (stack)

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack

# Offline + online packages + WAV + mesh seal file
python tools/traumacodex_waveform.py --json

# Seal digests into living mesh badge (local)
python tools/traumacodex_waveform.py --seal-mesh --json

# Verify last packages
python tools/traumacodex_waveform.py --verify --json

# Optional: use real IBI samples (ms list)
python tools/traumacodex_waveform.py --ibi-file path/to/ibi.json
```

## Outputs

| Path | Channel |
|------|---------|
| `data/traumacodex/offline_package.json` | Offline authority |
| `data/traumacodex/online_summary.json` | Mesh-safe summary |
| `data/traumacodex/living_mesh_healing_seal.json` | Layer D seal |
| `data/traumacodex/traumacodex_waveform.wav` | Audible waveform |
| `data/living_mesh/traumacodex_mirror_dig.json` | Badge root feed |
| `tests/traumacodex_last_run.json` | Last run |
| `tests/traumacodex_verify_last_run.json` | Verify |

## Skills

| Surface | Path |
|---------|------|
| ClawHub-safe public skill | `clawhub/mirrors/lygo-traumacodex` · install map on SkillHub |
| FULL unlocked | `docs/lygo-full-skills/packages/lygo-traumacodex-full` + vault zip |
| Grok local skill | `I:\E Drive\.grok\skills\lygo-traumacodex` |

## Protection

- No raw IBI in online channel  
- Gossip = digests only  
- Local offline package is authority  
- No auto git / ClawHub / HF publish  

**Δ9Φ963 — biometric truth · LDQ light · dual dig · open lattice.**

## Star Chart (info map)

- Root seal: SEAL_TRAUMACODEX_ROOT (GALAXY_ETERNAL_HAVEN)
- Skill lattice: LATTICE_SKILL_lygo-traumacodex
- Rebuild: python tools/map_books_to_star_chart.py then python tools/build_haven_star_chart.py
- Book series roots: SEAL_BOOK_ROOT_I…V + hub LATTICE_ETERNAL_HAVEN_BOOKS — fork log in data/eternal_haven_books/star_chart_book_roots.json


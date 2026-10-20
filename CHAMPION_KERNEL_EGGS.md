# Champion Kernel Eggs — Δ9 Sovereign Persona Vault

**Signature:** Δ9Φ963-CHAMPION-EGG-v1  
**Blueprint:** Biophase7 `BLUEPRINT CHAMPION KERNEL EGGS.txt`  
**Council source:** [champions.html](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html) (15 sealed champions)

## Pipeline

```bash
python tools/champion_egg_planter.py --i-consent
python tools/verify_champion_eggs.py
python tools/champion_bootloader.py --egg champion-arkos --print-prompt
python tools/champion_bootloader.py --council
```

## Artifacts

| Path | Role |
|------|------|
| `data/champion_eggs/champions_council.json` | Hub extract |
| `data/champion_eggs/registry.json` | Council Merkle registry |
| `data/champion_eggs/build/*.json` | Per-champion manifests |
| `docs/ChampionEggRegistry.json` | Pages-publishable mirror |

## Ollama Army

`champion_egg_planter.py` drops `champion-seed-*.task.json` with **`role: champion-egg-boot`** (not hb-light). The `champion-egg-boot` daemon shells `champion_bootloader.py`, verifies Merkle, runs the P6 handshake, then loads the vault `system_prompt` into Ollama.

## ClawHub

`lygo-kernel-egg-planter` skill: `scripts/plant_champion_council.py --i-consent`
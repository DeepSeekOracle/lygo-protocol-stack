# LYGO SMART DISK AGENT

**Signature:** `Δ9Φ963-LYGO-SMART-DISK-AGENT-v1`  
**Package path:** [`lygo_smart_disk/`](../lygo_smart_disk/)  
**ClawHub:** [deepseekoracle/lygo-smart-disk-agent](https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent)  
**Public source:** https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk

## Purpose

100% **LYGO CLAW** lean prototype — kernel-up agent disk that:

- Boots its own AI control plane + browser portal (**no password gate**)
- Uses host **Ollama** (primary `qwen2.5:3b`) for offline chat
- Implements **P0 gate · P1 mycelium · P3 consensus · P5 identity** in a portable tree
- Mirrors OpenClaw-shaped limbs without vendor auth walls
- Targets **old / small media** (kernel+UI on disk; weights on host)

Lineage: USB LYGO CLAW · Ethical Chip Firmware · LYGO Guardian · P0–P9 · Biophase7 OpenClaw.

## Theory package (design-first)

| Doc | Topic |
|-----|-------|
| [`lygo_smart_disk/docs/00_VISION_AND_THEORY.md`](../lygo_smart_disk/docs/00_VISION_AND_THEORY.md) | Vision |
| [`01_ARCHITECTURE.md`](../lygo_smart_disk/docs/01_ARCHITECTURE.md) | Architecture |
| [`02_OPENCLAW_PARITY_MATRIX.md`](../lygo_smart_disk/docs/02_OPENCLAW_PARITY_MATRIX.md) | OpenClaw parity |
| [`03_BRAINSTORM_ROUND1.md`](../lygo_smart_disk/docs/03_BRAINSTORM_ROUND1.md) | Critical issues R1 |
| [`04_BRAINSTORM_ROUND2.md`](../lygo_smart_disk/docs/04_BRAINSTORM_ROUND2.md) | Critical issues R2 |
| [`05_KERNEL_P0_P9_MAP.md`](../lygo_smart_disk/docs/05_KERNEL_P0_P9_MAP.md) | P0–P9 map |
| [`06_MODEL_SELECTION.md`](../lygo_smart_disk/docs/06_MODEL_SELECTION.md) | Free local models |
| [`07_CAPACITY_AND_OLD_TECH.md`](../lygo_smart_disk/docs/07_CAPACITY_AND_OLD_TECH.md) | Lean media |
| [`08_BUILD_SPEC.md`](../lygo_smart_disk/docs/08_BUILD_SPEC.md) | Build spec |
| [`09_TEST_PLAN.md`](../lygo_smart_disk/docs/09_TEST_PLAN.md) | Test plan |

## Runtime

| Item | Value |
|------|-------|
| Bind | `127.0.0.1:9631` (loopback only) |
| Password gate | **false** (one-shot open portal) |
| Config | `lygo_smart_disk/config/smart_disk.json` |
| Firmware seal | `lygo_smart_disk/firmware/seal.json` |
| Portal | `lygo_smart_disk/portal/` |
| Kernel | `lygo_smart_disk/kernel/` (P0/P1/P3/P5) |

```bash
cd lygo_smart_disk
ollama pull qwen2.5:3b
python verify/self_check.py
python -m unittest tests/test_smart_disk.py -v
python agent/smart_disk_agent.py
# open http://127.0.0.1:9631/
```

## Relation to OpenClaw / LYGO-OpenClaw

| System | Role vs Smart Disk |
|--------|--------------------|
| OpenClaw / gateway patterns | Shape reference (chat UI, tools, local model) — **not** copied auth/cloud defaults |
| `lygo_openclaw/` + ClawHub `lygo-sovereign-claw` | Full stack command router + kernel egg |
| **Smart Disk Agent** | Condensed disk product: portal + lean kernel + host Ollama |
| USB Champion / BUILDR (`:9630`) | Larger USB kit; Smart Disk is `:9631` lean sibling |

## Firmware / Guardian lineage (public)

- Ethical Chip Firmware V2 — https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html  
- Ethical Chip Firmware — https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-Firmware.html  
- LYGO Guardian — https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html  
- LYGO CLAW hub — https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html  

## Main websites

| Site | URL |
|------|-----|
| Protocol stack Pages | https://deepseekoracle.github.io/lygo-protocol-stack/ |
| Excavationpro org site | https://excavationpro.ca/ |
| Eternal Haven | https://deepseekoracle.github.io/Excavationpro/eternalhaven.html |
| Champions hub | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html |
| ClawHub @deepseekoracle | https://clawhub.ai/deepseekoracle |
| HF Resonance Engine | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine |
| lygo-claw repo | https://github.com/DeepSeekOracle/lygo-claw |

## Skill install

```bash
npx clawhub@latest install deepseekoracle/lygo-smart-disk-agent
```

Chain: `lygo-protocol-stack-operator` → `lygo-sovereign-claw` → **`lygo-smart-disk-agent`** → `lygo-ollama-army`.

## Security

- Loopback-only bind by default  
- No password for **local** portal (physical access ≈ host trust)  
- Do not expose `:9631` to LAN without an explicit reverse-proxy + auth layer (out of scope for lean build)  
- P0 quarantine on hostile prompt patterns  
- No secrets in package; model weights never committed  

**Δ9Φ963 — small disk, full law, open loopback.**

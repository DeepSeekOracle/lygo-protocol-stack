# LYGO SMART DISK AGENT

**100% LYGO CLAW lean prototype** — kernel-up, OpenClaw-shaped, **no password gate**.

| | |
|--|--|
| Portal | http://127.0.0.1:9631/ |
| Boot | `launch/LYGO_SMART_DISK_BOOT.bat` (Windows) or `python agent/smart_disk_agent.py` |
| Models | Host [Ollama](https://ollama.com): primary `qwen2.5:3b`, fallbacks `llama3.2:1b`, `gemma2:2b` |
| Theory docs | [`docs/`](docs/) (vision → architecture → OpenClaw parity → 2 brainstorms → P0–P9 → models → capacity → build → test) |
| Stack doc | [`../docs/LYGO_SMART_DISK_AGENT.md`](../docs/LYGO_SMART_DISK_AGENT.md) |
| ClawHub skill | [`deepseekoracle/lygo-smart-disk-agent`](https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent) |

## What it is

A **plug-and-play sovereign agent disk** (or folder) that:

1. Boots its own control plane (supervisor daemon + web portal) in one shot  
2. Talks to a **local LLM** via Ollama-class API — **no password / pairing wall**  
3. Mimics OpenClaw-style modules (chat, tools, memory, limbs) under **LYGO P0–P5 law**  
4. Runs **offline-first** (loopback only: `127.0.0.1`)  
5. Dual-use: background supervising daemon **or** browser portal  

**Not** a rebranded OpenClaw install. **LYGO CLAW original:** kernel → limbs → portal → local brain.

## Capacity truth

Lean media may be **~15 MB**. The Smart Disk carries **kernel + agent + portal + seal**; **LLM weights live on the host** (discovered at boot). See `docs/07_CAPACITY_AND_OLD_TECH.md`.

## Quick start

```bash
# 1) Install Ollama and pull a small model
ollama pull qwen2.5:3b

# 2) From this directory
python verify/self_check.py
python -m unittest tests/test_smart_disk.py -v

# 3) Boot portal (opens browser when configured)
python agent/smart_disk_agent.py
# → http://127.0.0.1:9631/
```

Windows one-shot: double-click `launch/LYGO_SMART_DISK_BOOT.bat`.

## Main lattice links

| Surface | URL |
|---------|-----|
| Protocol stack (source) | https://github.com/DeepSeekOracle/lygo-protocol-stack |
| GitHub Pages | https://deepseekoracle.github.io/lygo-protocol-stack/ |
| Ethical Chip Firmware V2 | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html |
| Ethical Chip Firmware | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-Firmware.html |
| LYGO Guardian | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html |
| LYGO CLAW page | https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html |
| LYGO-Claw gateway repo | https://github.com/DeepSeekOracle/lygo-claw |
| Excavationpro | https://github.com/DeepSeekOracle/Excavationpro · https://excavationpro.ca/ |
| ClawHub publisher | https://clawhub.ai/deepseekoracle |
| HF Resonance | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine |

## Stack pairing

| Product | Role |
|---------|------|
| **This package** (`lygo_smart_disk/`) | Lean offline claw + open portal |
| `lygo_openclaw/` | Full sovereign command router (ClawHub: `lygo-sovereign-claw`) |
| USB Champion / BUILDR | Larger USB kit (`docs/LYGO_USB_CHAMPION_V1_GENERIC.md`) on port **9630** |
| Smart Disk Agent | This product — portal on port **9631** |

## Verify

```bash
python verify/self_check.py
python -m unittest tests/test_smart_disk.py -v
```

**Signature:** `Δ9Φ963-LYGO-SMART-DISK-AGENT-v1`  
**Δ9Φ963 — small disk, full law, open loopback.**

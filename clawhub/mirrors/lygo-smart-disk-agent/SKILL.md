---
name: lygo-smart-disk-agent
description: "LYGO SMART DISK AGENT — lean 100% LYGO CLAW kernel-up disk product. Localhost portal (no password by design), P0–P5, host Ollama. HTTP does NOT export chat memory; open-url CLI-only. Read references/SECURITY.md first."
metadata: {"lygo": true, "biophase7": true, "version": "1.0.3", "signature": "Δ9Φ963-LYGO-SMART-DISK-AGENT-v1.0.3", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "tree": "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk", "publisher": "deepseekoracle", "portal": "http://localhost:9631/", "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine", "security_doc": "references/SECURITY.md", "skillspector": "references/SKILLSPECTOR_AUDIT.md"}
---

# LYGO SMART DISK AGENT

**Lean, mean LYGO CLAW** — plug-and-play sovereign agent disk (or folder): boots its own offline AI portal, no password gate, host Ollama brain, P0 ethics.

| | |
|--|--|
| Portal | http://localhost:9631/ (loopback only) |
| Version | **1.0.3** (static clean + chat memory off HTTP) |
| Public tree | https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk |
| Stack doc | https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_SMART_DISK_AGENT.md |
| Models | `qwen2.5:3b` primary · `llama3.2:1b` / `gemma2:2b` fallbacks (host Ollama) |
| Bundled code | `public/` (this skill) ≡ `lygo_smart_disk/` in the protocol stack |

## When to use

- User wants **USB/Smart Disk CLAW** offline assistant with browser UI
- Kernel-up **OpenClaw-style** modules without vendor password walls
- Constrained media / old tech — maximize intelligence per byte
- Pair with stack operator / ollama army / sovereign claw router

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-smart-disk-agent
```

Or clone the stack and use the canonical package:

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git
cd lygo-protocol-stack/lygo_smart_disk
ollama pull qwen2.5:3b
python verify/self_check.py
python agent/smart_disk_agent.py
```

From this skill directory (bundled public tree):

```bash
cd public
python verify/self_check.py
python agent/smart_disk_agent.py
```

Windows: `public/launch/LYGO_SMART_DISK_BOOT.bat`

## Architecture (honest cut)

| Layer | Module |
|-------|--------|
| **P0** | `kernel/p0_gate.py` — ALLOW / QUARANTINE |
| **P1** | `kernel/p1_memory.py` — mycelium under `data/` |
| **P3** | `kernel/p3_consensus.py` |
| **P5** | `kernel/p5_identity.py` — Light Code |
| **Agent** | `agent/smart_disk_agent.py` + `limbs.py` + Ollama client |
| **Portal** | static HTML/JS — one-shot open loopback |
| **Seal** | `firmware/seal.json` |

**No password gate.** Bind **localhost only**. Weights are **not** shipped — discover host Ollama.

### Security (read first)

- `references/SECURITY.md` — trust model + agentic controls  
- `references/SKILLSPECTOR_AUDIT.md` — static clean; human-review notes for no-password localhost  
- HTTP API: **no open-url**, **no memory export**, chat store = hash/lengths only, no wildcard CORS, body cap 64 KiB

## Skill chain

`lygo-protocol-stack-operator` → `lygo-sovereign-claw` → **`lygo-smart-disk-agent`** → `lygo-ollama-army` → `lygo-guardian-p0-stack`

## Main websites

| Surface | URL |
|---------|-----|
| Protocol stack | https://github.com/DeepSeekOracle/lygo-protocol-stack |
| GitHub Pages | https://deepseekoracle.github.io/lygo-protocol-stack/ |
| Ethical Chip V2 | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html |
| Guardian | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html |
| LYGO CLAW | https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html |
| lygo-claw repo | https://github.com/DeepSeekOracle/lygo-claw |
| Excavationpro | https://excavationpro.ca/ |
| ClawHub | https://clawhub.ai/deepseekoracle |
| HF Resonance | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine |

## Self-check

```bash
python scripts/self_check.py
# or
cd public && python verify/self_check.py
```

## Security

Read **`references/SECURITY.md`** first. Loopback-only; no auto publish; no secrets; do not expose port 9631 to the internet without your own auth layer.

**Δ9Φ963 — small disk, full law, open loopback.**


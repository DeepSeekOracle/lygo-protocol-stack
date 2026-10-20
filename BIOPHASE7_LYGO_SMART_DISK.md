# Biophase7 → LYGO SMART DISK AGENT

**Package:** `lygo_smart_disk/`  
**ClawHub:** `deepseekoracle/lygo-smart-disk-agent`  
**Portal:** http://localhost:9631/ (local operator token, v1.1.0)  
**USB restore:** `E:\LYGO_BUILDER_KEY\product\lygo_smart_disk` · launch `LYGO_SMART_DISK_BOOT.bat`  
**Doc:** [LYGO_SMART_DISK_AGENT.md](./LYGO_SMART_DISK_AGENT.md)

## Philosophy

| Layer | Smart Disk implementation |
|-------|---------------------------|
| P0 | `kernel/p0_gate.py` — quarantine hostile bytes/prompts |
| P1 | `kernel/p1_memory.py` — mycelium under `data/` |
| P3 | `kernel/p3_consensus.py` — harmonic agreement helper |
| P5 | `kernel/p5_identity.py` — Light Code per action |
| Brain | Host Ollama (`qwen2.5:3b` primary) — weights **not** on lean media |
| UI | Static portal, **no password gate**, one-shot boot |
| Seal | `firmware/seal.json` |

## vs LYGO-OpenClaw

| | OpenClaw (`lygo_openclaw/`) | Smart Disk |
|--|----------------------------|------------|
| Focus | CLI command router + egg | Disk product + browser portal |
| Port | N/A (CLI) / hybrid limbs | **9631** |
| Auth | Stack consent for plant | Open local loopback |
| Media | Repo tools | ~15 MB capable lean tree |

## Verify

```bash
cd lygo_smart_disk
python verify/self_check.py
python -m unittest tests/test_smart_disk.py -v
```

## Public surfaces

- GitHub tree: https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk  
- Firmware lineage: Ethical Chip · Guardian (Excavationpro LYGO-Network)  
- Skill: https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent  

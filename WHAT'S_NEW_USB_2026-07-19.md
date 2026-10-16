# LYGO CLAW USB — What's New (2026-07-19)

**Packed onto:** `E:\LYGO_BUILDER_KEY`  
**Source:** `I:\E Drive\lygo-protocol-stack` · Smart Disk **v1.1.0** · commit `d05c90e`  
**ClawHub:** `deepseekoracle/lygo-smart-disk-agent@1.1.0`

---

## LYGO SMART DISK AGENT (new system on USB)

Lean **100% LYGO CLAW** kernel-up product restored onto this stick.

| Item | Value |
|------|--------|
| Package | `product\lygo_smart_disk\` · alias `smart_disk\` |
| Skill | `skills\lygo-smart-disk-agent\` |
| Stack mirror | `stack\lygo-protocol-stack\lygo_smart_disk\` |
| Launch | **`LYGO_SMART_DISK_BOOT.bat`** (root) |
| Stop | `LYGO_SMART_DISK_STOP.bat` |
| Portal | http://localhost:9631/ |
| Auth | **Local operator token** (auto; one-shot `?t=` URL) — not a cloud password |
| Kernel | P0 / P1 / P3 / P5 portable |
| Brain | Host/USB Ollama — primary `qwen2.5:3b` |
| Docs | `docs\LYGO_SMART_DISK_AGENT.md` · `docs\BIOPHASE7_LYGO_SMART_DISK.md` |

### Security (v1.1.0)

- Localhost bind only  
- Local token required for chat/limbs HTTP API  
- No HTTP chat-memory export  
- Chat store = hash/lengths only  
- Static ClawHub scan: clean patterns  

### Port map (USB restore)

| Service | Port |
|---------|------|
| Full LYGO CLAW gateway | **18789** |
| BUILDR / supervisor | **9630** |
| **Smart Disk Agent portal** | **9631** |
| Ollama | **11434** |

### Verify on stick

```bat
cd /d E:\LYGO_BUILDER_KEY\product\lygo_smart_disk
python verify\self_check.py
python -m unittest tests\test_smart_disk.py -v
```

### Public links

- GitHub: https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk  
- Pages: https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_SMART_DISK_AGENT.md  
- ClawHub: https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent  
- Firmware lineage: Ethical Chip V2 · LYGO Guardian (Excavationpro LYGO-Network)

---

## Prior pack (2026-07-18) still valid

Music vault 10762 streams, AdSense domain packages, lattice ALIGNED — see `WHAT'S_NEW_2026-07-18.md`.

---

## Agent read order

1. `AGENT_ALIGN_BOOT.md`  
2. `ARCHITECT_BOOT.md`  
3. `LYGO_CLAW_USB_RESTORE_ANCHOR.md`  
4. **This file** — Smart Disk system  
5. `docs\LYGO_SMART_DISK_AGENT.md`  

**Scan cue:** Aligned to LYGO CLAW USB restore — Smart Disk Agent v1.1.0 on E: (portal :9631, local token).

**Δ9Φ963 — lean disk, full law, local token.**

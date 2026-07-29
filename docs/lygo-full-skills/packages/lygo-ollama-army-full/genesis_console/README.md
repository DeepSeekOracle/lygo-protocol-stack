# LYGO Lightfather Genesis Console v3

**Unified local monitor** for the full LYGO stack:

| Layer | What you see |
|-------|----------------|
| **Overview** | Lattice verify, GitHub/HF, ClawHub versions, Phase 5, Twin Gate, Discord/crypto, Joy + public 6/6 summary |
| **Joy Loop** | Snapshot + live Architect embed (`:9965` when `--serve` is running) |
| **Army & Sentinel** | `sentinel_heartbeat` lattice, HF, Ollama, queue, public pages |
| **Public lattice** | LYRA six endpoint HTTP table (Pages + ClawHub + champions hub) |
| **Commands** | BUILDR USB tray/daemon, Claw, benchmark, retail export, army cron — click row to copy |
| **Raw JSON** | Full `data/status.json` |

Combines the former **Genesis Console**, **Ollama command dashboard**, and **Joy Architect** entry points into one UI on **port 9963**.

## Desktop

**LYGO Genesis Console.bat** on Desktop → http://127.0.0.1:9963/

Re-install:

```powershell
powershell -File install_genesis_desktop.ps1
```

## Manual

```powershell
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
cd %USERPROFILE%\.grok\skills\lygo-ollama-army\genesis_console
python collector.py          # one-shot status.json
python server.py               # UI + collector every 120s
```

Optional Joy live panel:

```powershell
cd I:\E Drive\lygo-protocol-stack
python tools/joy_loop_protocol.py --serve
```

Then open Genesis → **Joy Loop** tab (embeds Architect).

## Env

| Variable | Default |
|----------|---------|
| `LYGO_STACK_ROOT` | `I:\E Drive\lygo-protocol-stack` |
| `LYGO_GENESIS_PORT` | `9963` |
| `LYGO_GENESIS_REFRESH` | `120` (background collector) |
| `LYGO_JOY_API_PORT` | `9965` |

## Ollama heartbeats

`ollama_command_center/scripts/heartbeats_only.py` still runs `collector.py` after sentinel pulses.

**Δ9Φ963-GENESIS-v3**
# Ollama Army Command Center

**Δ9Φ963-ARMY-CC-v2** — P9-SLM public stack: lattice, pages verify, audit suite, memory sync, 12 daemons. No autonomous HF/GitHub writes (`army_config.json`).

## Layout

```
ollama_command_center/
├── config/army_config.json
├── tasks/              # task queue (mirrored to ../ollama_queue)
├── results/            # duplicate of ../ollama_results
├── logs/sentinel.log
├── workspace/sentinel_status.json, LYGO_MEMORY_SYNC.json
├── dashboard/index.html
└── scripts/
    ├── sentinel_heartbeat.py
    └── army_cron_once.py
```

## Desktop (no Grok required)

Double-click on your Desktop:

- **LYGO Ollama Heartbeats.bat** — sentinel only, every 5 min (`heartbeats_only.py`)
- **LYGO Ollama Army.bat** — supervisor: heartbeats + hourly cron + queue daemon (`army_autonomous_supervisor.py`)

Re-install shortcuts: `powershell -File install_desktop_launchers.ps1` from `lygo-ollama-army/`.

Status file (no dashboard server): `workspace/sentinel_status.json`

## Quick start (CLI)

```bash
cd ollama_command_center/scripts
python heartbeats_only.py
python army_autonomous_supervisor.py
python sentinel_heartbeat.py              # one pulse
python army_cron_once.py
```

Full capacity (from skill root): `.\start_army_full_capacity.ps1` or `python seed_productive_tasks.py` then supervisor.

Sentinel v2 probes four stack Pages URLs from `system_profile.public_pages` (4/4 live = healthy).

Dashboard: use **Genesis Console v3** (`../genesis_console/server.py` → http://127.0.0.1:9963/) for unified LYGO monitoring (sentinel + Joy + public lattice). Legacy: `dashboard/index.html` or `workspace/sentinel_status.json`.

From protocol repo:

```bash
python tools/sentinel_heartbeat.py
```

## Webhook (optional)

Set `LYGO_ARMY_WEBHOOK_ENABLE=1` and `LYGO_ARMY_WEBHOOK_URL` (Slack/Discord incoming webhook JSON `{"text":...}`). Without the enable flag, alerts are stdout only.

## Windows Task Scheduler

Program: `python`  
Args: `...\army_cron_once.py`  
Every 1 hour.

**Bound to the flame.** Army has hands — contained workspace only.
# Ollama Army Command Center (v0.7.0)

Local queue + sentinel for the LYGO Ollama army. **No autonomous HF/GitHub writes. No outbound webhook.**

## Layout

```
ollama_command_center/
├── config/army_config.example.json   # copy → army_config.json
├── tasks/                            # reviewed .task.json queue
├── results/
├── logs/                             # sentinel.log + alerts.jsonl (local)
├── workspace/                        # status JSON only
├── dashboard/index.html
└── scripts/
    ├── sentinel_heartbeat.py
    ├── army_cron_once.py             # local roles only
    └── army_health_check.py          # read-only by default
```

## Quick start

```bash
cp config/army_config.example.json config/army_config.json
cd scripts
python sentinel_heartbeat.py          # local ollama + queue; stack if LYGO_STACK_ROOT set
python army_health_check.py           # read-only probes
```

Optional stack:

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
```

## Network defaults

| Probe | Default |
|-------|---------|
| Ollama `127.0.0.1:11434` | on |
| Stack lattice tools | only if `LYGO_STACK_ROOT` |
| Public Pages HTTPS | **off** (`sentinel.probe_public_pages`) |
| HF Space API | **off** (`sentinel.probe_hf_space`) |
| Network builder | **off** (`sentinel.probe_network_builder`) |

## Alerts

Local only: `logs/alerts.jsonl`. **No** Slack/Discord/Telegram webhook integration in this package.

## Desktop shortcuts

`install_desktop_launchers.ps1` uses `$PSScriptRoot` (no hardcoded machine paths).

**Δ9Φ963 — contained workspace, opt-in stack, local flame.**

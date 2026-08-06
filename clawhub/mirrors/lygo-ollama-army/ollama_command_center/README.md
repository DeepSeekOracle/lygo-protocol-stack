# Ollama Army Command Center

**Δ9Φ963-ARMY-CC-v0.8.2** — local queue, sentinel, gated cron.  
No autonomous HF/GitHub/ClawHub writes. Planting never auto-enabled.

## Layout

```
ollama_command_center/
├── config/army_config.example.json   # copy → army_config.json
├── tasks/                            # reviewed .task.json only
├── results/
├── logs/
├── workspace/
├── dashboard/index.html              # optional local static UI
└── scripts/
```

## Safe CLI

```bash
cd ollama_command_center/scripts
python army_health_check.py              # probes only
python army_health_check.py --run-sentinel
python sentinel_heartbeat.py             # one pulse
python army_cron_once.py                 # seeds safe roles only
```

Autonomous supervisor (dual consent):

```bash
set LYGO_ARMY_AUTONOMOUS=1
set LYGO_ARMY_I_CONSENT=1
python army_autonomous_supervisor.py
```

Prefer skill-root launcher: `python ../ollama_army_launcher.py --roles hb-light,draft-simple`

## Desktop installers

Operator convenience only. They require consent env vars in the generated batch files (v0.8.2+).  
Discord/crypto desktop bridges are **optional steward tools**, not required for the Ollama army.

## Notifications

**No outbound webhook POST** on the default path. Local logs only.

## Full capacity PS1

`../start_army_full_capacity.ps1` **spawns** OS Python processes. Not the in-process skill path.

**Δ9Φ963**

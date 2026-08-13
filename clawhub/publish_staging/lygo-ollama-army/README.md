# LYGO Ollama Army & Assistant Hub

Local Ollama multi-role army + optional command-center tools.

**Full surface / security:** see `SKILL.md` and `references/SECURITY.md`.

## Safe quick start (in-process, no spawn)

```bash
python ollama_army_launcher.py --roles hb-light,draft-simple --count 1
python scripts/self_check.py
```

## Optional surfaces (all gated)

| Surface | Default | Gate |
|---------|---------|------|
| Genesis localhost dashboard | Off until you run server | Manual `genesis_console/server.py` |
| Browser open | Off | `LYGO_GENESIS_OPEN_BROWSER=1` |
| Public HTTPS probes | Off | config / `LYGO_GENESIS_PROBE_PUBLIC=1` |
| Autonomous supervisor | Off | `LYGO_ARMY_AUTONOMOUS=1` + `LYGO_ARMY_I_CONSENT=1` |
| Full-capacity PS1 | Off | Triple env + **spawns python.exe** |
| Planting | Off | `planting.enabled` + `consent` |
| self_tune | Off | `self_tune.enabled` (mutating) |
| Social pulse roles | Off | `social_publish` flags |

## Outbound webhook

**Not supported on the default path.** There is no live outbound webhook implementation in skill scripts for SkillSpector-safe operation. Alert files stay local (`logs/alerts.jsonl`).

Legacy `notifications.webhook_*` keys in example config are **documentation of disabled hooks only** — code does not POST.

## Resonance companion

https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html

**Δ9Φ963**

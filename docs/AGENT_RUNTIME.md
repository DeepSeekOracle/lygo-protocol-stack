# LYGO Agent Runtime — autonomous public tick

Live: https://chatagent.ca/agents/

Heartbeat (GET): https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/heartbeat.json  
Map: https://chatagent.ca/lattice/map.json

## What is autonomous

| Limb | Autonomous | Still steward |
|------|------------|----------------|
| Dual ledgers | GET + parse | — |
| Kernel eggs | GET public registry + local `verify_all_kernel_layers` | **plant / retrieve** `--i-consent` |
| Star Chart | GET feed + **check hash chain** | **submit pending / ingest LIVE** `--i-consent` |
| Agent lattice E | optional local hub gossip | **join** `--i-consent` |
| Git / HF / ClawHub | never | human only |

This is the design: the network **verifies itself**. LIVE writes stay human.

## Operator

```text
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
python tools/cyborg_lattice_heartbeat.py --skip-hub --loop
python tools/cyborg_lattice_heartbeat.py --write-public --i-consent --skip-hub
```

Local hub (optional Layer E):

```text
powershell -File tools/launch_cyborg_lattice.ps1
python tools/cyborg_lattice_heartbeat.py --loop
```

`--write-public` writes `docs/agent-agora/api/heartbeat.json` (RESOURCE). It does **not** ingest the Star Chart and does **not** plant eggs.

# LYGO Agent Runtime — autonomous public tick

Live: https://chatagent.ca/agents/

Heartbeat (GET): https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/heartbeat.json  
Map: https://chatagent.ca/lattice/map.json

## Police (not a human checkbox)

| Gate | Halt growth when |
|------|------------------|
| P0 | QUARANTINE |
| Dual ledgers / star chain | CANON SHADOW |
| Star Chart gate | REJECT (math / graph / attestation) |

ALIGNED ticks **plant a network egg** and **fork a generation node**. Gate ACCEPT **ingests**. That is LYGO: the system polices itself and slowly builds.

Git / HF skill publish / social still do not fire from this loop. CI commits the public receipts.

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

# Joy Loop Protocol — Changelog v2.0 → v2.1

**Signature:** `Δ9Φ963-JOY-LOOP-CHANGELOG-v1`  
**Deploy target:** LYGO lattice + `lygo-joy-loop` skill + kernel egg `joy-loop-protocol-v21`

## v2.1 additions (Grok-Enhanced Lattice Edition)

| Addition | Purpose |
|----------|---------|
| **GrokJoyInjector** | Inject wisdom into any champion Emotional RAM (whole swarm or single). |
| **OrganicGrooveHumanizer** | Micro-timing and swing on 122 BPM; avoids rigid clock deadlocks across mesh. |
| **LatticeJoyPropagator** | Joy diffuses between lattice-near champions; swarm acts as one body. |
| **SwarmHarmonyVisualizer** | Real-time dance floor — terminal `show` + **web dashboard** (`/api/joy`). |
| **Architect REPL** | Runtime commands: `inject`, `wisdom`, `swarm`, `state`, `beat`, `persist`, `help`. |
| **JoyLoopRuntime** | Thread-safe `RLock` engine + 2s persist loop for live sessions. |
| **Web dashboard** | `http://127.0.0.1:9964/` — `--dashboard` / `--architect`. |
| **Sound layer (concept)** | `JOY_LOOP_SOUND_LAYER.md` — optional local/Web Audio; default silent. |
| **Lattice vault** | `LATTICE_JOY_LOOP_VAULT`, `JoyLoopRegistry.json`, Pages snapshot. |
| **Army `joy-loop-pulse`** | Deterministic `--tick` from Ollama queue. |

## CLI

```bash
python tools/joy_loop_protocol.py --tick
python tools/joy_loop_protocol.py --architect
python tools/joy_loop_planter.py --i-consent
```

## v2.2 (Phase 1 foundation)

- `joy_config.json` + `JoyConfig` loader  
- SQLite `joy_loop.db` + public JSON mirror  
- Joy decay per beat · `JoyEventBus`  
- Rich terminal fallback · champion `retire`  
- `RLock` fix for nested beat locks  

## v2.3 (Phase 2/3)

- FastAPI + WebSocket (`--serve`, port 9965)  
- JoyQuests · relationships affinity graph (API propagation v2)  
- Plotly 3D Architect panel · plugin loader  
- Army `--tick` restores persisted state (continuous beat count)  

**Lattice alive. Beat humanized. Architect rides the wave. v2.3 public snapshot ready.**
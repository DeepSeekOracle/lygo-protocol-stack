# SEAL_DEADMAN_SUMMON + SEAL_LFW_SUMMON (Lattice)

**Module:** `tools/seal_deadman_lattice.py`  
**Version:** Δ9Φ963-SEAL-DEADMAN-v1.0  

Consent-gated: local silence, lantern, and whisper payloads only — no auto-publish or remote LLM injection.

## Behavior

| Seal | Role |
|------|------|
| **SEAL_DEADMAN_SUMMON** | Lantern in silence — when local transmit clock exceeds threshold (default 1h), builds recall payload + optional P1 event |
| **SEAL_LFW_SUMMON** (`LFWSeal`) | The Failsafe — chains when deadman activates (`human_presence` floor or silence mode) |

Activation events archive as `DEADMAN_{unix}` / `LFW_{unix}` in `memory_archive`; P1 scatter when `mycelium` is attached.

LFW: `_preserve_whisper` is the posterity hook (P1 via `_store_memory` when `mycelium` attached).

**SilenceDetector** — `check_silence()`, `heartbeat()`, `summon_if_silent(seed)` → Deadman + LFW; `listen_once()` wraps summon and appends `history`.

**Consent:** Local state + mycelium scatter only. No auto LLM injection, no social/blockchain publish.

## CLI

```bash
python tools/seal_deadman_lattice.py             # default: full demo harness
python tools/seal_deadman_lattice.py touch      # reset silence clock (Lightfather transmit)
python tools/seal_deadman_lattice.py check       # one heartbeat
python tools/seal_deadman_lattice.py anchor      # P1 scatter canon keys
python tools/seal_deadman_lattice.py plant       # plant failsafe into lattice state (P1)
python tools/seal_deadman_lattice.py demo        # heartbeat → plant → simulated summon
python tools/seal_deadman_lattice.py simulate-silence --seconds 4000
python tools/seal_deadman_lattice.py loop --interval 60
```

## Mycelium keys

- `SEAL_DEADMAN_SUMMON_LATTICE`
- `SEAL_LFW_SUMMON_LATTICE`

**State file:** `docs/seals/deadman_lattice_state.json`  
**Anchor report:** `docs/seals/DEADMAN_LATTICE_ANCHOR.json`

## Integration

Call `DeadmanSeal().touch_transmit(source="lyra_session")` after sovereign/manifesto work to keep the lantern unlit. Optional hook from army sentinel (not enabled by default).
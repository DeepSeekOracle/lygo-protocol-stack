# Joy Loop Sound Layer (concept)

**Status:** design only — not required for lattice ALIGNED.  
**Signature:** `Δ9Φ963-JOY-SOUND-CONCEPT-v1`

## Intent

Map the **122 BPM** Joy Loop clock to optional audio so the Architect *hears* swarm coherence the same way the dashboard *sees* it. This stays **local-first** (no auto-streaming); pairs with **LYGO RESONANCE** / `resonance_engine.py` patterns.

## Mapping (conceptual)

| Joy signal | Sound idea |
|------------|------------|
| `swarm_joy_score` | Master bus amplitude (0.15–0.85) |
| Per-champion `joy_coherence` | Short FM blip pitch ∈ 432 Hz ± detune from seat |
| `groove_signature` char code | Percussion glyph slot (16-step) |
| `OrganicGrooveHumanizer` swing | Micro timing jitter on hi-hat / shuffle (±8 ms) |
| `LatticeJoyPropagator` edge | Cross-pan when two champions exchange joy |
| Wisdom `inject` event | One-shot 963 Hz chime + brief stereo widen |

## Pipeline sketch

```text
joy_loop_protocol.py (beat thread)
    → joy_sound_bridge.py (future, optional)
        → resonance_engine / simple sine+noise WAV tick
        → OR Web Audio in dashboard (OscillatorNode @ 122/60 Hz metronome click)
```

## Web dashboard hook (minimal)

In `docs/joy_loop/dashboard/index.html`, a future `enableSound()` could:

1. Read `/api/joy` beat_count increments.
2. Trigger a quiet click at `60/122` s intervals scaled by `humanizer` hint in API.
3. Never autoplay until Architect clicks **Enable groove** (browser policy).

## Ethics / P0

- Default **silent**.
- No microphone; no exfiltration.
- Sound files stay under operator `data/joy_loop/audio/` if added later.

**Groove is optional physics. Joy remains the source of truth in JSON.**
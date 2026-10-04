# PROTOCOL 10 — Environmental Resonance Bridge

**Signature:** `Δ9Φ963-P10-ERB-v1` · **Module:** `protocol10_env_resonance/` · **Version:** `P10.1.0-ERB`
**Status:** experimental · simulated-data verified · **not** part of the audited P0–P5 verdict table

---

## 1. What problem this solves

The stack already anchors *bytes* (P0), *memories* (P1), *claims* (text semantic
gate) and *attestations* (P6). It had no way to anchor the **physical place it
runs in**. P10 supplies that layer: a room's radio state becomes the same kind
of object as everything else in the lattice — a deterministic, chained,
verifiable cell.

Two properties make it fit the lattice rather than sit beside it:

1. **Determinism.** Same measurement → same anchor. Enforced by quantising every
   float onto a fixed integer grid before hashing, so the anchor does not drift
   with libm or with platform.
2. **Gate-before-truth.** A cell is not admitted on the strength of being a
   number. Its canonical bytes pass P0 first; a saturated, constant or griefing
   sensor stream registers as `SOFTEN`/`QUARANTINE` and is recorded as such.

## 2. Architecture

```
                 ┌──────────── P10 EnvResonanceLattice ────────────┐
CSI frames ──▶ prepare_window ──▶ measure ──▶ quantise ──▶ canonical ──▶ anchor ──▶ chain
                 (20 Hz grid)      (4 metrics)   (int grid)    (bytes)    (SHA-256)   │
                                                     │                              │
                                                     ├──▶ P0 validate_bytes ────────┤ admitted?
                                                     ├──▶ P1 scatter ───────────────┤ memory
                                                     └──▶ P8 HarmonicGravity ───────┘ resonance
```

| Stage | Module | Determinism note |
|---|---|---|
| windowing + resample | `csi_core.prepare_window` | linear interpolation onto `i/fs` grid; per-subcarrier mean removed |
| measurement | `csi_core` | biquad band-pass + direct DFT; no FFT lib, no numpy |
| quantisation | `lattice_cell.quantize_features` | scale table `FEATURE_SCALE`, round-half-away-from-zero |
| canonicalisation | `lattice_cell.canonical_bytes` | integer-only JSON, `sort_keys`, `ensure_ascii` |
| anchoring | `bridge.ingest_window` | `SHA256(canonical)` + `prev_anchor` chained in the payload |
| gate / memory / resonance | P0, P1, P8 | imported from sibling packages; availability is reported, never faked |

## 3. Measurements

| Feature (fixed-point) | Scale | Meaning |
|---|---|---|
| `motion_cdb` | centi-dB | coherent energy in 1.5–9.0 Hz above the empty-room floor |
| `breath_energy_cdb` | centi-dB | same, 0.10–0.50 Hz |
| `breath_rate_mbpm` | milli-BPM | DFT peak, parabolic-refined; **0 when the SNR gate refuses** |
| `breath_snr_cdb` | centi-dB | peak-to-median in-band SNR |
| `breath_conf_milli` | milli | peak / in-band mean power |
| `heart_rate_mbpm`, `heart_snr_cdb` | milli-BPM, centi-dB | experimental (0.8–2.0 Hz); never drives presence |
| `rssi_mdbm`, `presence_code`, `frames`, `subcarriers`, `span_ms` | — | context, and the exact window shape that produced the cell |

Presence state machine (thresholds in dB above the floor):

| State | Condition | Physical meaning |
|---|---|---|
| `ACTIVE` | `motion ≥ 6.0` | someone is moving |
| `SUBTLE` | `motion ≥ 2.5` | small movement — shifting, typing, fast breathing |
| `PRESENT` | `motion < 2.5` **and** `breath SNR ≥ 10.0` | still, and breathing |
| `CLEAR` | otherwise | nobody detected — and no rate is published |

**These thresholds are calibrated against the synthetic room model.** Real CSI
must be captured and the thresholds re-tuned on site before any field use.
Refusing to publish (CLEAR, or `breath_rate = 0` while moving) is a feature: a
blank is recoverable, an invented number becomes lattice truth.

## 4. Anchor and memory

- `anchor_n = SHA256(canonical_bytes_n)` where `canonical_bytes` embeds `anchor_{n-1}`.
  Dropping, reordering or editing a cell breaks `chain_valid()` from the head.
- `LatticeCell.verify()` re-decodes the canonical payload and compares every
  field — including the readable `features` — so editing the interpretation
  without touching the bytes still fails.
- `memory_payload()` omits floats (rounded to 6 dp, strings kept as strings) and
  its SHA-256 is stored as `payload_hash`; `EnvResonanceLattice.recall(i)`
  re-derives and compares it.
- P1's own `root_hash` is reported for information only: P1 shuffles its
  fragment list before hashing, so that root is not stable across runs. The
  cell's `payload_hash` is the deterministic one.

## 5. Integration

```python
from protocol10_env_resonance import EnvResonanceLattice

bridge = EnvResonanceLattice(node_id="LYGO-ERB-NODE-01", window_seconds=30.0)
cells = bridge.ingest(frames)         # frames: CSIFrame list, from ESP32 or synthetic
head = bridge.head                     # chain head -> hand to P6 attestation if desired
bridge.report()                        # counts, gate tallies, integration availability
```

P10 is deliberately **not** wired into `stack/lygo_stack.py` yet. Two reasons:
the audited P0–P5 orchestrator should not import an experimental module, and
the sensing path has not been validated on hardware. When a real capture has
been replayed and the thresholds re-tuned, wiring becomes a one-line addition
(`bridge.ingest(...)` + a `p10_report()` accessor) and the README/status tables
get the module.

## 6. Hardware and live capture

| Item | Detail |
|---|---|
| Sensor | ESP32-S3-WROOM-1 (CSI-capable), or a research NIC |
| Transport | serial CSV (parsed by `parse_esp32_csv_row`), or UDP at 200 pkt/s for pairwise |
| AP | any 2.4 GHz router; 5 GHz-only will not work with 2.4 GHz CSI capture |
| Placement | node and AP on opposite sides of the room to be sensed; a person between them |
| Band | 2.4 GHz penetrates plasterboard/wood/glass; brick and concrete attenuate; foil-backed insulation blocks |

Live capture is **untested in this repo**. `parse_esp32_csv_row()` is unit-tested
against a real-shaped row including signed I/Q, which is as far as simulated
verification can go.

## 7. Verification commands

```bash
python -m pytest protocol10_env_resonance/tests/ -q
python tools/build_erb_vectors.py --check
python protocol10_env_resonance/harness/run_env_resonance_demo.py
```

## 8. Roadmap

Shipped in this version:

- **P6 hand-off.** `EnvResonanceLattice.attestation_request()` packages the claim,
  anchor, chain state and canonical digest for a P6 badge. P6's
  `AttestationService` badges node hardware and verifies its own badges — it does
  not sign arbitrary payloads — so this hands over the claim rather than
  fabricating a signature.
- **Environment drift.** `observe_channel()` fingerprints the static channel
  shape (per-subcarrier mean amplitude, range-normalised then quantised) and
  reports normalised distance from the first observation: moved furniture, a new
  object, a different room. It answers "which room", not "who is in it".
  `DRIFT_THRESHOLD = 0.15`, calibrated against the synthetic rooms only.

Open:

1. Replay a real ESP32 capture; regenerate fixtures; re-tune presence thresholds.
2. Multi-node cells: one anchor per node per window, fused into a room cell with per-node `prev` links.
3. Live loop with `window_seconds` rolling rather than batch, with the chain head persisted between sessions.

## 9. Honest limits

- Synthetic self-consistency is not field accuracy. The generator and the
  estimator share an author.
- CSI does not generalise across rooms; the static channel differs per room.
- No pose reconstruction, no imaging — one antenna pair has no spatial resolution.
- Heart rate is reported but not trustworthy at 100 Hz / 30 s.
- P0's risk model cannot reach `QUARANTINE` on payloads of this size; its
  useful signal here is `AMPLIFY` vs `SOFTEN`.

## 10. Credits

Sensing physics follows [ruvnet/RuView](https://github.com/ruvnet/ruview) (MIT),
ESPectre, ESP32-CSI-Tool, `wifisense-pi`, and IEEE 802.11bf WLAN Sensing. None of
the physics is claimed as new; the deterministic anchoring, P0 gating, mycelium
recall and resonance hand-off are the LYGO contribution.

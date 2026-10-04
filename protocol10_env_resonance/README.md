# P10 — Environmental Resonance Bridge (ERB)

**Version:** `P10.1.0-ERB` · **Status:** experimental, simulated-data verified (see *What is real*)
**Lattice role:** environmental physics → deterministic, gated, recallable lattice cells → resonance hand-off

Turn a *place* into lattice state. Ordinary WiFi hardware already fills every
room with radio waves; when a person moves, breathes or sits still, those waves
scatter differently, and the channel response (CSI — Channel State Information)
carries that difference. P10 reads those measurements and does the LYGO thing
with them: **quantise deterministically, gate through P0, anchor with SHA-256,
scatter into P1 memory, and hand the anchor integer to P8 for resonance.**

No cameras, no wearables, no learned black box in the pipeline: a band-pass, a
DFT and a fixed-point quantiser.

---

## Why this belongs in the stack

| Stack layer | What P10 uses it for |
|---|---|
| **P0** — byte-entropy filter | Every cell's canonical bytes pass the Φ-gate before the reading is admitted. Poisoned, saturated or malformed sensor payloads are `SOFTEN`/`QUARANTINE`d instead of silently becoming lattice truth. |
| **P1** — Memory Mycelium | Each cell payload is scattered into fragments, recallable and hash-checked. Environmental memory survives node loss. |
| **P8** — LDQ synthesis (`HarmonicGravity`) | The anchor integer maps to golden-ratio harmonic parameters (bpm, root frequency, intensity) — the room's radio state becomes a resonance seed. |
| **P10** — this module | Turns *environmental* physics into the same anchor discipline the rest of the stack already applies to bytes, memories and claims. |

The philosophical point the steward asked for: the lattice stops talking only
about text and starts listening to the **environment** — and it listens
deterministically, so a measurement is a fact you can re-derive, not a vibe.

---

## Pipeline

```
ESP32-S3 / research NIC (or synthetic.py)
        │  CSI frames: per-subcarrier amplitude + phase @ 100 Hz
        ▼
csi_core.prepare_window      detrend per subcarrier → resample to a 20 Hz grid
        │                     common mode = mean across subcarriers
        ├─ motion_energy_db  band 1.5–9.0 Hz, 2-stage biquad, k-normalised
        ├─ breath_energy_db  band 0.10–0.50 Hz
        └─ estimate_breathing  DFT peak + parabolic refine + SNR gate
        ▼
lattice_cell.quantize_features   every value → fixed-point integer
lattice_cell.canonical_bytes     integer-only JSON, sort_keys, no floats
        ▼
P0 validate_bytes                AMPLIFY / SOFTEN / QUARANTINE  → admitted?
        ▼
anchor = SHA256(canonical || prev_anchor)      ← chained, tamper-evident
        ▼
P1 MemoryMycelium.scatter        recallable fragments + payload hash
P8 HarmonicGravity(anchor)       bpm / root frequency / intensity
```

### The metric that makes this honest

```
band_energy_db = 10·log10( k · var(common_band) / mean_i var(trace_i_band) )
```

Receiver noise is independent on every subcarrier, so it averages down by `k`
when the subcarriers are summed; anything physical in the room moves them
together. Multiplying by `k` puts **an empty room at ~0 dB** in any room, at
any distance, at any transmit power — no calibration pass and no learned
baseline that can drift out of date. Verified: the clear-room vector reads
`−0.10 dB`.

### The determinism contract

> The same CSI window produces the same anchor — byte for byte.

Mechanism: nothing floating-point ever reaches the hash. Measurements are
quantised onto fixed integer grids (centi-dB, milli-BPM, milli-unit) first, so
last-bit differences in `sin`/`log10` cannot move an anchor except on an
exact tie. `tools/build_erb_vectors.py --check` replays five synthetic rooms
and fails if any anchor moved.

---

## Quick start

```bash
# from the LYGO protocol stack root
python -m pytest protocol10_env_resonance/tests/ -q          # 21 tests
python tools/build_erb_vectors.py --check                    # golden anchors
python protocol10_env_resonance/harness/run_env_resonance_demo.py
```

```python
from protocol10_env_resonance import EnvResonanceLattice, synthesize_csi

bridge = EnvResonanceLattice(node_id="LYGO-ERB-NODE-01", window_seconds=30.0)
frames = synthesize_csi(duration_s=30.0, fs_hz=100.0, breathing_bpm=18.0)
cells  = bridge.ingest(frames)

cell = cells[0]
cell.presence          # 'PRESENT' — still, but breathing
cell.features['breath_rate_mbpm'] / 1000.0   # 18.0 bpm
cell.p0['verdict']     # 'AMPLIFY'
cell.anchor            # chained SHA-256
cell.resonance         # {'bpm':..., 'root_frequency':...} from P8

bridge.recall(0)       # P1 memory round-trip, hash-checked
bridge.report()        # cell count, chain_valid, gate/presence tallies
```

### Live hardware (not yet exercised)

`csi_core.parse_esp32_csv_row()` parses the ESP32-CSI-Tool / ESPectre CSV row
format (25 metadata columns + `[I Q I Q …]`), including signed I/Q. The parser
is unit-tested against a real-shaped row, but **no ESP32 has been attached to
this module yet** — treat the live path as untested until a capture is replayed
through the harness. Required hardware for real sensing (all of it is
commodity, none of it is a camera):

| Option | Hardware | Cost | Capability |
|---|---|---|---|
| Single node | ESP32-S3 dev board + any 2.4 GHz router | ~$9 | presence, motion, breathing rate |
| Pairwise | 2× ESP32-S3 (one TX at 200 pkt/s) | ~$18 | bounded sensing zone, cleaner vitals |
| Mesh | 3–6× ESP32-S3 | ~$54 | room identification, through-wall |

CSI-capable hardware is mandatory for anything beyond RSSI presence: consumer
laptops do not expose per-subcarrier CSI.

---

## What is real

Verified by tests in this repo, on synthetic CSI with known ground truth:

- **Breathing rate recovery** — 18.0 / 12.0 / 9.0 bpm requested, 18.00 / 12.00 / 9.00 bpm measured.
- **Empty room sits at the floor** — −0.10 dB motion, −0.65 dB breath band.
- **Walking dominates the motion band** — +16.6 dB, and the vitals estimator *refuses* (SNR 2.97 dB < 6 dB) rather than inventing a rate while the subject moves.
- **Determinism** — identical anchors across independent bridge instances and across process runs (`tools/build_erb_vectors.py --check`).
- **Tamper evidence** — editing a cell's readable features, or reordering cells, fails `verify()` / `chain_valid()`.
- **Stack integration** — P0 verdict recorded per cell, P1 recall round-trips hash-exact, P8 hand-off deterministic and in range.

## What is not real yet

- **No real hardware capture.** Every number above comes from `synthetic.py`, whose author wrote both the signal and the estimator. That is a self-consistency check, not a field result. The first real ESP32 capture must be replayed and the anchors regenerated — expect the presence thresholds to need recalibration on site.
- **CSI does not generalise across rooms.** The static channel differs per room; a threshold tuned in one room is a starting point in the next, not a constant.
- **Heart rate is experimental** (`estimate_heart_rate`) — 0.8–2.0 Hz at 100 Hz CSI over 30 s is marginal; it is reported but never allowed to set presence.
- **No pose, no imaging.** Antenna-array pose reconstruction (RF-Pose/DensePose style) is explicitly out of scope: one TX/RX with one antenna each has no spatial resolution, and this module makes no such claim.
- **The P0 gate's real signal here is AMPLIFY vs SOFTEN**, plus the hard 8 KiB cap; the filter's risk model cannot reach `QUARANTINE` on payloads of this size. That is a property of P0, not of P10, and it is recorded per cell rather than smoothed over.
- **P1's `root_hash` varies between runs** (its fragment list is shuffled before hashing). The cell therefore carries its own deterministic `payload_hash`; the P1 root is reported for information only.

## Credits / prior art

The sensing physics follows the open WiFi-CSI line of work, and none of it is
claimed as new here:

- [ruvnet/RuView](https://github.com/ruvnet/ruview) (MIT) — WiFi CSI sensing stack, model at `ruvnet/wifi-densepose-pretrained`
- [ESPectre](https://github.com/PeterkoCZ91/esphome-wifi-csi) — ESPHome CSI presence/breathing component
- ESP32-CSI-Tool (Steven Hernandez) — the CSV capture format parsed here
- IEEE 802.11bf — WLAN Sensing, the standard this all converges on
- `wifisense-pi` — the noise-floor-from-covariance approach the dB metric follows

What P10 adds is the LYGO part: fixed-point determinism, the Φ-gate, chained
anchoring, mycelium recall, and the resonance hand-off.

## Files

| Path | Role |
|---|---|
| `csi_core.py` | CSI ingest, resampling, band energy, rate estimation, presence state |
| `lattice_cell.py` | Quantisation, canonical bytes, chained anchor, verification |
| `bridge.py` | `EnvResonanceLattice` — windows, P0/P1/P8 wiring, reporting |
| `synthetic.py` | Deterministic LCG room generator (the falsifier) |
| `tests/` | 20 falsifiable checks |
| `harness/run_env_resonance_demo.py` | End-to-end demo, human + `--json` output |
| `fixtures/erb_vectors.json` | Golden anchors (built by `tools/build_erb_vectors.py`) |
| `docs/PROTOCOL10_ENV_RESONANCE.md` | Architecture, thresholds, integration notes |

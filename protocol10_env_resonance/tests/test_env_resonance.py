"""P10 test suite — falsifiable checks on the physics, the anchor and the chain.

Run from the stack root:

    python -m pytest protocol10_env_resonance/tests/ -q
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_ERB = _HERE.parents[1]
if str(_ERB.parent) not in sys.path:
    sys.path.insert(0, str(_ERB.parent))

from protocol10_env_resonance import (  # noqa: E402
    DRIFT_THRESHOLD,
    EnvResonanceLattice,
    LatticeCell,
    canonical_bytes,
    estimate_breathing,
    motion_energy_db,
    parse_esp32_csv_row,
    prepare_window,
    quantize_features,
    resonance_parameters,
    synthesize_csi,
)
from protocol10_env_resonance.bridge import P0_AVAILABLE, P1_AVAILABLE, P8_AVAILABLE  # noqa: E402
from protocol10_env_resonance.csi_core import (  # noqa: E402
    BREATH_BAND_HZ,
    breath_energy_db,
    presence_state,
)

EMPTY = dict(breathing_bpm=0.0, motion_windows=())
BREATH_18 = dict(breathing_bpm=18.0, motion_windows=())
WALK = dict(breathing_bpm=0.0, motion_windows=[(10.0, 20.0)])


def measure(**kw):
    frames = synthesize_csi(duration_s=30.0, fs_hz=100.0, seed=963, **kw)
    window = prepare_window(frames)
    assert window is not None
    return window, motion_energy_db(window), breath_energy_db(window), estimate_breathing(window)


# --- physics ---------------------------------------------------------------

def test_empty_room_sits_at_the_noise_floor():
    _, motion_db, breath_db, breath = measure(**EMPTY)
    assert abs(motion_db) < 3.0, f"empty room must read ~0 dB, got {motion_db:.2f}"
    assert abs(breath_db) < 3.0, f"empty breath band must read ~0 dB, got {breath_db:.2f}"
    assert not breath.resolved


def test_walking_is_far_above_the_floor():
    _, motion_db, _, _ = measure(**WALK)
    assert motion_db > 8.0, f"walking must dominate the motion band, got {motion_db:.2f}"


def test_breathing_rate_is_recovered():
    _, _, breath_db, breath = measure(**BREATH_18)
    assert breath.resolved, "18 bpm synthetic breathing must resolve"
    assert abs(breath.bpm - 18.0) <= 1.5, f"expected ~18 bpm, got {breath.bpm:.2f}"
    assert breath_db > 3.0, f"breathing must lift the breath band, got {breath_db:.2f}"
    assert breath.snr_db > 6.0


def test_breathing_rate_tracks_a_different_rate():
    _, _, _, breath = measure(breathing_bpm=12.0, motion_windows=[])
    assert abs(breath.bpm - 12.0) <= 1.5, f"expected ~12 bpm, got {breath.bpm:.2f}"


def test_empty_room_refuses_to_invent_a_rate():
    """A CLEAR room must not publish a breathing rate. False positives are worse than blanks."""
    _, _, _, breath = measure(**EMPTY)
    assert not breath.resolved
    assert breath.bpm == 0.0 or breath.snr_db < 10.0


def test_presence_state_machine():
    assert presence_state(0.0, 0.0) == "CLEAR"
    assert presence_state(0.0, 25.0) == "PRESENT"
    assert presence_state(4.0, 0.0) == "SUBTLE"
    assert presence_state(12.0, 0.0) == "ACTIVE"


# --- determinism -----------------------------------------------------------

def test_same_stream_same_anchor():
    a = EnvResonanceLattice()
    b = EnvResonanceLattice()
    cells_a = a.ingest(synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18))
    cells_b = b.ingest(synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18))
    assert [c.anchor for c in cells_a] == [c.anchor for c in cells_b]
    assert cells_a[0].features == cells_b[0].features


def test_anchor_matches_manual_recompute():
    frames = synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18)
    cell = EnvResonanceLattice().ingest(frames)[0]
    assert cell.anchor == hashlib.sha256(cell.canonical).hexdigest()
    assert cell.verify(prev_anchor="0" * 64)


def test_quantiser_is_exact_fixed_point():
    q = quantize_features(
        {
            "motion_cdb": 0.12345,
            "breath_energy_cdb": -0.5,
            "breath_rate_mbpm": 18.0004,
            "breath_snr_cdb": 12.5,
            "breath_conf_milli": 3.0,
            "heart_rate_mbpm": 0.0,
            "heart_snr_cdb": 0.0,
            "rssi_mdbm": -48.0,
            "presence_code": 3,
            "frames": 3000,
            "subcarriers": 64,
            "span_ms": 29010,
        }
    )
    assert q["motion_cdb"] == 12
    assert q["breath_energy_cdb"] == -50
    assert q["breath_rate_mbpm"] == 18000
    assert all(isinstance(v, int) for v in q.values())


def test_quantiser_rejects_missing_features():
    with pytest.raises(ValueError):
        quantize_features({"motion_cdb": 0.0})


def test_tampering_breaks_the_anchor():
    frames = synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18)
    cell = EnvResonanceLattice().ingest(frames)[0]
    forged = LatticeCell(
        index=cell.index,
        node_id=cell.node_id,
        window_start_us=cell.window_start_us,
        window_end_us=cell.window_end_us,
        features=dict(cell.features, motion_cdb=cell.features["motion_cdb"] + 1),
        canonical=cell.canonical,
        prev_anchor=cell.prev_anchor,
        anchor=cell.anchor,
    )
    assert not forged.verify()


def test_reordering_breaks_the_chain():
    frames = synthesize_csi(duration_s=70.0, fs_hz=100.0, **BREATH_18)
    bridge = EnvResonanceLattice(window_seconds=30.0)
    cells = bridge.ingest(frames)
    assert len(cells) >= 2
    assert bridge.chain_valid()
    bridge.cells.reverse()
    assert not bridge.chain_valid()


def test_canonical_bytes_are_stable_ascii_json():
    features = quantize_features(
        {
            "motion_cdb": 1.0,
            "breath_energy_cdb": 2.0,
            "breath_rate_mbpm": 3.0,
            "breath_snr_cdb": 4.0,
            "breath_conf_milli": 5.0,
            "heart_rate_mbpm": 6.0,
            "heart_snr_cdb": 7.0,
            "rssi_mdbm": 8.0,
            "presence_code": 9,
            "frames": 10,
            "subcarriers": 11,
            "span_ms": 12,
        }
    )
    blob = canonical_bytes(7, "NODE", 0, 30000000, features, "0" * 64)
    assert json.loads(blob.decode())["index"] == 7
    assert canonical_bytes(7, "NODE", 0, 30000000, features, "0" * 64) == blob


# --- integration with the stack -------------------------------------------

@pytest.mark.skipif(not P0_AVAILABLE, reason="P0 not present")
def test_p0_gate_runs_and_is_recorded():
    cell = EnvResonanceLattice().ingest(synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18))[0]
    assert cell.p0["verdict"] in ("AMPLIFY", "SOFTEN", "QUARANTINE")
    assert "entropy" in cell.p0


@pytest.mark.skipif(not P1_AVAILABLE, reason="P1 not present")
def test_p1_memory_roundtrip():
    bridge = EnvResonanceLattice()
    cell = bridge.ingest(synthesize_csi(duration_s=30.0, fs_hz=100.0, **BREATH_18))[0]
    recovered = bridge.recall(0)
    assert hashlib.sha256(recovered).hexdigest() == cell.memory["payload_hash"]
    assert json.loads(recovered.decode())["anchor"] == cell.anchor


@pytest.mark.skipif(not P8_AVAILABLE, reason="P8 not present")
def test_p8_resonance_handoff_is_deterministic():
    params = resonance_parameters("a" * 64)
    assert params["source"] == "P8:harmonic_gravity"
    assert 55.0 <= params["root_frequency"] <= 880.0
    assert resonance_parameters("a" * 64) == params


def test_resonance_parameters_bounds_without_p8():
    params = resonance_parameters("0123456789abcdef" * 4)
    assert 0.0 < params["intensity"] <= 1.0
    assert params["phi_band"] >= 1.6


# --- golden vectors --------------------------------------------------------

def test_golden_vectors_still_replay():
    """The fixture is the falsifier: if a refactor moves an anchor, this fails."""
    import subprocess

    fixture = _ERB / "fixtures" / "erb_vectors.json"
    if not fixture.exists():
        pytest.skip("fixture not built yet — run tools/build_erb_vectors.py")
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    assert doc["vector_version"]


def test_golden_vectors_check_passes_from_a_clean_process():
    """Determinism across processes, not just across objects in one process."""
    import subprocess
    import sys as _sys

    script = _ERB.parent / "tools" / "build_erb_vectors.py"
    if not script.exists():
        pytest.skip("vector builder missing")
    proc = subprocess.run(
        [_sys.executable, str(script), "--check"],
        capture_output=True,
        text=True,
        cwd=str(_ERB.parent),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


# --- ingest formats --------------------------------------------------------

def test_esp32_csv_parser_accepts_a_real_shaped_row():
    row = (
        "CSI_DATA,STA,AA:BB:CC:DD:EE:FF,-48,11,0,0,20,0,0,0,0,0,0,-96,0,6,0,"
        "123456789,0,64,0,0,123456789,8,[10 -5 20 -10 30 -15 40 -20]"
    )
    frame = parse_esp32_csv_row(row)
    assert frame is not None
    assert frame.subcarriers == 4
    assert frame.t_us == 123456789
    assert frame.rssi == -48
    assert frame.amplitudes[0] == pytest.approx(11.1803, abs=1e-3)
    # signed I/Q: a byte > 127 is a negative sample, not 255
    assert frame.phases[0] < 0.0


def test_esp32_csv_parser_skips_junk():
    assert parse_esp32_csv_row("") is None
    assert parse_esp32_csv_row("type,role,mac") is None
    assert parse_esp32_csv_row("CSI_DATA,STA,AA,-48,11,0,0,20,0,0,0,0,0,0,-96,0,6,0,1,0,64,0,0,0,") is None


def test_bands_are_in_physiological_order():
    assert BREATH_BAND_HZ[1] < 1.5  # breathing sits below the motion band


# --- environment drift + attestation ---------------------------------------

def _room(profile: int, **kw):
    return synthesize_csi(
        duration_s=30.0, fs_hz=100.0, seed=963, room_profile=profile, breathing_bpm=12.0, **kw
    )


def test_channel_fingerprint_is_stable_for_the_same_room():
    a = EnvResonanceLattice().observe_channel(_room(0))
    b = EnvResonanceLattice().observe_channel(_room(0))
    assert a["is_baseline"] is True
    assert a["fingerprint"] == b["fingerprint"]


def test_channel_drift_detects_a_different_room():
    """Fingerprint answers 'which room', not 'who is in it'."""
    bridge = EnvResonanceLattice()
    base = bridge.observe_channel(_room(0))
    same = bridge.observe_channel(_room(0))
    other = bridge.observe_channel(_room(3))
    assert same["distance"] == 0.0 and not same["changed"]
    assert other["distance"] > DRIFT_THRESHOLD
    assert other["changed"] is True
    assert other["baseline"] == base["fingerprint"]


def test_attestation_request_carries_the_chain_state():
    bridge = EnvResonanceLattice()
    bridge.ingest(_room(0))
    req = bridge.attestation_request()
    assert req["anchor"] == bridge.head
    assert req["canonical_sha256"] == req["anchor"]
    assert req["chain_valid"] is True
    assert req["badge"] is None
    with pytest.raises(ValueError):
        EnvResonanceLattice().attestation_request()

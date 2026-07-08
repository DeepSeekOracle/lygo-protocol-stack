from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from protocol6_quantum_attest.keylime_bridge import KeylimeAttestation
from protocol8_ldq_synthesis import HarmonicGravity
from tls_manager import TLSCertificateManager
from live_synthesis import generate_audio_from_seed


def test_tls_pin_roundtrip():
    td = Path(tempfile.mkdtemp())
    a = TLSCertificateManager("n1", td / "a")
    b = TLSCertificateManager("n2", td / "b")
    pa, pb = a.generate_self_signed(), b.generate_self_signed()
    a.ingest_peer_pin("n2", pb)
    assert a.verify_peer(b.cert_file) == "n2"
    assert a.get_pin("n2") == pb


def test_keylime_sim_quote():
    q = KeylimeAttestation("t1").get_quote()
    assert q and KeylimeAttestation.verify_quote(q)


def test_ldq_synthesis_wav():
    td = Path(tempfile.mkdtemp())
    out = Path(td) / "t.wav"
    r = generate_audio_from_seed("abc123", out, duration_sec=0.5)
    assert r["ok"] and out.stat().st_size > 44


def test_harmonic_gravity_seed_stable():
    g = HarmonicGravity(42)
    p1 = g.get_all_parameters()
    p2 = HarmonicGravity(42).get_all_parameters()
    assert p1["bpm"] == p2["bpm"]
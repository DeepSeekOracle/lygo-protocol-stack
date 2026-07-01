"""Canonical Protocol 0 test vectors."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from lygo_p0 import validate_bytes  # noqa: E402


def test_json_amplify():
    r = validate_bytes(b'{"a":1,"b":2}')
    assert r["verdict"] == "AMPLIFY"


def test_null_padding_soften():
    r = validate_bytes(b"\x00" * 1000)
    assert r["verdict"] == "SOFTEN"


def test_pattern_soften():
    r = validate_bytes((b"\x01\x02\x03" * 1000)[:3000])
    assert r["verdict"] == "SOFTEN"


def test_sequence_soften():
    r = validate_bytes(bytes(range(200)))
    assert r["verdict"] == "SOFTEN"


def test_oversize_quarantine():
    r = validate_bytes(b"\x00" * 9000)
    assert r["verdict"] == "QUARANTINE"
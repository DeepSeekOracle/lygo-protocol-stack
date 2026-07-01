"""P0.4 vector suite — 30+ adversarial, boundary, recursive, high-entropy cases."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from lygo_p0 import canonical_line, load_vectors, run_vector_suite, validate_bytes  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "p0_vectors.json"


@pytest.fixture(scope="module")
def vectors():
    if not FIXTURES.is_file():
        pytest.skip("Run tools/build_p0_vectors.py first")
    return load_vectors()


def test_fixture_count(vectors):
    assert len(vectors) >= 30


def test_legacy_canonical_ids(vectors):
    by_id = {v["id"]: v for v in vectors}
    assert validate_bytes(bytes.fromhex(by_id["json_minimal"]["hex"]))["verdict"] == "AMPLIFY"
    assert validate_bytes(bytes.fromhex(by_id["null_1k"]["hex"]))["verdict"] == "SOFTEN"
    assert validate_bytes(bytes.fromhex(by_id["oversize_9000"]["hex"]))["verdict"] == "QUARANTINE"


def test_all_vectors_match_expected(vectors):
    for v in vectors:
        data = bytes.fromhex(v["hex"])
        r = validate_bytes(data)
        assert r["verdict"] == v["expected_verdict"], v["id"]
        assert r["phi_risk"] == v["expected_phi_risk"], v["id"]


def test_phi_risk_present(vectors):
    for v in vectors:
        r = validate_bytes(bytes.fromhex(v["hex"]))
        assert "phi_risk" in r
        assert "reasoning" in r
        assert len(r["reasoning"]) > 10


def test_canonical_suite_stable_hash(vectors):
    body = run_vector_suite()
    lines = body.strip().split("\n")
    assert len(lines) == len(vectors)
    for line, v in zip(lines, vectors):
        assert line.startswith(v["id"] + "|")


def test_categories_cover_risk_surface():
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    cats = set(data["categories"])
    for need in ("canonical", "boundary", "adversarial", "high_entropy", "recursive"):
        assert need in cats
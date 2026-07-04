#!/usr/bin/env python3
"""P0 parity: golden vectors (Python byte_entropy_filter) + structural lyra kernel."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
sys.path.insert(0, str(PY))

import byte_entropy_filter as bef  # noqa: E402
import lygo_p0_lyra_kernel as lyra  # noqa: E402

GOLDEN = ROOT / "protocol0_byte_entropy_filter" / "fixtures" / "p0_canonical.sha256"


def test_golden_hash() -> tuple[bool, str]:
    body = bef.run_vector_suite()
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if not GOLDEN.is_file():
        return False, f"missing golden file {GOLDEN}"
    expected = GOLDEN.read_text(encoding="utf-8").strip().split()[0]
    return digest == expected, f"golden {expected[:16]}… got {digest[:16]}…"


def test_vector_expected_verdicts() -> tuple[bool, str]:
    fails = []
    for entry in bef.load_vectors():
        data = bytes.fromhex(entry["hex"])
        res = bef.validate_bytes(data)
        exp = entry.get("expected_verdict")
        if exp and res["verdict"] != exp:
            fails.append(f"{entry['id']}: expected {exp} got {res['verdict']}")
        exp_phi = entry.get("expected_phi_risk")
        if exp_phi is not None and res.get("phi_risk") != exp_phi:
            fails.append(f"{entry['id']}: expected_phi_risk mismatch")
    return (not fails, "; ".join(fails[:5]))


def test_lyra_structural() -> tuple[bool, str]:
    v = lyra.LYGOValidator()
    res = v.validate({"a": 1})
    if res.get("verdict") != "ALLOW":
        return False, f"simple dict expected ALLOW got {res.get('verdict')}"
    if "oath" in res:
        return False, "oath block must not exist after Biophase7 removal"
    res2 = v.validate("x" * 10000)
    if res2.get("verdict") != "ISOLATE":
        return False, f"oversize expected ISOLATE got {res2.get('verdict')}"
    return True, "structural bounds OK"


def main() -> int:
    checks = [
        ("golden_sha256", test_golden_hash),
        ("vector_verdicts", test_vector_expected_verdicts),
        ("lyra_structural", test_lyra_structural),
    ]
    results = []
    ok_all = True
    for name, fn in checks:
        ok, detail = fn()
        results.append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            ok_all = False
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")
    out = ROOT / "tests" / "parity_last_run.json"
    out.write_text(
        json.dumps({"signature": "Δ9Φ963-P0-PARITY-v1.1", "ok": ok_all, "checks": results}, indent=2),
        encoding="utf-8",
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
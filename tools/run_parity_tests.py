#!/usr/bin/env python3
"""P0 parity: golden vectors + structural lyra kernel; Oath Vector must stay deprecated/off by default."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "protocol0_nano_kernel" / "src" / "python"
sys.path.insert(0, str(PY))

import lygo_p0  # noqa: E402
import lygo_p0_lyra_kernel as lyra  # noqa: E402

GOLDEN = ROOT / "protocol0_nano_kernel" / "fixtures" / "p0_canonical.sha256"


def test_golden_hash() -> tuple[bool, str]:
    body = lygo_p0.run_vector_suite()
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if not GOLDEN.is_file():
        return False, f"missing golden file {GOLDEN}"
    expected = GOLDEN.read_text(encoding="utf-8").strip().split()[0]
    return digest == expected, f"golden {expected[:16]}… got {digest[:16]}…"


def test_vector_expected_verdicts() -> tuple[bool, str]:
    fails = []
    for entry in lygo_p0.load_vectors():
        data = bytes.fromhex(entry["hex"])
        res = lygo_p0.validate_bytes(data)
        exp = entry.get("expected_verdict")
        if exp and res["verdict"] != exp:
            fails.append(f"{entry['id']}: expected {exp} got {res['verdict']}")
    return (not fails, "; ".join(fails[:5]))


def test_lyra_structural_without_oath() -> tuple[bool, str]:
    v = lyra.LYGOValidator(enable_oath_vector=False)
    res = v.validate({"a": 1})
    if res.get("verdict") != "ALLOW":
        return False, f"simple dict expected ALLOW got {res.get('verdict')}"
    if "oath" in res:
        return False, "oath block present when enable_oath_vector=False"
    big = "x" * 10000
    res2 = v.validate(big)
    if res2.get("verdict") != "ISOLATE":
        return False, f"oversize expected ISOLATE got {res2.get('verdict')}"
    return True, "structural bounds OK"


def test_oath_deprecated_flag() -> tuple[bool, str]:
    v = lyra.LYGOValidator(enable_oath_vector=True)
    res = v.validate({"a": 1})
    if res.get("oath_deprecated"):
        return True, "oath path marked deprecated"
    if "oath" in res:
        return True, "oath optional path still available (deprecated)"
    return False, "expected oath or deprecation marker"


def main() -> int:
    checks = [
        ("golden_sha256", test_golden_hash),
        ("vector_verdicts", test_vector_expected_verdicts),
        ("lyra_structural", test_lyra_structural_without_oath),
        ("oath_deprecated", test_oath_deprecated_flag),
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
        json.dumps({"signature": "Δ9Φ963-P0-PARITY-v1", "ok": ok_all, "checks": results}, indent=2),
        encoding="utf-8",
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Verify Champion Kernel Eggs — tamper gate (mirrors kernel egg four pillars)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "champion_eggs" / "registry.json"
BUILD = ROOT / "data" / "champion_eggs" / "build"
OUT = ROOT / "tests" / "champion_eggs_last_run.json"
SIGNATURE = "Δ9Φ963-CHAMPION-EGG-VERIFY-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def merkle_root(hex_hashes: list[str]) -> str:
    if not hex_hashes:
        return hashlib.sha256(b"").hexdigest()
    layer = list(hex_hashes)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            pair = layer[i] + (layer[i + 1] if i + 1 < len(layer) else layer[i])
            nxt.append(hashlib.sha256(pair.encode()).hexdigest())
        layer = nxt
    return layer[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not REGISTRY.is_file():
        print("MISSING registry", file=sys.stderr)
        return 2
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = []
    all_ok = True
    roots = []
    for entry in reg.get("eggs", []):
        egg_id = entry.get("egg_id")
        expected = (entry.get("transport") or {}).get("content_sha256", "")
        bin_path = ROOT / entry.get("bin_path", f"data/champion_eggs/build/{egg_id}.bin")
        ok = bin_path.is_file() and sha256_bytes(bin_path.read_bytes()) == expected
        if ok:
            roots.append(entry.get("merkle_root", ""))
        else:
            all_ok = False
        checks.append({"egg_id": egg_id, "ok": ok})
    expected_council = reg.get("council_merkle_root", "")
    computed = merkle_root([r for r in roots if r])
    council_ok = computed == expected_council and len(roots) == reg.get("champion_count", 0)
    if not council_ok:
        all_ok = False
    verdict = "ALIGNED" if all_ok else "QUARANTINE"
    report = {
        "signature": SIGNATURE,
        "timestamp": time.time(),
        "verdict": verdict,
        "all_pass": all_ok,
        "champion_count": reg.get("champion_count"),
        "council_merkle_root": expected_council,
        "council_merkle_recomputed": computed,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(report))
    else:
        print(f"champion_eggs verdict={verdict} count={reg.get('champion_count')}")
    return 0 if all_ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
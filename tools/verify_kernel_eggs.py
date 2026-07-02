#!/usr/bin/env python3
"""
Kernel egg tamper verification — four pillars enforced locally.
SHA-256 per egg · registry Merkle root · anchor envelope match · reject on mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "kernel_eggs" / "registry.json"
BUILD = ROOT / "data" / "kernel_eggs" / "build"
ANCHORS = ROOT / "data" / "anchors"
OUT = ROOT / "tests" / "kernel_eggs_last_run.json"
SIGNATURE = "Δ9Φ963-KERNEL-EGG-VERIFY-v1"


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


def verify_registry(reg: dict) -> dict:
    checks: list[dict] = []
    all_ok = True
    transport_hashes: list[str] = []

    for entry in reg.get("eggs", []):
        egg_id = entry.get("egg_id", "?")
        expected = (entry.get("transport") or {}).get("content_sha256", "")
        bin_rel = entry.get("bin_path", "")
        bin_path = ROOT / bin_rel if bin_rel else BUILD / f"{egg_id}.bin"
        ok_bin = False
        actual = ""
        if bin_path.is_file():
            actual = sha256_bytes(bin_path.read_bytes())
            ok_bin = actual == expected
            if ok_bin:
                transport_hashes.append(actual)
        checks.append(
            {
                "id": f"egg-bin-{egg_id}",
                "pass": ok_bin and bool(expected),
                "expected_sha256": expected[:16] if expected else None,
                "actual_sha256": actual[:16] if actual else None,
            }
        )
        if not (ok_bin and expected):
            all_ok = False

    recomputed = merkle_root(transport_hashes)
    declared = reg.get("registry_merkle_root", "")
    root_ok = recomputed == declared and bool(declared)
    checks.append(
        {
            "id": "registry-merkle-root",
            "pass": root_ok,
            "declared": declared[:16] if declared else None,
            "recomputed": recomputed[:16],
        }
    )
    if not root_ok:
        all_ok = False

    for anch in reg.get("anchored", []):
        egg_id = anch.get("egg_id", "?")
        digest = anch.get("content_sha256", "")
        anchor_path = ANCHORS / f"{digest}.json"
        anchor_ok = anchor_path.is_file()
        envelope_match = False
        if anchor_ok:
            env = json.loads(anchor_path.read_text(encoding="utf-8"))
            envelope_match = env.get("content_sha256") == digest
            bin_path = BUILD / f"{egg_id}.bin"
            if bin_path.is_file():
                envelope_match = envelope_match and sha256_bytes(bin_path.read_bytes()) == digest
        checks.append(
            {
                "id": f"anchor-{egg_id}",
                "pass": anchor_ok and envelope_match,
                "content_sha256": digest[:16] if digest else None,
            }
        )
        if not (anchor_ok and envelope_match):
            all_ok = False

    ar = reg.get("anchor_registry") or {}
    if ar.get("content_sha256"):
        ar_ok = (ANCHORS / f"{ar['content_sha256']}.json").is_file()
        checks.append({"id": "anchor-registry-manifest", "pass": ar_ok})
        if not ar_ok:
            all_ok = False

    return {
        "signature": SIGNATURE,
        "all_pass": all_ok,
        "verdict": "ALIGNED" if all_ok else "QUARANTINE",
        "registry_merkle_root": declared,
        "checks": checks,
        "timestamp": time.time(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default=str(OUT))
    args = ap.parse_args()

    if not REGISTRY.is_file():
        report = {"signature": SIGNATURE, "all_pass": False, "verdict": "QUARANTINE", "error": "no_registry"}
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    report = verify_registry(reg)
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "all_pass": report["all_pass"]}, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
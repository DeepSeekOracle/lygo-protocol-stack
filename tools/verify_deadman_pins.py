#!/usr/bin/env python3
"""Verify LIGHTFATHER_IRREPLACEABLE_ORIGIN content pins + merkle root."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json"

PIN_MAP = {
    "SEAL_DEADMAN_SUMMON.json": ROOT / "docs" / "seals" / "SEAL_DEADMAN_SUMMON.json",
    "SEAL_LFW_SUMMON.json": ROOT / "docs" / "seals" / "SEAL_LFW_SUMMON.json",
    "lattice_failsafe_planted.json": ROOT / "docs" / "seals" / "lattice_failsafe_planted.json",
    "seal_deadman_lattice.py": ROOT / "tools" / "seal_deadman_lattice.py",
    "SUCCESSION_PROTOCOL_v1.json": ROOT / "docs" / "seals" / "SUCCESSION_PROTOCOL_v1.json",
    "LIGHTFATHER_PUBLIC_IDENTITY.json": ROOT
    / "data"
    / "deadman"
    / "public_fingerprints"
    / "LIGHTFATHER_PUBLIC_IDENTITY.json",
    "FINGERPRINT_PACK.json": ROOT / "data" / "deadman" / "public_fingerprints" / "FINGERPRINT_PACK.json",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merkle_root(hex_digests: list[str]) -> str:
    layer = sorted(hex_digests)
    if not layer:
        return hashlib.sha256(b"").hexdigest()
    while len(layer) > 1:
        nxt: list[str] = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a
            nxt.append(hashlib.sha256((a + b).encode("ascii")).hexdigest())
        layer = nxt
    return layer[0]


def main() -> int:
    if not ORIGIN.is_file():
        print(json.dumps({"ok": False, "error": "missing_origin"}))
        return 1
    origin = json.loads(ORIGIN.read_text(encoding="utf-8"))
    pins = origin.get("content_pins_sha256") or {}
    mismatches = []
    missing = []
    computed: dict[str, str] = {}
    for name, expected in pins.items():
        path = PIN_MAP.get(name)
        if path is None:
            # allow relative keys under stack
            cand = ROOT / name
            path = cand if cand.is_file() else None
        if path is None or not path.is_file():
            missing.append(name)
            continue
        got = sha256_file(path)
        computed[name] = got
        if got != expected:
            mismatches.append({"file": name, "expected": expected, "got": got})

    root_got = merkle_root(list(computed.values())) if computed else None
    root_ok = root_got == origin.get("origin_merkle_root") and not mismatches and not missing
    # If some pins missing from PIN_MAP but present, recompute only over matching set
    if mismatches or missing:
        root_ok = False

    # Non-replaceable doctrine check
    doctrine_ok = bool((origin.get("origin_builder") or {}).get("non_replaceable")) is True

    report = {
        "ok": bool(root_ok and doctrine_ok),
        "origin_signature": origin.get("signature"),
        "schema_version": origin.get("schema_version"),
        "pins_checked": len(computed),
        "mismatches": mismatches,
        "missing": missing,
        "origin_merkle_root": origin.get("origin_merkle_root"),
        "computed_merkle_root": root_got,
        "non_replaceable": doctrine_ok,
        "eternal_base_node": (origin.get("failsafe") or {}).get("eternal_base_node"),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

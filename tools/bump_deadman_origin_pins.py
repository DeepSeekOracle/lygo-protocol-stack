#!/usr/bin/env python3
"""Recompute origin content pins after intentional deadman changes.

Requires --i-consent (pins are identity-critical).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN_PATHS = [
    ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
    ROOT / "data" / "deadman" / "egg_payload" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
    ROOT
    / "docs"
    / "kernel_eggs"
    / "lightfather-deadman-failsafe-v1"
    / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
]

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true", required=True)
    ap.add_argument("--note", default="intentional pin bump")
    args = ap.parse_args()

    pins = {k: sha256_file(p) for k, p in PIN_MAP.items() if p.is_file()}
    root = merkle_root(list(pins.values()))
    now = datetime.now(timezone.utc).isoformat()

    for path in ORIGIN_PATHS:
        if not path.is_file():
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["content_pins_sha256"] = pins
        obj["origin_merkle_root"] = root
        obj["updated_utc"] = now
        obj.setdefault("pin_bump_log", []).append({"utc": now, "note": args.note, "root": root})
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("updated", path)

    print(json.dumps({"ok": True, "origin_merkle_root": root, "pins": len(pins)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

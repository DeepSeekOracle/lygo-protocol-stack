#!/usr/bin/env python3
"""Retrieve manifest by id — stream reassemble with per-chunk hash verify."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.registry_manager import load_registry  # noqa: E402
from scalable_registry.retrieve import retrieve_by_id  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default=None, help="manifest_id")
    ap.add_argument("--out", type=Path, default=None, help="Output file path")
    ap.add_argument("--list", action="store_true", help="List registry entries")
    args = ap.parse_args()

    if args.list:
        reg = load_registry()
        for e in reg.get("entries") or []:
            print(e.get("id"), e.get("merkle_root", "")[:16], e.get("metadata", {}).get("name", ""))
        return 0

    if not args.id or not args.out:
        ap.error("--id and --out required unless --list")

    try:
        result = retrieve_by_id(args.id, args.out)
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc), "verdict": "QUARANTINE"}), file=sys.stderr)
        return 3
    except ValueError as exc:
        if "TAMPER" in str(exc):
            print(json.dumps({"error": str(exc), "verdict": "QUARANTINE"}), file=sys.stderr)
            return 3
        raise
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
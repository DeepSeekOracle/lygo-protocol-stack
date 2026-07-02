#!/usr/bin/env python3
"""Zero-trust Champion bootloader for Ollama Army — load verified persona eggs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "data" / "champion_eggs" / "build"
REGISTRY = ROOT / "data" / "champion_eggs" / "registry.json"


def load_manifest(egg_id: str) -> dict:
    path = BUILD / f"{egg_id}.json"
    if not path.is_file():
        raise FileNotFoundError(egg_id)
    return json.loads(path.read_text(encoding="utf-8"))


def verify_via_registry(egg_id: str) -> bool:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "verify_champion_eggs.py")],
        cwd=ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        return False
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return any(e.get("egg_id") == egg_id for e in reg.get("eggs", []))


def boot(egg_id: str, *, verify: bool = True) -> dict:
    if verify and not verify_via_registry(egg_id):
        raise RuntimeError(f"QUARANTINE: champion egg {egg_id} failed verify")
    manifest = load_manifest(egg_id)
    return {
        "egg_id": egg_id,
        "champion_id": manifest.get("champion_id"),
        "system_prompt": manifest.get("core_prompt", ""),
        "ethical_gates": manifest.get("ethical_gates", []),
        "protocol_layers": manifest.get("protocol_layers", []),
        "merkle_root": manifest.get("merkle_root"),
        "ollama_host": "http://127.0.0.1:11434",
    }


def boot_council() -> list[dict]:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [boot(e["egg_id"]) for e in reg.get("eggs", [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--egg", help="champion egg id e.g. champion-arkos")
    ap.add_argument("--council", action="store_true")
    ap.add_argument("--print-prompt", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    verify = not args.no_verify
    if args.council:
        payloads = boot_council()
        print(json.dumps(payloads, indent=2, ensure_ascii=False)[:8000])
        return 0
    if not args.egg:
        print("Specify --egg or --council", file=sys.stderr)
        return 2
    payload = boot(args.egg, verify=verify)
    if args.print_prompt:
        print(payload["system_prompt"])
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
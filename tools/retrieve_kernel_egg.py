#!/usr/bin/env python3
"""SOA retrieval — local CA, registry, or Arweave gateway."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "kernel_eggs" / "registry.json"
ANCHORS = ROOT / "data" / "anchors"


def decode_transport(data: bytes) -> dict:
    try:
        return json.loads(zlib.decompress(data).decode("utf-8"))
    except Exception:
        return json.loads(data.decode("utf-8"))


def from_local_sha(sha256: str) -> dict | None:
    path = ANCHORS / f"{sha256}.json"
    if not path.is_file():
        return None
    env = json.loads(path.read_text(encoding="utf-8"))
    b64 = env.get("payload_b64")
    if not b64:
        return {"envelope": env, "note": "payload too large for inline; use bin in kernel_eggs/build"}
    return decode_transport(base64.b64decode(b64))


def from_gateway(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--egg", required=True, help="egg_id e.g. p0-nano-kernel")
    ap.add_argument("--list", action="store_true", help="List eggs in registry")
    ap.add_argument("--from-url", help="Fetch permaweb URL directly")
    args = ap.parse_args()

    if args.list:
        if not REGISTRY.is_file():
            print("No registry — run build + anchor first")
            return 1
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for e in reg.get("eggs", []):
            print(e.get("egg_id"), e.get("transport", {}).get("content_sha256", "")[:16])
        for a in reg.get("anchored", []):
            print(" anchored:", a.get("egg_id"), a.get("url", a.get("service")))
        return 0

    if args.from_url:
        egg = decode_transport(from_gateway(args.from_url))
        print(json.dumps(egg, indent=2)[:8000])
        return 0

    if not REGISTRY.is_file():
        return 1
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    hit = next((a for a in reg.get("anchored", []) if a.get("egg_id") == args.egg), None)
    if hit and hit.get("content_sha256"):
        egg = from_local_sha(hit["content_sha256"])
        if egg:
            print(json.dumps(egg, indent=2)[:12000])
            return 0
    bin_path = ROOT / "data" / "kernel_eggs" / "build" / f"{args.egg}.bin"
    if bin_path.is_file():
        import hashlib

        actual = hashlib.sha256(bin_path.read_bytes()).hexdigest()
        expected = None
        for e in reg.get("eggs", []):
            if e.get("egg_id") == args.egg:
                expected = (e.get("transport") or {}).get("content_sha256")
                break
        for a in reg.get("anchored", []):
            if a.get("egg_id") == args.egg:
                expected = expected or a.get("content_sha256")
        if expected and actual != expected:
            print(
                json.dumps(
                    {
                        "error": "TAMPER_DETECTED",
                        "egg_id": args.egg,
                        "expected_sha256": expected,
                        "actual_sha256": actual,
                        "verdict": "QUARANTINE",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 3
        print(json.dumps(decode_transport(bin_path.read_bytes()), indent=2)[:12000])
        return 0
    print(f"Egg {args.egg} not found locally", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
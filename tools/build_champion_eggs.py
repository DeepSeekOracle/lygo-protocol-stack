#!/usr/bin/env python3
"""Build Champion Kernel Eggs — manifests + transport blobs + council registry."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from champion_egg_schema import COUNCIL_SIGNATURE, manifest_from_champion  # noqa: E402
from kernel_egg_catalog import merkle_root  # noqa: E402

COUNCIL_JSON = ROOT / "data" / "champion_eggs" / "champions_council.json"
BUILD_DIR = ROOT / "data" / "champion_eggs" / "build"
REGISTRY = ROOT / "data" / "champion_eggs" / "registry.json"
MAX_BYTES = 102400


def _git_head() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10)
            .strip()[:12]
        )
    except Exception:
        return "unknown"


def _transport(egg: dict) -> dict:
    payload = json.dumps(egg, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    transport = zlib.compress(payload, level=9)
    if len(transport) > MAX_BYTES:
        slim = {**egg, "core_prompt": (egg.get("core_prompt") or "")[:12000]}
        payload = json.dumps(slim, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        transport = zlib.compress(payload, level=9)
    if len(transport) > MAX_BYTES:
        raise ValueError(f"egg {egg.get('egg_id')} exceeds {MAX_BYTES} bytes after slim")
    digest = hashlib.sha256(transport).hexdigest()
    return {
        "encoding": "zlib+json",
        "size_bytes": len(transport),
        "content_sha256": digest,
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "blob_b64": base64.b64encode(transport).decode("ascii"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--council", type=Path, default=COUNCIL_JSON)
    args = ap.parse_args()
    if not args.council.is_file():
        print("Run extract_champions_from_hub.py first", file=sys.stderr)
        return 2

    data = json.loads(args.council.read_text(encoding="utf-8"))
    champions = data.get("champions") or []
    if len(champions) < 15:
        print(f"Expected ≥15 champions, got {len(champions)}", file=sys.stderr)
        return 1

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    built_utc = time.time()
    git_head = _git_head()
    eggs_meta = []
    manifest_hashes = []

    for ch in champions:
        manifest = manifest_from_champion(ch, git_head=git_head, built_utc=built_utc)
        manifest["merkle_root"] = hashlib.sha256(
            json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        transport = _transport(manifest)
        egg_id = manifest["egg_id"]
        json_path = BUILD_DIR / f"{egg_id}.json"
        bin_path = BUILD_DIR / f"{egg_id}.bin"
        json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        bin_path.write_bytes(base64.b64decode(transport["blob_b64"]))
        manifest_hashes.append(manifest["merkle_root"])
        eggs_meta.append(
            {
                "egg_id": egg_id,
                "champion_id": manifest["champion_id"],
                "merkle_root": manifest["merkle_root"],
                "transport": {k: v for k, v in transport.items() if k != "blob_b64"},
                "json_path": str(json_path.relative_to(ROOT)),
                "bin_path": str(bin_path.relative_to(ROOT)),
            }
        )
        print(f"[built] {egg_id} ({manifest['champion_id']}) {transport['size_bytes']}b")

    council_root = merkle_root(manifest_hashes)
    super_egg = {
        "type": "council_super_egg",
        "signature": COUNCIL_SIGNATURE,
        "council_id": "DELTA9_QUANTUM_COUNCIL",
        "champion_count": len(eggs_meta),
        "global_merkle_root": council_root,
        "egg_ids": [e["egg_id"] for e in eggs_meta],
        "built_utc": built_utc,
        "git_head": git_head,
        "bootloader": "tools/champion_bootloader.py --council",
    }
    (BUILD_DIR / "council-super-egg.json").write_text(
        json.dumps(super_egg, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    reg = {
        "signature": COUNCIL_SIGNATURE,
        "updated_utc": built_utc,
        "git_head": git_head,
        "council_merkle_root": council_root,
        "champion_count": len(eggs_meta),
        "eggs": eggs_meta,
        "super_egg": "data/champion_eggs/build/council-super-egg.json",
        "source": str(args.council.relative_to(ROOT)),
    }
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    (ROOT / "docs" / "ChampionEggRegistry.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print(f"council_merkle_root={council_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
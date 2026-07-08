#!/usr/bin/env python3
"""Build kernel eggs — shard for Arweave Turbo free tier (100 KiB per egg)."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from kernel_egg_catalog import (  # noqa: E402
    EGG_SPECS,
    RETRIEVAL_SOA,
    SIGNATURE,
    file_sha256,
    merkle_root,
)
from lygo_anchor_config import AnchorProfile  # noqa: E402

BUILD_DIR = ROOT / "data" / "kernel_eggs" / "build"
REGISTRY = ROOT / "data" / "kernel_eggs" / "registry.json"


def _git_head() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10)
        return out.strip()[:12]
    except Exception:
        return "unknown"


def build_egg(egg_id: str, max_bytes: int, *, compress: bool) -> dict | None:
    spec = EGG_SPECS.get(egg_id)
    if not spec:
        return None
    artifacts = []
    hashes = []
    for label, path in spec:
        if not path.is_file():
            artifacts.append({"label": label, "path": str(path), "missing": True})
            continue
        raw = path.read_bytes()
        digest = file_sha256(path)
        hashes.append(digest)
        gh = None
        try:
            gh = f"{RETRIEVAL_SOA['github_repo']}/blob/main/{path.relative_to(ROOT).as_posix()}"
        except ValueError:
            gh = None
        entry: dict = {
            "label": label,
            "path": str(path),
            "sha256": digest,
            "size_bytes": len(raw),
            "retrieve": {"github_raw": gh, "hf_dataset": RETRIEVAL_SOA["hf_dataset"]},
        }
        if len(raw) <= 24_000:
            entry["inline_b64"] = base64.b64encode(raw).decode("ascii")
        artifacts.append(entry)
    egg = {
        "signature": SIGNATURE,
        "egg_id": egg_id,
        "built_utc": time.time(),
        "git_head": _git_head(),
        "merkle_root": merkle_root(hashes),
        "retrieval_soa": {**RETRIEVAL_SOA, "git_head": _git_head()},
        "artifacts": artifacts,
        "note": "Kernel capsule — not a bootable OS. Verify sha256 then pull full files from SOA URLs.",
    }
    payload = json.dumps(egg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    transport = payload
    encoding = "json"
    if compress:
        transport = zlib.compress(payload, level=9)
        encoding = "zlib+json"
    if len(transport) > max_bytes:
        # Drop inline — hash-only egg
        slim = {**egg, "artifacts": [{k: v for k, v in a.items() if k != "inline"} for a in artifacts]}
        payload = json.dumps(slim, sort_keys=True, separators=(",", ":")).encode("utf-8")
        transport = zlib.compress(payload, level=9) if compress else payload
        encoding = "zlib+json" if compress else "json"
    if len(transport) > max_bytes:
        return None
    egg["_transport"] = {
        "encoding": encoding,
        "size_bytes": len(transport),
        "content_sha256": __import__("hashlib").sha256(transport).hexdigest(),
        "blob_b64": base64.b64encode(transport).decode("ascii"),
    }
    return egg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--egg", action="append", help="Build only these egg ids")
    ap.add_argument("--max-bytes", type=int, default=AnchorProfile.load().free_max_bytes)
    ap.add_argument("--no-compress", action="store_true")
    args = ap.parse_args()

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    ids = args.egg or list(EGG_SPECS.keys())
    built = []
    skipped = []
    for egg_id in ids:
        egg = build_egg(egg_id, args.max_bytes, compress=not args.no_compress)
        if egg is None:
            skipped.append({"egg_id": egg_id, "reason": "exceeds_max_bytes"})
            continue
        transport_meta = egg.pop("_transport")
        out_path = BUILD_DIR / f"{egg_id}.json"
        out_path.write_text(json.dumps(egg, indent=2), encoding="utf-8")
        bin_path = BUILD_DIR / f"{egg_id}.bin"
        import base64

        bin_path.write_bytes(base64.b64decode(transport_meta["blob_b64"]))
        built.append(
            {
                "egg_id": egg_id,
                "merkle_root": egg["merkle_root"],
                "transport": transport_meta,
                "json_path": str(out_path.relative_to(ROOT)),
                "bin_path": str(bin_path.relative_to(ROOT)),
            }
        )

    registry = {
        "signature": SIGNATURE,
        "updated_utc": time.time(),
        "git_head": _git_head(),
        "free_max_bytes": args.max_bytes,
        "registry_merkle_root": merkle_root([b["transport"]["content_sha256"] for b in built]),
        "eggs": built,
        "skipped": skipped,
        "retrieval_soa": RETRIEVAL_SOA,
    }
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    public = ROOT / "docs" / "KernelEggRegistry.json"
    public.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(json.dumps({"built": len(built), "skipped": skipped, "registry": str(REGISTRY)}, indent=2))
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())
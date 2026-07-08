#!/usr/bin/env python3
"""Anchor kernel egg registry + each .bin to local CA + Turbo (free tier)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lygo_anchor import MultiAnchor  # noqa: E402
from lygo_anchor_config import AnchorProfile  # noqa: E402

REGISTRY = ROOT / "data" / "kernel_eggs" / "registry.json"
BUILD_DIR = ROOT / "data" / "kernel_eggs" / "build"
SIGNATURE = "Δ9Φ963-KERNEL-EGG-ANCHOR-v1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--local-only", action="store_true", help="Skip Turbo (airgap)")
    args = ap.parse_args()

    if not REGISTRY.is_file():
        print("Run build_kernel_eggs.py first", file=sys.stderr)
        return 1

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    profile = AnchorProfile.load()
    if args.local_only:
        profile.mode = "local"
    multi = MultiAnchor(profile, ROOT)
    anchored = []

    for entry in reg.get("eggs", []):
        egg_id = entry["egg_id"]
        bin_path = ROOT / entry["bin_path"]
        if not bin_path.is_file():
            continue
        data = bin_path.read_bytes()
        pid = f"kernel_egg_{egg_id}"
        if args.dry_run:
            anchored.append({"egg_id": egg_id, "dry_run": True, "size": len(data)})
            continue
        result = multi.anchor_bytes(data, pid, description=f"KERNEL_EGG:{egg_id}")
        anchored.append(
            {
                "egg_id": egg_id,
                "payload_id": pid,
                "content_sha256": result.content_sha256,
                "url": result.url,
                "service": result.service,
                "success": result.success,
                "size_bytes": len(data),
                "metadata": result.metadata,
            }
        )

    # Anchor registry manifest (small JSON)
    reg_payload = json.dumps(
        {
            "signature": SIGNATURE,
            "registry_merkle_root": reg.get("registry_merkle_root"),
            "eggs": anchored,
            "retrieval_soa": reg.get("retrieval_soa"),
            "anchored_utc": time.time(),
        },
        sort_keys=True,
    ).encode("utf-8")
    if not args.dry_run:
        reg_anchor = multi.anchor_bytes(reg_payload, "kernel_egg_registry", description="KERNEL_EGG_REGISTRY")
        reg["anchor_registry"] = {
            "url": reg_anchor.url,
            "content_sha256": reg_anchor.content_sha256,
            "service": reg_anchor.service,
        }
    reg["anchored"] = anchored
    reg["anchor_signature"] = SIGNATURE
    reg["anchored_utc"] = time.time()
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    # Receipt for lattice
    receipt_path = ROOT / "tools/lygo_control_center/workspace/kernel_eggs_last_anchor.json"
    receipt_path.write_text(json.dumps({"anchored": anchored, "registry": str(REGISTRY)}, indent=2), encoding="utf-8")
    print(json.dumps({"anchored_count": len(anchored), "registry": str(REGISTRY)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
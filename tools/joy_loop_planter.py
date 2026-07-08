#!/usr/bin/env python3
"""Plant Joy Loop kernel egg + public lattice mirrors (consent-gated)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_LOCAL = ROOT / "data" / "joy_loop" / "joy_loop_egg_registry.json"
REGISTRY_PUBLIC = ROOT / "docs" / "JoyLoopRegistry.json"
MANIFEST = ROOT / "data" / "joy_loop" / "joy_loop_egg_manifest.json"
SIGNATURE = "Δ9Φ963-JOY-LOOP-EGG-v1"
EGG_ID = "joy-loop-protocol-v21"


def _git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10
        )
        return out.strip()[:12]
    except Exception:
        return "unknown"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest() -> dict:
    artifacts = [
        ("joy_loop_protocol", ROOT / "tools" / "joy_loop_protocol.py"),
        ("joy_loop_doc", ROOT / "docs" / "JOY_LOOP_PROTOCOL.md"),
        ("joy_snapshot_stub", ROOT / "docs" / "joy_loop" / "joy_loop_snapshot.json"),
    ]
    hashes = []
    entries = []
    for label, path in artifacts:
        if not path.is_file():
            entries.append({"label": label, "path": str(path), "missing": True})
            continue
        digest = _sha256_file(path)
        hashes.append(digest)
        entries.append(
            {
                "label": label,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest,
                "size_bytes": path.stat().st_size,
            }
        )

    def merkle(hex_hashes: list[str]) -> str:
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

    merkle_root = merkle(hashes)
    manifest = {
        "signature": SIGNATURE,
        "type": "joy_loop_kernel_egg",
        "egg_id": EGG_ID,
        "version": "2.1.0",
        "built_utc": time.time(),
        "git_head": _git_head(),
        "merkle_root": merkle_root,
        "resonance_bpm": 122,
        "artifacts": entries,
        "boot": "python tools/joy_loop_protocol.py --tick",
        "pages_mirror": "https://deepseekoracle.github.io/lygo-protocol-stack/JoyLoopRegistry.json",
        "snapshot_mirror": (
            "https://deepseekoracle.github.io/lygo-protocol-stack/joy_loop/joy_loop_snapshot.json"
        ),
        "ethical_gates": ["P0_STRICT", "LUMINAL_ETHICS", "LOCAL_FIRST"],
        "protocol_layers": ["P2", "P5", "P6"],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    registry = {
        "signature": SIGNATURE,
        "updated_utc": time.time(),
        "git_head": manifest["git_head"],
        "egg_count": 1,
        "registry_merkle_root": merkle_root,
        "eggs": [
            {
                "egg_id": EGG_ID,
                "merkle_root": merkle_root,
                "manifest_path": "data/joy_loop/joy_loop_egg_manifest.json",
            }
        ],
    }
    REGISTRY_LOCAL.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    REGISTRY_PUBLIC.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()
    if not args.i_consent and os.environ.get("LYGO_JOY_PLANT_CONSENT", "").lower() not in (
        "yes",
        "1",
        "true",
    ):
        print("Consent required: --i-consent or LYGO_JOY_PLANT_CONSENT=yes", file=sys.stderr)
        return 2

    doc = ROOT / "docs" / "JOY_LOOP_PROTOCOL.md"
    if not doc.is_file():
        print("missing JOY_LOOP_PROTOCOL.md", file=sys.stderr)
        return 1

    subprocess.check_call(
        [sys.executable, str(ROOT / "tools" / "joy_loop_protocol.py"), "--tick"],
        cwd=ROOT,
    )
    reg = build_manifest()
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "build_kernel_eggs.py")], cwd=ROOT)
    subprocess.check_call(
        [sys.executable, str(ROOT / "tools" / "build_haven_star_chart.py")], cwd=ROOT
    )
    print(f"[joy] planted {EGG_ID} merkle={reg['registry_merkle_root'][:16]}…")
    print(f"[joy] public {REGISTRY_PUBLIC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
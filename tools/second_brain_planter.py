#!/usr/bin/env python3
"""Plant LYGO Second Brain kernel egg + public lattice mirrors (consent-gated)."""

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
REGISTRY_LOCAL = ROOT / "data" / "second_brain" / "second_brain_egg_registry.json"
REGISTRY_PUBLIC = ROOT / "docs" / "SecondBrainRegistry.json"
MANIFEST = ROOT / "data" / "second_brain" / "second_brain_egg_manifest.json"
SNAPSHOT_PUBLIC = ROOT / "docs" / "second_brain" / "second_brain_snapshot.json"
LEDGER = ROOT / "data" / "second_brain" / "manifest.jsonl"
SIGNATURE = "Δ9Φ963-SECOND-BRAIN-EGG-v1"
EGG_ID = "lygo-second-brain-v10"


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


def _merkle(hex_hashes: list[str]) -> str:
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


def append_ledger(event: str, detail: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **detail,
    }
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")


def build_manifest() -> dict:
    core_artifacts = [
        ("second_brain_cli", ROOT / "tools" / "lygo_second_brain.py"),
        ("second_brain_spec", ROOT / "docs" / "BIOPHASE7_LYGO_SECOND_BRAIN.md"),
        ("vault_readme", ROOT / "lygo_second_brain" / "README.md"),
        ("ingest_script", ROOT / "lygo_second_brain" / "scripts" / "ingest.py"),
        ("embed_index", ROOT / "lygo_second_brain" / "scripts" / "embed_index.py"),
    ]
    hashes: list[str] = []
    entries = []
    for label, path in core_artifacts:
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

    merkle_root = _merkle(hashes)
    manifest = {
        "signature": SIGNATURE,
        "type": "lygo_second_brain_kernel_egg",
        "egg_id": EGG_ID,
        "version": "1.0.0",
        "built_utc": time.time(),
        "git_head": _git_head(),
        "merkle_root": merkle_root,
        "artifacts": entries,
        "boot": "python tools/lygo_second_brain.py index",
        "pages_mirror": "https://deepseekoracle.github.io/lygo-protocol-stack/SecondBrainRegistry.json",
        "snapshot_mirror": (
            "https://deepseekoracle.github.io/lygo-protocol-stack/"
            "second_brain/second_brain_snapshot.json"
        ),
        "ethical_gates": ["P0_STRICT", "LOCAL_FIRST", "NO_AUTO_PUSH"],
        "protocol_layers": ["P2", "P6"],
        "clawhub": "https://clawhub.ai/deepseekoracle/lygo-second-brain",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    digest = _sha256_file(MANIFEST)
    manifest["artifacts"].append(
        {
            "label": "second_brain_egg_manifest",
            "path": "data/second_brain/second_brain_egg_manifest.json",
            "sha256": digest,
            "size_bytes": MANIFEST.stat().st_size,
        }
    )
    merkle_root = _merkle([a["sha256"] for a in manifest["artifacts"] if a.get("sha256")])
    manifest["merkle_root"] = merkle_root
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
                "manifest_path": "data/second_brain/second_brain_egg_manifest.json",
                "kernel_egg_registry": "docs/KernelEggRegistry.json",
            }
        ],
        "ledger": "data/second_brain/manifest.jsonl",
    }
    REGISTRY_LOCAL.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    REGISTRY_PUBLIC.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    SNAPSHOT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PUBLIC.write_text(
        json.dumps(
            {
                "signature": SIGNATURE,
                "egg_id": EGG_ID,
                "registry_merkle_root": merkle_root,
                "git_head": manifest["git_head"],
                "vault_default": "lygo_second_brain/vault",
                "updated_utc": registry["updated_utc"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return registry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--skip-kernel-rebuild", action="store_true")
    args = ap.parse_args()
    if not args.i_consent and os.environ.get("LYGO_SECOND_BRAIN_PLANT_CONSENT", "").lower() not in (
        "yes",
        "1",
        "true",
    ):
        print(
            "Consent required: --i-consent or LYGO_SECOND_BRAIN_PLANT_CONSENT=yes",
            file=sys.stderr,
        )
        return 2

    spec = ROOT / "docs" / "BIOPHASE7_LYGO_SECOND_BRAIN.md"
    if not spec.is_file():
        print("missing BIOPHASE7_LYGO_SECOND_BRAIN.md", file=sys.stderr)
        return 1

    self_check = ROOT / "clawhub" / "mirrors" / "lygo-second-brain" / "scripts" / "self_check.py"
    if self_check.is_file():
        subprocess.check_call([sys.executable, str(self_check)], cwd=ROOT)

    reg = build_manifest()
    append_ledger(
        "kernel_egg_plant",
        {"egg_id": EGG_ID, "merkle": reg["registry_merkle_root"][:16]},
    )

    if not args.skip_kernel_rebuild:
        subprocess.check_call([sys.executable, str(ROOT / "tools" / "build_kernel_eggs.py")], cwd=ROOT)
        subprocess.check_call(
            [sys.executable, str(ROOT / "tools" / "verify_kernel_eggs.py")], cwd=ROOT
        )
        subprocess.check_call(
            [sys.executable, str(ROOT / "tools" / "build_haven_star_chart.py")], cwd=ROOT
        )

    print(f"[second-brain] planted {EGG_ID} merkle={reg['registry_merkle_root'][:16]}…")
    print(f"[second-brain] public {REGISTRY_PUBLIC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
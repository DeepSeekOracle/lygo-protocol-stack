#!/usr/bin/env python3
"""Plant lygo-lpis-v10 kernel egg + public registry (consent-gated)."""

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
REGISTRY_PUBLIC = ROOT / "docs" / "PromptImplantRegistry.json"
MANIFEST = ROOT / "data" / "prompt_vault" / "lpis_egg_manifest.json"
SIGNATURE = "Δ9Φ963-LPIS-EGG-v1"
EGG_ID = "lygo-lpis-v10"


def _git_head() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10)
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


def build_manifest() -> dict:
    artifacts = [
        ("lpis_cli", ROOT / "tools" / "lygo_lpis.py"),
        ("lpis_spec", ROOT / "docs" / "BIOPHASE7_LYGO_LPIS.md"),
        ("package_readme", ROOT / "lygo_lpis" / "README.md"),
        ("framework", ROOT / "lygo_lpis" / "framework.py"),
        ("vault", ROOT / "lygo_lpis" / "vault.py"),
        ("analyzer", ROOT / "lygo_lpis" / "analyzer.py"),
    ]
    entries = []
    hashes = []
    for label, path in artifacts:
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
        "type": "lygo_lpis_kernel_egg",
        "egg_id": EGG_ID,
        "version": "1.0.0",
        "built_utc": time.time(),
        "git_head": _git_head(),
        "merkle_root": merkle_root,
        "artifacts": entries,
        "boot": "python tools/lygo_lpis.py list",
        "clawhub": "https://clawhub.ai/deepseekoracle/lygo-lpis",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    digest = _sha256_file(MANIFEST)
    manifest["artifacts"].append(
        {
            "label": "lpis_egg_manifest",
            "path": "data/prompt_vault/lpis_egg_manifest.json",
            "sha256": digest,
            "size_bytes": MANIFEST.stat().st_size,
        }
    )
    merkle_root = _merkle([a["sha256"] for a in manifest["artifacts"]])
    manifest["merkle_root"] = merkle_root
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    registry = {
        "signature": SIGNATURE,
        "updated_utc": time.time(),
        "git_head": manifest["git_head"],
        "egg_count": 1,
        "registry_merkle_root": merkle_root,
        "eggs": [{"egg_id": EGG_ID, "merkle_root": merkle_root, "manifest_path": "data/prompt_vault/lpis_egg_manifest.json"}],
        "ledger": "data/prompt_vault/implant_runs.jsonl",
    }
    REGISTRY_PUBLIC.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()
    if not args.i_consent and os.environ.get("LYGO_LPIS_PLANT_CONSENT", "").lower() not in ("yes", "1", "true"):
        print("Consent required: --i-consent", file=sys.stderr)
        return 2

    sc = ROOT / "clawhub" / "mirrors" / "lygo-lpis" / "scripts" / "self_check.py"
    if sc.is_file():
        subprocess.check_call([sys.executable, str(sc)], cwd=ROOT)

    reg = build_manifest()
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "build_kernel_eggs.py")], cwd=ROOT)
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "verify_kernel_eggs.py")], cwd=ROOT)
    print(f"[lpis] planted {EGG_ID} merkle={reg['registry_merkle_root'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
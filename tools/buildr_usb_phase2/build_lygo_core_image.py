#!/usr/bin/env python3
"""Build signed read-only lygo_core archive (Phase 2 — Windows + Linux portable)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from signing import SIGNATURE, load_or_create_key, sha256_hex, sign_blob

# Paths relative to KEY root included in core
CORE_INCLUDE_PREFIXES = (
    "hermes",
    "phase2",
    "product/champions",
    "product/models/MODEL_MANIFEST.json",
    "verify_bootstrap.py",
    "scripts/bootstrap_env.ps1",
    "scripts/verify_builder_key.ps1",
    "restore/EGG_RECOVERY_MAP.json",
)

CORE_STACK_TOOLS = (
    "tools/verify_kernel_eggs.py",
    "tools/verify_champion_eggs.py",
    "tools/verify_lattice_alignment.py",
    "tools/lygo_hermes_audit.py",

    "protocol0_byte_entropy_filter/src/python/lygo_p0.py",
    "protocol0_byte_entropy_filter/src/python/byte_entropy_filter.py",
    "stack/kernel_bridge.py",
    "stack/lygo_stack.py",
    "docs/KernelEggRegistry.json",
    "docs/ChampionEggRegistry.json",
    "docs/STACK_STATUS.md",
)

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "results",
    "build",
}
EXCLUDE_GLOBS = ("*.bin", "*.pyc", "*.log")


def _skip(path: Path, rel: str) -> bool:
    parts = Path(rel).parts
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    if "clawhub" in parts and "mirrors" in parts:
        return True
    if rel.startswith("stack/data/kernel_eggs"):
        return True
    if rel.startswith("army"):
        return True
    if rel.startswith("_builder_vault"):
        return True
    if rel.startswith("data/") or rel.startswith("images/") or rel.startswith("mnt_core/"):
        return True
    return any(rel.endswith(x.lstrip("*")) for x in ("*.pyc",) if "*" in x)


def collect_files(key_root: Path) -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    seen: set[str] = set()

    def add(physical: Path, arcname: str) -> None:
        if not physical.is_file() or arcname in seen or _skip(physical, arcname):
            return
        seen.add(arcname)
        out.append((physical, arcname))

    for prefix in CORE_INCLUDE_PREFIXES:
        p = key_root / prefix
        if p.is_file():
            add(p, prefix.replace("\\", "/"))
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(key_root).as_posix()
                    add(f, rel)

    stack = key_root / "stack" / "lygo-protocol-stack"
    if stack.is_dir():
        for rel_tool in CORE_STACK_TOOLS:
            add(stack / rel_tool, f"stack/lygo-protocol-stack/{rel_tool}")

    return sorted(out, key=lambda x: x[1])


def build_manifest(files: list[tuple[Path, str]]) -> dict:
    entries = {}
    for physical, arcname in files:
        data = physical.read_bytes()
        entries[arcname] = sha256_hex(data)
    return {
        "signature": SIGNATURE,
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "format": "lygo_core.tar.gz",
        "file_count": len(entries),
        "files": entries,
        "merkle_root": _merkle(list(entries.values())),
    }


def _merkle(hex_hashes: list[str]) -> str:
    layer = list(hex_hashes)
    if not layer:
        return sha256_hex(b"")
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            pair = layer[i] + (layer[i + 1] if i + 1 < len(layer) else layer[i])
            nxt.append(hashlib.sha256(pair.encode()).hexdigest())
        layer = nxt
    return layer[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-root", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", r"E:\LYGO_BUILDER_KEY"))
    args = ap.parse_args()
    key_root = Path(args.key_root)
    images = key_root / "images"
    images.mkdir(parents=True, exist_ok=True)
    archive = images / "lygo_core.tar.gz"

    files = collect_files(key_root)
    if not files:
        print("No files to pack", flush=True)
        return 2

    manifest = build_manifest(files)
    with tarfile.open(archive, "w:gz") as tar:
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        # embed manifest inside tar
        import io

        ti = tarfile.TarInfo(name="LYGO_CORE_MANIFEST.json")
        ti.size = len(manifest_bytes)
        tar.addfile(ti, io.BytesIO(manifest_bytes))
        for physical, arcname in files:
            tar.add(physical, arcname=arcname)

    blob = archive.read_bytes()
    (images / "lygo_core.sha256").write_text(sha256_hex(blob) + "\n", encoding="utf-8")
    key = load_or_create_key(key_root)
    sig = sign_blob(blob, key)
    (images / "lygo_core.sig").write_text(sig + "\n", encoding="utf-8")
    (images / "lygo_core.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "archive": str(archive), "bytes": len(blob), "files": len(files)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Verify and extract lygo_core read-only image to mnt_core/."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tarfile
from pathlib import Path

from signing import load_or_create_key, sha256_hex, verify_blob


def verify_archive(key_root: Path) -> dict:
    images = key_root / "images"
    archive = images / "lygo_core.tar.gz"
    if not archive.is_file():
        return {"ok": False, "error": "missing lygo_core.tar.gz — run build_lygo_core_image.py"}
    blob = archive.read_bytes()
    expect_sha = (images / "lygo_core.sha256").read_text(encoding="utf-8").strip()
    if sha256_hex(blob) != expect_sha:
        return {"ok": False, "error": "lygo_core.sha256 mismatch"}
    sig = (images / "lygo_core.sig").read_text(encoding="utf-8").strip()
    key = load_or_create_key(key_root)
    if not verify_blob(blob, sig, key):
        return {"ok": False, "error": "lygo_core.sig invalid — QUARANTINE"}
    return {"ok": True, "bytes": len(blob)}


def extract_core(key_root: Path, *, force: bool = False) -> dict:
    v = verify_archive(key_root)
    if not v.get("ok"):
        return v
    mnt = key_root / "mnt_core"
    if mnt.exists() and any(mnt.iterdir()) and not force:
        return {"ok": True, "skipped": "mnt_core already populated", "path": str(mnt)}
    if mnt.exists():
        shutil.rmtree(mnt)
    mnt.mkdir(parents=True)
    archive = key_root / "images" / "lygo_core.tar.gz"
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=mnt, filter="data")
    # Windows read-only hint
    for f in mnt.rglob("*"):
        if f.is_file():
            try:
                os.chmod(f, stat.S_IREAD)
            except OSError:
                pass
    return {"ok": True, "path": str(mnt), "files": sum(1 for _ in mnt.rglob("*") if _.is_file())}


def validate_extracted_manifest(key_root: Path) -> dict:
    mnt = key_root / "mnt_core"
    man_path = mnt / "LYGO_CORE_MANIFEST.json"
    side = key_root / "images" / "lygo_core.manifest.json"
    manifest = json.loads((man_path if man_path.is_file() else side).read_text(encoding="utf-8"))
    bad = []
    for arcname, expect in manifest.get("files", {}).items():
        p = mnt / arcname
        if not p.is_file():
            bad.append(f"missing:{arcname}")
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != expect:
            bad.append(f"tamper:{arcname}")
    return {"ok": not bad, "bad": bad[:20], "count": manifest.get("file_count")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-root", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", r"E:\LYGO_BUILDER_KEY"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    key_root = Path(args.key_root)
    steps = {
        "verify_archive": verify_archive(key_root),
        "extract": extract_core(key_root, force=args.force),
        "manifest": validate_extracted_manifest(key_root),
    }
    ok = all(s.get("ok") for s in steps.values())
    print(json.dumps({"ok": ok, "steps": steps}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
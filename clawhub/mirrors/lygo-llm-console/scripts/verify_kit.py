#!/usr/bin/env python3
"""Verify the shipped kit, file by file, against kit/KIT_SHA256SUMS.txt.

No network. No subprocess. Reads the skill's own files only.

    python scripts/verify_kit.py           # verify + report JSON (exit 0 ok, 1 mismatch)
    python scripts/verify_kit.py --list    # list the shipped files

Why file-by-file: the 1.2.0 package shipped one zip and one digest, which says "the archive is the
archive" and nothing about what is inside it. This kit ships as a tree, so every file is checked and
extra/missing files are reported rather than tolerated.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KIT = ROOT / "kit"
SUMS = KIT / "KIT_SHA256SUMS.txt"
MANIFEST = KIT / "PUBLIC_KIT.json"


def read_sums() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, rel = line.partition("  ")
        if digest and rel:
            out[rel.strip()] = digest.strip().lower()
    return out


def main(argv: list[str]) -> int:
    if not KIT.is_dir():
        print(json.dumps({"ok": False, "error": "kit_missing", "path": str(KIT)}))
        return 1
    if not SUMS.is_file():
        print(json.dumps({"ok": False, "error": "checksum_list_missing", "path": str(SUMS)}))
        return 1

    sums = read_sums()
    on_disk = {p.relative_to(KIT).as_posix(): p for p in KIT.rglob("*") if p.is_file()}
    on_disk.pop("KIT_SHA256SUMS.txt", None)

    if "--list" in argv:
        for rel in sorted(on_disk):
            print(f"{sums.get(rel, 'UNLISTED ')}  {rel}")
        return 0

    mismatched: list[dict[str, str]] = []
    for rel, want in sorted(sums.items()):
        p = KIT / rel
        if not p.is_file():
            mismatched.append({"file": rel, "problem": "missing"})
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            mismatched.append({"file": rel, "problem": "sha256_mismatch", "expected": want, "got": got})

    extra = sorted(set(on_disk) - set(sums) - {"PUBLIC_KIT.json"})
    for rel in extra:
        mismatched.append({"file": rel, "problem": "not_in_checksum_list"})

    manifest: dict = {}
    if MANIFEST.is_file():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except ValueError as exc:  # noqa: BLE001
            mismatched.append({"file": "PUBLIC_KIT.json", "problem": f"unreadable: {exc}"})

    declared = manifest.get("file_count")
    if isinstance(declared, int) and declared != len(sums):
        mismatched.append({
            "file": "PUBLIC_KIT.json",
            "problem": "manifest_count_mismatch",
            "declared": declared,
            "checksum_lines": len(sums),
        })

    result = {
        "ok": not mismatched,
        "kit_release": (KIT / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()
        if (KIT / "VERSION").is_file()
        else "unknown",
        "files_verified": len(sums),
        "files_on_disk": len(on_disk),
        "bytes": sum(p.stat().st_size for p in on_disk.values()),
        "mismatched": mismatched,
        "note": "Unlisted files are reported, never silently accepted.",
    }
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""refresh_manifests.py - recompute the file-hash entries in a kit's *_MANIFEST.json.

The manifests are the published integrity record of a certified build, so they must never drift
silently: this tool recomputes every entry, prints exactly what moved, and stamps the manifest
with when and why. Run it after any intentional edit to a hashed file, then re-run
scripts/certify_build.py (tests/test_branding.py fails on unrefreshed drift).

Identity: sha256 over the file's bytes with line endings normalised to LF, plus that length -
the same identity scripts/certify_build.py checks. Line endings are a checkout detail, not a
build change: core.autocrlf rewrites text files to CRLF on Windows checkouts, so a raw-byte hash
would read a pristine copy as MODIFIED.

Usage:
    python scripts/refresh_manifests.py                    # refresh, stamped with now
    python scripts/refresh_manifests.py --note "why"       # stamp a reason
    python scripts/refresh_manifests.py --check            # report drift only (exit 1 if any)
    python scripts/refresh_manifests.py --root <other kit> # refresh the public copy or the USB kit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Line-ending bytes, written via codes so no escaping layer can mangle them:
CRLF = bytes((13, 10))
LF = bytes((10,))  # note the comma: bytes((10)) would be ten NUL bytes, not a newline


def identity(path: Path) -> tuple[str, int]:
    """(sha256 over LF-normalised bytes, that length) - the certified identity of a file."""
    data = path.read_bytes()
    if CRLF in data:
        data = data.replace(CRLF, LF)
    return hashlib.sha256(data).hexdigest(), len(data)


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh *_MANIFEST.json file hashes.")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="kit root to refresh (default: the kit this script lives in)")
    ap.add_argument("--note", default="", help="why the hashes moved (stamped in the manifest)")
    ap.add_argument("--check", action="store_true", help="report drift without writing")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    print(f"root: {root}")
    total = 0
    for m in sorted(root.glob("*_MANIFEST.json")):
        raw = m.read_bytes()
        trailing_nl = raw.endswith(b"\n")
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - report, never crash
            print(f"  {m.name}: unreadable ({exc})")
            continue
        files = data.get("files") if isinstance(data, dict) else None
        if not isinstance(files, list):
            print(f"  {m.name}: no files list - skipped")
            continue
        changed = []
        for row in files:
            if not isinstance(row, dict) or "path" not in row:
                continue
            target = root / str(row["path"])
            if not target.is_file():
                print(f"  MISSING {row['path']}")
                continue
            digest, size = identity(target)
            if row.get("sha256_16") != digest[:16] or row.get("bytes") != size:
                changed.append((str(row["path"]), row.get("sha256_16"), digest[:16],
                                row.get("bytes"), size))
                row["sha256_16"] = digest[:16]
                row["bytes"] = size
        if not changed:
            print(f"  {m.name}: all {len(files)} entries already correct")
            continue
        total += len(changed)
        for path, old, new, ob, nb in changed:
            print(f"    {path}: {old} -> {new}  ({ob} -> {nb} bytes)")
        if args.check:
            print(f"  {m.name}: {len(changed)} entries DRIFTED (not written, --check)")
            continue
        data["rebrand_refresh_iso"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        if args.note:
            data["rebrand_refresh_note"] = args.note
        data["rebrand_refresh_files"] = [c[0] for c in changed]
        m.write_text(json.dumps(data, indent=2) + ("\n" if trailing_nl else ""), encoding="utf-8")
        print(f"  {m.name}: {len(changed)} of {len(files)} entries refreshed")

    if args.check and total:
        print(f"total drift: {total} entries - run without --check to refresh")
        return 1
    print("total entries refreshed:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())

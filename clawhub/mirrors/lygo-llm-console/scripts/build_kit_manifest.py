#!/usr/bin/env python3
"""Regenerate kit/KIT_SHA256SUMS.txt and kit/PUBLIC_KIT.json from the kit as it is on disk.

No network. No subprocess. Reads and writes only this skill's own files.

    python scripts/build_kit_manifest.py           # rewrite both artifacts
    python scripts/build_kit_manifest.py --check   # exit 1 if they are stale, write nothing

Why this exists: 1.6.1 edited a dozen kit files and left the checksum list behind, so
`verify_kit.py` reported every one of them as a mismatch and the published digests described a
release that no longer existed. Regenerating by hand is how that happens; a script that can also
answer "are these stale?" is how it stops happening. `--check` is what self_check calls.

The two generated artifacts are deliberately outside their own manifest: a list of hashes cannot
contain its own hash, and PUBLIC_KIT.json records the payload it describes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KIT = ROOT / "kit"
SUMS = KIT / "KIT_SHA256SUMS.txt"
MANIFEST = KIT / "PUBLIC_KIT.json"

# generated, so a manifest cannot describe them without changing itself
GENERATED = {"KIT_SHA256SUMS.txt", "PUBLIC_KIT.json"}


def payload() -> dict[str, str]:
    """Kit-relative posix path -> sha256, for every shipped file, sorted."""
    out: dict[str, str] = {}
    for path in sorted(KIT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(KIT).as_posix()
        if rel in GENERATED:
            continue
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def sums_text(files: dict[str, str]) -> str:
    return "".join(f"{digest}  {rel}\n" for rel, digest in sorted(files.items()))


def manifest_text(files: dict[str, str], built_at: str) -> str:
    previous: dict = {}
    if MANIFEST.is_file():
        try:
            previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except ValueError:
            previous = {}

    total = sum((KIT / rel).stat().st_size for rel in files)
    manifest = {
        "kit": previous.get("kit", "lygo-llm-console public kit (ClawHub package, unpacked)"),
        "console_release": previous.get("console_release", ""),
        "source_tree": previous.get("source_tree", ""),
        "built_at": built_at,
        "packed_as_archive": False,
        "reason_unpacked": previous.get(
            "reason_unpacked",
            "a registry reviewer can read every file that runs; the 1.2.0 zip drew four HIGH "
            "analysis-evasion findings for being uninspectable",
        ),
        "patched_in_the_copy_only": previous.get("patched_in_the_copy_only", []),
        "not_shipped": previous.get("not_shipped", {}),
        "file_count": len(files),
        "total_bytes": total,
        "files": dict(sorted(files.items())),
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def stale(files: dict[str, str]) -> list[str]:
    problems: list[str] = []
    if not SUMS.is_file():
        problems.append("kit/KIT_SHA256SUMS.txt missing")
    elif SUMS.read_text(encoding="utf-8") != sums_text(files):
        problems.append("kit/KIT_SHA256SUMS.txt does not match the kit")
    if not MANIFEST.is_file():
        problems.append("kit/PUBLIC_KIT.json missing")
    else:
        try:
            man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"kit/PUBLIC_KIT.json unreadable: {exc}")
        else:
            if man.get("files") != dict(sorted(files.items())):
                problems.append("kit/PUBLIC_KIT.json hashes do not match the kit")
            if man.get("file_count") != len(files):
                problems.append(
                    f"kit/PUBLIC_KIT.json says {man.get('file_count')} files, kit has {len(files)}"
                )
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                       help="report whether the artifacts are stale; write nothing")
    args = parser.parse_args(argv)

    if not KIT.is_dir():
        print(json.dumps({"ok": False, "error": "kit_missing", "path": str(KIT)}))
        return 1

    files = payload()
    if not files:
        print(json.dumps({"ok": False, "error": "kit_empty"}))
        return 1

    if args.check:
        problems = stale(files)
        print(json.dumps({"ok": not problems, "files": len(files), "problems": problems}, indent=2))
        return 0 if not problems else 1

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    SUMS.write_text(sums_text(files), encoding="utf-8", newline="\n")
    MANIFEST.write_text(manifest_text(files, built_at), encoding="utf-8", newline="\n")

    problems = stale(files)
    print(json.dumps({
        "ok": not problems,
        "files": len(files),
        "bytes": sum((KIT / rel).stat().st_size for rel in files),
        "built_at": built_at,
        "sums_sha256": hashlib.sha256(SUMS.read_bytes()).hexdigest(),
        "problems": problems,
    }, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

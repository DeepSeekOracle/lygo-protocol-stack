#!/usr/bin/env python3
"""scan_for_secrets.py — run before every commit/push in lyra-crypto-operator.

Blocks the commit if staged files contain anything that LOOKS like key
material. Heuristic safety net for agent-written wallet files in wrong folder.

Usage:
    python scripts/scan_for_secrets.py            # scan staged files
    python scripts/scan_for_secrets.py --all       # scan whole working tree
    python scripts/scan_for_secrets.py --install-hook   # wire into git pre-commit
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("hex_private_key_64", re.compile(r"\b(0x)?[0-9a-fA-F]{64}\b")),
    ("wif_private_key", re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")),
    (
        "bip39_mnemonic_12plus",
        re.compile(r"(?:\b\w+\b[ \t]+){11,23}\b\w+\b"),
    ),
    ("xai_key", re.compile(r"\bxai-[A-Za-z0-9_-]{10,}\b")),
    ("nvidia_key", re.compile(r"\bnvapi-[A-Za-z0-9_-]{10,}\b")),
    (
        "generic_api_key_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|private[_-]?key|mnemonic|seed[_-]?phrase)\b\s*[:=]\s*['\"][^'\"]{16,}['\"]"
        ),
    ),
]

SKIP_NAMES = {"scan_for_secrets.py"}


def staged_files() -> list[Path]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [Path(p) for p in out.splitlines() if p]


def all_tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [Path(p) for p in out.splitlines() if p]


def scan_file(path: Path) -> list[str]:
    if path.name in SKIP_NAMES:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []

    hits = []
    for name, pattern in PATTERNS:
        if name == "bip39_mnemonic_12plus" and path.suffix in (".md", ".rst"):
            continue
        if pattern.search(text):
            hits.append(name)
    return hits


def main() -> int:
    args = sys.argv[1:]

    if "--install-hook" in args:
        hook_path = Path(".git/hooks/pre-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(
            "#!/bin/sh\npython scripts/scan_for_secrets.py || exit 1\n",
            encoding="utf-8",
        )
        hook_path.chmod(0o755)
        print(f"Installed pre-commit hook at {hook_path}")
        return 0

    files = all_tracked_files() if "--all" in args else staged_files()
    problems: dict[str, list[str]] = {}

    for f in files:
        if not f.exists():
            continue
        hits = scan_file(f)
        if hits:
            problems[str(f)] = hits

    if problems:
        print("BLOCKED: possible key/secret material detected:\n")
        for f, hits in problems.items():
            print(f"  {f}: {', '.join(hits)}")
        print(
            "\nReview by hand if false positives. Do not commit real keys — see README."
        )
        return 1

    print(f"OK: scanned {len(files)} file(s), no key-shaped material found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Detect common workspace path drift mistakes.

Purpose:
- Flag code that writes to `skills/state` instead of workspace `state/`.
- Flag hardcoded workspace paths that won't port.

Usage:
  python scripts/path_drift_lint.py --root .

Exit codes:
  0 = no findings
  3 = findings present
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "dist", "build"}
TEXT_EXTS = {".py", ".js", ".ts", ".md", ".ps1", ".json", ".yml", ".yaml"}

PATTERNS = [
    # writing to skills/state (common bug)
    ("skills_state_path", re.compile(r"skills[\\/]+state")),
    # absolute workspace hardcode
    ("hardcoded_workspace", re.compile(r"\\\\?C:[\\/].*?\\\\\.openclaw\\\\workspace|C:[\\/].*?\\.openclaw[\\/]+workspace", re.I)),
]

# Don't flag docs/self that mention the pattern.
DEFAULT_EXCLUDE_FILES = {"SKILL.md", "path_drift_lint.py", "ws_paths.py"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if p.name in DEFAULT_EXCLUDE_FILES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--max-bytes", type=int, default=500_000)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    findings = []

    for fp in iter_files(root):
        try:
            data = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if fp.stat().st_size > args.max_bytes:
            continue

        for name, rx in PATTERNS:
            for m in rx.finditer(data):
                # small context window
                start = max(0, m.start() - 40)
                end = min(len(data), m.end() + 40)
                findings.append(
                    {
                        "file": str(fp),
                        "rule": name,
                        "match": m.group(0),
                        "context": data[start:end].replace("\n", "\\n"),
                    }
                )
                break

    out = {"ok": len(findings) == 0, "findingCount": len(findings), "findings": findings}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

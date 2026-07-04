#!/usr/bin/env python3
"""Report Excavationpro HTML pages missing google-adsense-account meta in <head>."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB = "ca-pub-0646320966060599"
META = re.compile(r'<meta\s+name=["\']google-adsense-account["\']', re.I)
ROOT = Path(__file__).resolve().parents[2] / "Excavationpro"
SKIP_DIRS = {"aichat", "haven_star_chart", "Hytale", "LYRA"}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    missing_meta: list[str] = []
    meta_outside_head: list[str] = []
    no_head: list[str] = []
    ok = 0
    for html in sorted(root.rglob("*.html")):
        if any(p in SKIP_DIRS for p in html.relative_to(root).parts):
            continue
        t = html.read_text(encoding="utf-8", errors="replace")
        rel = str(html.relative_to(root)).replace("\\", "/")
        he = t.lower().find("</head>")
        if he <= 0:
            no_head.append(rel)
            continue
        head = t[:he]
        if META.search(head) and PUB in head:
            ok += 1
            continue
        if META.search(t) and not META.search(head):
            meta_outside_head.append(rel)
        else:
            missing_meta.append(rel)
    print(f"ok_in_head: {ok}")
    print(f"missing_meta: {len(missing_meta)}")
    for m in missing_meta:
        print(f"  MISSING {m}")
    print(f"meta_outside_head: {len(meta_outside_head)}")
    for m in meta_outside_head:
        print(f"  OUTSIDE_HEAD {m}")
    print(f"no_head: {len(no_head)}")
    for m in no_head:
        print(f"  NO_HEAD {m}")
    return 1 if missing_meta or meta_outside_head or no_head else 0


if __name__ == "__main__":
    raise SystemExit(main())
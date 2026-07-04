#!/usr/bin/env python3
"""Propagate unified champion-pack scripts to all lygo-champion-* ClawHub mirrors."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "clawhub" / "templates" / "champion-pack" / "scripts"
MIRRORS = ROOT / "clawhub" / "mirrors"


def main() -> int:
    if not TEMPLATE.is_dir():
        print("MISSING template", file=sys.stderr)
        return 2
    updated = []
    skipped = []
    for mirror in sorted(MIRRORS.glob("lygo-champion-*")):
        canon = mirror / "references" / "canon.json"
        if not canon.is_file():
            skipped.append(mirror.name)
            continue
        scripts = mirror / "scripts"
        scripts.mkdir(exist_ok=True)
        for name in ("self_check.py", "show_hash.py"):
            shutil.copy2(TEMPLATE / name, scripts / name)
        updated.append(mirror.name)
    print(json.dumps({"updated": len(updated), "mirrors": updated, "skipped": skipped}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
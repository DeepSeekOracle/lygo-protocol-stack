#!/usr/bin/env python3
"""Add staged BLACK OUT albums via the safe listen-portal tool."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
STAGE = Path(r"I:\E Drive\MUSIC_VAULT\_staging_black_out")
TOOL = STACK / "tools" / "safe_add_music_to_listen_portal.py"


def main() -> int:
    albums = sorted(p for p in STAGE.iterdir() if p.is_dir())
    if not albums:
        print("no staged albums")
        return 2
    for alb in albums:
        print("=== ADD", alb.name, "===")
        r = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--folder",
                str(alb),
                "--album",
                alb.name,
                "--artist",
                "Excavationpro",
                "--publish-hf",
            ],
            cwd=str(STACK),
        )
        if r.returncode != 0:
            print("FAIL album", alb.name, r.returncode)
            return r.returncode
    print("=== DEPLOY ASIAN ===")
    r = subprocess.run(
        [sys.executable, str(TOOL), "--inject-playlist-only", "--deploy-asian"],
        cwd=str(STACK),
    )
    if r.returncode != 0:
        return r.returncode
    print("=== PROMOTE EXCAV BACKUP ===")
    r = subprocess.run(
        [sys.executable, str(TOOL), "--promote-backup-excav"],
        cwd=str(STACK),
    )
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify immutable feed chain and print latest entries."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _stack_paths import resolve_stack_root


def main() -> int:
    root = resolve_stack_root()
    script = root / "tools" / "haven_star_chart_feed.py"
    cp = subprocess.run(
        [sys.executable, str(script), "--verify"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    print(cp.stdout or cp.stderr)
    if cp.returncode != 0:
        return cp.returncode
    feed_path = root / "docs" / "haven_star_chart" / "haven_star_chart_feed.json"
    if feed_path.is_file():
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
        for row in (feed.get("entries") or [])[:5]:
            print(
                json.dumps(
                    {
                        "seq": row.get("seq"),
                        "status": row.get("status"),
                        "agent_id": row.get("agent_id"),
                        "node_id": row.get("node_id"),
                        "entry_hash": (row.get("entry_hash") or "")[:16],
                    }
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
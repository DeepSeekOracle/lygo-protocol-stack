#!/usr/bin/env python3
"""Repo entrypoint — delegates to Ollama Army Command Center sentinel."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ARMY_SENTINEL = (
    Path(__file__).resolve().parents[1].parent
    / ".grok"
    / "skills"
    / "lygo-ollama-army"
    / "ollama_command_center"
    / "scripts"
    / "sentinel_heartbeat.py"
)


def main() -> int:
    if not ARMY_SENTINEL.is_file():
        print("Army sentinel not found:", ARMY_SENTINEL, file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(ARMY_SENTINEL), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
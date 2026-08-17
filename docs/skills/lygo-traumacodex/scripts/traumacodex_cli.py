#!/usr/bin/env python3
"""TraumaCodex CLI — prefer stack tool when LYGO_STACK_ROOT is set."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if stack:
        tool = Path(stack) / "tools" / "traumacodex_waveform.py"
        if tool.is_file():
            return subprocess.call([sys.executable, str(tool), *sys.argv[1:]])
    # Bundled fallback: try sibling stack layout
    for candidate in (
        SCRIPT_DIR.parents[3] / "tools" / "traumacodex_waveform.py",
        SCRIPT_DIR.parents[2] / "tools" / "traumacodex_waveform.py",
    ):
        if candidate.is_file():
            return subprocess.call([sys.executable, str(candidate), *sys.argv[1:]])
    print(
        "TraumaCodex needs LYGO_STACK_ROOT pointing at lygo-protocol-stack "
        "(tools/traumacodex_waveform.py). FULL package: "
        "https://chatagent.ca/lygoskillhub.html#full-lygo",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

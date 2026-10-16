#!/usr/bin/env python3
"""FULL LYGO Pure-Data Witness — unlocked register + map (engineer channel)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def main() -> int:
    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if stack:
        tools = Path(stack) / "tools"
        if (tools / "pure_data_register.py").is_file():
            sys.path.insert(0, str(tools))
            # Delegate to stack register when available
            import runpy
            sys.argv[0] = str(tools / "pure_data_register.py")
            # If user called pdw_full_cli with no subcommand hint, keep argv
            runpy.run_path(str(tools / "pure_data_register.py"), run_name="__main__")
            return 0
    # In-package ClawHub-safe CLI
    import pdw_cli
    return pdw_cli.main()

if __name__ == "__main__":
    raise SystemExit(main())

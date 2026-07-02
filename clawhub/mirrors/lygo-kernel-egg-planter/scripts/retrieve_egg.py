#!/usr/bin/env python3
"""Thin wrapper to stack retrieve_kernel_egg.py."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def stack_root() -> Path:
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        return Path(env)
    for anc in SKILL_ROOT.parents:
        if (anc / "tools" / "retrieve_kernel_egg.py").is_file():
            return anc
    return SKILL_ROOT.parents[4]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--egg", default=None)
    args = ap.parse_args()
    tool = stack_root() / "tools" / "retrieve_kernel_egg.py"
    if not tool.is_file():
        print("Set LYGO_STACK_ROOT", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(tool)]
    if args.list:
        cmd.append("--list")
    elif args.egg:
        cmd.extend(["--egg", args.egg])
    else:
        cmd.append("--list")
    return subprocess.call(cmd, cwd=stack_root())


if __name__ == "__main__":
    raise SystemExit(main())
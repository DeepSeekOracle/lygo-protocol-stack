#!/usr/bin/env python3
"""Compat wrapper → mint_cli.py backfill (no subprocess)."""
from __future__ import annotations

import sys

from mint_cli import main as mint_main


def main() -> None:
    # Ensure consent flag present for writes; pass through args
    argv = list(sys.argv[1:])
    if "--i-consent" not in argv:
        argv.append("--i-consent")
    sys.argv = [sys.argv[0], "backfill", *argv]
    raise SystemExit(mint_main())


if __name__ == "__main__":
    main()

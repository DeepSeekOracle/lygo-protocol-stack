#!/usr/bin/env python3
"""Alias entrypoint — Biophase7 blueprint name → lygo_lpis CLI."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "lygo_lpis.py"), run_name="__main__")
#!/usr/bin/env python3
"""Delegate to LYRA_CORE Discord system map post (requires local bot token)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LYRA = Path(r"I:\E Drive\LYRA_CORE\tools\post_lygo_system_links.py")
if not LYRA.is_file():
    print("Missing LYRA_CORE post script", file=sys.stderr)
    raise SystemExit(1)
raise SystemExit(subprocess.call([sys.executable, "-B", str(LYRA)], cwd=str(LYRA.parent.parent)))
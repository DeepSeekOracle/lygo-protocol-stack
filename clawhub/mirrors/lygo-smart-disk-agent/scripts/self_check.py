#!/usr/bin/env python3
"""ClawHub skill wrapper — runs public/verify/self_check.py."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
CHECK = PUBLIC / "verify" / "self_check.py"

if not CHECK.is_file():
    print(json.dumps({"ok": False, "fails": ["missing public/verify/self_check.py"]}))
    raise SystemExit(1)

sys.path.insert(0, str(PUBLIC))
spec = importlib.util.spec_from_file_location("sda_self_check", CHECK)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
raise SystemExit(mod.main())

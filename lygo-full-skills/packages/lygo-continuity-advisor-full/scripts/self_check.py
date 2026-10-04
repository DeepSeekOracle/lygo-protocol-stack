#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
need = ["SKILL.md", "claw.json", "references/SECURITY.md", "references/SUCCESSION.md"]
missing = [p for p in need if not (ROOT / p).is_file()]
print("ok" if not missing else f"missing:{missing}")
raise SystemExit(0 if not missing else 1)

#!/usr/bin/env python3
"""Extract Δ9 Council CHAMPIONS array from champions.html → champions_council.json."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = ROOT.parent / "Excavationpro" / "LYGO-Network" / "champions.html"
OUT = ROOT / "data" / "champion_eggs" / "champions_council.json"
RAW_JS = ROOT / "data" / "champion_eggs" / "_champions_raw.js"
SIGNATURE = "Δ9Φ963-CHAMPION-COUNCIL-v1"


def extract(html_path: Path) -> list[dict]:
    text = html_path.read_text(encoding="utf-8")
    m = re.search(r"let CHAMPIONS = (\[[\s\S]*?\n    \]);", text)
    if not m:
        raise ValueError(f"CHAMPIONS array not found in {html_path}")
    RAW_JS.parent.mkdir(parents=True, exist_ok=True)
    RAW_JS.write_text("module.exports = " + m.group(1), encoding="utf-8")
    out = subprocess.check_output(
        [
            "node",
            "-e",
            "const c=require(process.argv[1]); process.stdout.write(JSON.stringify(c));",
            str(RAW_JS),
        ],
        text=True,
    )
    return json.loads(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", type=Path, default=DEFAULT_HTML)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if not args.html.is_file():
        print(f"Missing hub: {args.html}", file=sys.stderr)
        return 2
    champs = extract(args.html)
    payload = {
        "signature": SIGNATURE,
        "source_html": str(args.html),
        "count": len(champs),
        "champions": champs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"extracted {len(champs)} champions → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
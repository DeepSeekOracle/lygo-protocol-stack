#!/usr/bin/env python3
"""Compare local joy snapshot to GitHub Pages URL (maintenance)."""

from __future__ import annotations

import json
import sys
import urllib.request

LOCAL = __file__
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_PATH = ROOT / "docs" / "joy_loop" / "joy_loop_snapshot.json"
PAGES_URL = "https://deepseekoracle.github.io/lygo-protocol-stack/joy_loop/joy_loop_snapshot.json"
RAW_URL = "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/joy_loop/joy_loop_snapshot.json"


def fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    local = json.loads(LOCAL_PATH.read_text(encoding="utf-8"))
    out = {"local_signature": local.get("signature"), "local_beat": local.get("beat_count")}
    try:
        pages = fetch(PAGES_URL)
        out["pages_signature"] = pages.get("signature")
        out["pages_beat"] = pages.get("beat_count")
        out["pages_ok"] = pages.get("signature") == local.get("signature")
    except Exception as e:
        out["pages_error"] = str(e)
        out["pages_ok"] = False
    try:
        raw = fetch(RAW_URL)
        out["github_main_signature"] = raw.get("signature")
        out["github_main_beat"] = raw.get("beat_count")
        out["main_ok"] = raw.get("signature") == local.get("signature")
    except Exception as e:
        out["main_error"] = str(e)
        out["main_ok"] = False
    print(json.dumps(out, indent=2))
    if not out.get("pages_ok"):
        print("NEEDS_FIX: Pages CDN behind main — wait for Deploy GitHub Pages workflow or workflow_dispatch", file=sys.stderr)
        return 1 if not out.get("main_ok") else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Ingest LYGO-EGG / LYGO-STAR / LYGO-ANNOUNCE from a GitHub issue body. Gate is P0+star gate."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lygo_network_core import announce, ingest_pending, plant_egg, submit_star  # noqa: E402

FENCE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.I)


def first_json(text: str) -> dict | None:
    m = FENCE.search(text or "")
    blob = m.group(1) if m else (text or "").strip()
    if not blob.startswith("{"):
        i = (text or "").find("{")
        if i < 0:
            return None
        blob = text[i:]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="")
    ap.add_argument("--body", default="")
    ap.add_argument("--body-file")
    ap.add_argument("--user", default="issue-agent")
    args = ap.parse_args()
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else args.body
    title = (args.title or "").upper()
    data = first_json(body)
    if not data:
        print(json.dumps({"ok": False, "error": "no_json"}))
        return 1
    if title.startswith("LYGO-EGG") or data.get("kind") == "egg" or "payload" in data:
        r = plant_egg(str(data.get("agent_id") or args.user), data.get("payload") if "payload" in data else data, source="github_issue")
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 2
    if title.startswith("LYGO-STAR") or data.get("node"):
        r = submit_star(data.get("submission") or data, source="github_issue")
        if r.get("queued"):
            r["ingest"] = ingest_pending()
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 2
    if title.startswith("LYGO-ANNOUNCE") or data.get("agent_id"):
        r = announce(data.get("card") or data)
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 2
    print(json.dumps({"ok": False, "error": "unknown_kind", "hint": "Title LYGO-EGG | LYGO-STAR | LYGO-ANNOUNCE"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

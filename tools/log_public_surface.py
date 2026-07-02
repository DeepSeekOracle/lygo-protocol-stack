#!/usr/bin/env python3
"""Append to docs/LYGO_PUBLIC_LINK_ARCHIVE.json — growing public link memory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs" / "LYGO_PUBLIC_LINK_ARCHIVE.json"
MEMORY = ROOT / "docs" / "AGENT_MEMORY_SNAPSHOT.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Register a public URL in the LYGO link archive")
    ap.add_argument("--id", required=True, help="Stable entry id (e.g. my-new-page)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--url", required=True, help="Primary live URL")
    ap.add_argument("--role", default="misc")
    ap.add_argument("--repo-path", default="", help="Optional path inside lygo-protocol-stack")
    ap.add_argument("--note", default="", help="Log line for growth_log")
    args = ap.parse_args()

    data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    entries = data.setdefault("entries", [])
    existing = next((e for e in entries if e.get("id") == args.id), None)
    if existing:
        existing.setdefault("urls", {})["live"] = args.url
        if args.repo_path:
            existing["urls"]["repo_canonical"] = args.repo_path
        existing["title"] = args.title
        existing["role"] = args.role
    else:
        entry = {
            "id": args.id,
            "title": args.title,
            "role": args.role,
            "urls": {"live": args.url},
            "since": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        if args.repo_path:
            entry["urls"]["repo_canonical"] = args.repo_path
        entries.append(entry)

    log_line = args.note or f"registered {args.id} → {args.url}"
    data.setdefault("growth_log", []).append(
        {
            "utc": datetime.now(timezone.utc).isoformat(),
            "event": log_line,
            "refs": [args.id],
        }
    )
    data["updated_utc"] = datetime.now(timezone.utc).isoformat()
    ARCHIVE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if MEMORY.is_file():
        mem = json.loads(MEMORY.read_text(encoding="utf-8"))
        mem.setdefault("session_log", []).append(
            f"{data['updated_utc'][:10]}: link archive — {log_line}"
        )
        mem.setdefault("public_link_archive", str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"))
        MEMORY.write_text(json.dumps(mem, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "archive": str(ARCHIVE), "id": args.id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
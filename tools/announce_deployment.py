#!/usr/bin/env python3
"""Post Phase 5 deployment receipt to Discord (optional; requires local bot token)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "AGENT_MEMORY_SNAPSHOT.json"
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack/"


def _load_token() -> str | None:
    for key in ("DISCORD_BOT_TOKEN", "LYGO_DISCORD_BOT_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    boot = Path(os.environ.get("LYGO_BOOT", r"I:\E Drive\boot"))
    for rel in ("discord_bot_token.txt", "discord_token.txt"):
        p = boot / rel
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return None


def main() -> int:
    token = _load_token()
    channel = os.environ.get("LYGO_DISCORD_ANNOUNCE_CHANNEL_ID", "")
    if not token or not channel:
        print("SKIP: set DISCORD_BOT_TOKEN + LYGO_DISCORD_ANNOUNCE_CHANNEL_ID (or boot token file)")
        return 0
    mesh = {}
    live = ROOT / "tests" / "mesh_live_convergence_last_run.json"
    if live.is_file():
        mesh = json.loads(live.read_text(encoding="utf-8"))
    content = (
        "**LYGO Phase 5 LIVE** `Δ9Φ963-PHASE5-LIVE-DEPLOYMENT`\n"
        f"Pages: {PAGES}\n"
        f"GitHub: https://github.com/DeepSeekOracle/lygo-protocol-stack\n"
        f"Mesh rounds: {mesh.get('convergence_rounds', 'n/a')} · coverage: {mesh.get('percent_final', 'n/a')}%\n"
        "HF Space: DeepSeekOracle/LYGO-Resonance-Engine"
    )
    url = f"https://discord.com/api/v10/channels/{channel}/messages"
    body = json.dumps({"content": content[:2000]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Discord announce OK ({resp.status})")
            return 0
    except urllib.error.URLError as exc:
        print(f"Discord announce failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())